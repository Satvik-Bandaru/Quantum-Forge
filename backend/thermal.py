"""Bounded lumped thermal circuit, not a calibrated dilution refrigerator.

Three finite-heat-capacity stages exchange heat by linear conductances. Each
idealized active cooler removes a capped amount of heat above its bath setting.
The room boundary is fixed. The ODE integrates external heat/cooling ledgers so
the first law is checked independently of the temperature display.
"""
from __future__ import annotations

import math

import numpy as np
from pydantic import Field
from scipy.integrate import solve_ivp

from .models import StrictModel


class ThermalStage(StrictModel):
    initial_temperature_k: float = Field(ge=.005, le=350)
    bath_temperature_k: float = Field(ge=.005, le=350)
    heat_capacity_j_per_k: float = Field(ge=.001, le=100000)
    heat_load_w: float = Field(ge=0, le=100)
    cooling_conductance_w_per_k: float = Field(ge=0, le=10)
    cooling_capacity_w: float = Field(ge=0, le=100)


class ThermalNetwork(StrictModel):
    room_temperature_k: float = Field(default=300, ge=200, le=350)
    room_to_shield_w_per_k: float = Field(default=.002, ge=0, le=1)
    shield_to_cold_plate_w_per_k: float = Field(default=.00002, ge=0, le=1)
    cold_plate_to_mixing_w_per_k: float = Field(default=.0000002, ge=0, le=1)
    shield: ThermalStage = Field(default_factory=lambda: ThermalStage(
        initial_temperature_k=60, bath_temperature_k=50, heat_capacity_j_per_k=500,
        heat_load_w=.2, cooling_conductance_w_per_k=.5, cooling_capacity_w=50))
    cold_plate: ThermalStage = Field(default_factory=lambda: ThermalStage(
        initial_temperature_k=5, bath_temperature_k=4, heat_capacity_j_per_k=5,
        heat_load_w=.001, cooling_conductance_w_per_k=.1, cooling_capacity_w=1))
    mixing_chamber: ThermalStage = Field(default_factory=lambda: ThermalStage(
        initial_temperature_k=.1, bath_temperature_k=.02, heat_capacity_j_per_k=.002,
        heat_load_w=.000001, cooling_conductance_w_per_k=.002, cooling_capacity_w=.0002))


STAGES = (('shield', 'Intermediate shield'), ('cold_plate', 'Cold plate'), ('mixing_chamber', 'Mixing chamber'))


def simulate_thermal(config: ThermalNetwork, elapsed_s: float, *, rtol: float = 2e-8,
                     atol: float = 1e-10) -> dict:
    """Inspect a deterministic elapsed-time snapshot; never advance wall-clock time.

    Internal tolerance kwargs support validation; they are not public API controls.
    The 350 K domain boundary terminates the trace and marks it nonrunnable.
    Numerical failures raise ArithmeticError, never substitute a temperature.
    """
    config = ThermalNetwork.model_validate(config.model_dump())
    if not math.isfinite(elapsed_s) or not 0 <= elapsed_s <= 604800:
        raise ValueError('Thermal elapsed time must be within 0–604800 seconds.')
    nodes = [getattr(config, name) for name, _ in STAGES]
    initial = np.array([node.initial_temperature_k for node in nodes])
    capacities = np.array([node.heat_capacity_j_per_k for node in nodes])
    loads = np.array([node.heat_load_w for node in nodes])
    baths = np.array([node.bath_temperature_k for node in nodes])
    cooling_g = np.array([node.cooling_conductance_w_per_k for node in nodes])
    cooling_max = np.array([node.cooling_capacity_w for node in nodes])
    g_room = config.room_to_shield_w_per_k
    g_shield = config.shield_to_cold_plate_w_per_k
    g_cold = config.cold_plate_to_mixing_w_per_k

    def powers(temperatures):
        room_heat = g_room * (config.room_temperature_k - temperatures[0])
        shield_to_cold = g_shield * (temperatures[0] - temperatures[1])
        cold_to_mix = g_cold * (temperatures[1] - temperatures[2])
        cooling = np.minimum(cooling_max, np.maximum(0., cooling_g * (temperatures - baths)))
        net = loads + np.array([room_heat - shield_to_cold, shield_to_cold - cold_to_mix, cold_to_mix]) - cooling
        return net, cooling, room_heat

    evaluations = 0

    def rhs(t, state):
        nonlocal evaluations
        evaluations += 1
        if evaluations > 20000:
            raise ArithmeticError('Thermal solver exceeded its bounded evaluation budget.')
        net, cooling, room_heat = powers(state[:3])
        return np.r_[net / capacities, room_heat, sum(cooling)]

    def upper_boundary(t, state):
        # A 0.1 microkelvin event tolerance lets a stationary state exactly on
        # the inclusive boundary remain valid, while outward heating terminates.
        return (350. + 1e-7) - max(state[:3])

    upper_boundary.terminal = True
    upper_boundary.direction = -1
    initial_state = np.r_[initial, 0., 0.]
    terminated = False
    elapsed = float(elapsed_s)
    if elapsed_s == 0:
        times = np.array([0.])
        values = initial_state[:, None]
    else:
        try:
            solution = solve_ivp(rhs, (0., elapsed_s), initial_state, method='Radau',
                                 rtol=rtol, atol=atol, dense_output=True, events=upper_boundary)
        except Exception as exc:
            raise ArithmeticError(f'Thermal integration failed: {exc}') from exc
        if not solution.success or solution.sol is None or not np.isfinite(solution.y).all():
            raise ArithmeticError('Thermal integration failed or produced nonfinite values.')
        elapsed = float(solution.t[-1])
        terminated = solution.status == 1
        # Include internal solver points in diagnostics, even when omitted from
        # the bounded display trace. No temperature clipping hides a failure.
        if float(np.min(solution.y[:3])) < .005 - 1e-7:
            raise ArithmeticError('Thermal integration produced an unphysical temperature.')
        times = np.linspace(0., elapsed, 101)
        values = solution.sol(times)
    if not np.isfinite(values).all() or float(np.min(values[:3])) < .005 - 1e-7:
        raise ArithmeticError('Thermal trace contains invalid temperatures.')
    final = values[:3, -1]
    net, cooling, room_heat = powers(final)
    stored = float(capacities @ (final - initial))
    supplied = float(sum(loads) * elapsed)
    boundary = float(values[3, -1])
    removed = float(values[4, -1])
    residual = stored - (supplied + boundary - removed)
    tolerance = 1e-6 + 2e-7 * max(abs(stored), abs(supplied), abs(boundary), abs(removed))
    if abs(residual) > tolerance:
        raise ArithmeticError('Thermal energy-balance check failed.')
    stages = [{'id': 'room', 'label': 'Fixed room boundary', 'temperature_k': config.room_temperature_k,
               'heat_capacity_j_per_k': None, 'heat_load_w': 0., 'cooling_power_w': 0.,
               'net_power_w': 0., 'boundary_heat_to_shield_w': float(room_heat)}]
    for i, (name, label) in enumerate(STAGES):
        stages.append({'id': name, 'label': label, 'temperature_k': float(final[i]),
                       'heat_capacity_j_per_k': float(capacities[i]), 'heat_load_w': float(loads[i]),
                       'cooling_power_w': float(cooling[i]), 'net_power_w': float(net[i]),
                       'cooling_capacity_w': float(cooling_max[i]),
                       'cooling_saturated': bool(cooling_max[i] > 0 and cooling[i] >= cooling_max[i] * (1 - 1e-10))})
    return {
        'model': 'thermal-network-1', 'valid': not terminated, 'elapsed_s': elapsed,
        'requested_elapsed_s': float(elapsed_s), 'stages': stages,
        'trajectory': [{'time_s': float(t), 'shield_k': float(values[0, i]),
                        'cold_plate_k': float(values[1, i]), 'mixing_chamber_k': float(values[2, i])}
                       for i, t in enumerate(times)],
        'energy': {'stored_change_j': stored, 'heat_input_j': supplied, 'cooling_removed_j': removed,
                   'boundary_heat_j': boundary, 'residual_j': residual},
        'checks': [
            {'name': 'Thermal energy balance', 'passed': abs(residual) <= tolerance,
             'value': abs(residual), 'tolerance': tolerance},
            {'name': 'Thermal temperature domain', 'passed': not terminated,
             'value': float(np.max(values[:3])), 'tolerance': 350.},
        ],
        'solver': 'scipy.integrate.solve_ivp Radau', 'function_evaluations': evaluations,
        'limitations': [
            'Educational lumped thermal circuit with constant heat capacities and conductances; not a calibrated dilution refrigerator or helium-cycle model.',
            'Fixed room boundary, ideal independent active coolers and declared constant heat loads. Cooling is capped by each configured capacity and vanishes at/below its bath setting.',
            'No helium flow, radiation law, temperature-dependent material properties or microwave heating feedback. Microwave attenuation does not silently add a heat load.',
            'Elapsed time is explicitly configured; mixing-chamber temperature is frozen during the subsequent quantum acquisition.',
            'Numerical tolerances and energy balance measure computational consistency, not physical calibration uncertainty.',
        ],
    }
