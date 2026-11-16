"""Energy conservation, analytical limiting cases and independent solver checks."""
import math

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.integrate import solve_ivp


def network(**patch):
    from backend.thermal import ThermalNetwork
    data = ThermalNetwork().model_dump()
    for key, value in patch.items():
        if isinstance(value, dict):
            data[key].update(value)
        else:
            data[key] = value
    return ThermalNetwork.model_validate(data)


def simulate(config, elapsed):
    from backend.thermal import simulate_thermal
    return simulate_thermal(config, elapsed)


def stage(result, name='mixing_chamber'):
    return next(item for item in result['stages'] if item['id'] == name)


def isolated(**kwargs):
    return network(room_to_shield_w_per_k=0, shield_to_cold_plate_w_per_k=0,
                   cold_plate_to_mixing_w_per_k=0, **kwargs)


def test_initial_condition_and_energy_are_unchanged_at_zero_elapsed_time():
    result = simulate(network(), 0)
    assert result['valid']
    assert [row['temperature_k'] for row in result['stages']] == [300, 60, 5, .1]
    assert result['energy'] == dict(stored_change_j=0., heat_input_j=0., cooling_removed_j=0., boundary_heat_j=0., residual_j=0.)
    assert len(result['trajectory']) == 1


def test_isolated_cooling_matches_independent_exponential_solution():
    config = isolated(mixing_chamber={'heat_load_w': 0, 'cooling_capacity_w': 1})
    result = simulate(config, 2)
    assert stage(result)['temperature_k'] == pytest.approx(.02 + .08 * math.exp(-2), abs=2e-9)
    assert abs(result['energy']['residual_j']) < 1e-8


def test_zero_cooling_is_linear_heating_and_capacity_limits_cooling():
    config = isolated(mixing_chamber={'initial_temperature_k': .1, 'heat_capacity_j_per_k': 1,
                                     'heat_load_w': .1, 'cooling_capacity_w': 0})
    result = simulate(config, 2)
    assert stage(result)['temperature_k'] == pytest.approx(.3, abs=1e-9)
    capped = isolated(mixing_chamber={'initial_temperature_k': 2, 'bath_temperature_k': .02,
                                     'heat_capacity_j_per_k': 1, 'heat_load_w': 0,
                                     'cooling_conductance_w_per_k': 1, 'cooling_capacity_w': .1})
    cooled = simulate(capped, 2)
    assert stage(cooled)['temperature_k'] == pytest.approx(1.8, abs=1e-9)
    assert stage(cooled)['cooling_power_w'] == pytest.approx(.1)


def test_isolated_coupled_nodes_conserve_energy_and_reach_weighted_equilibrium():
    config = network(room_to_shield_w_per_k=0, shield_to_cold_plate_w_per_k=0,
                     cold_plate_to_mixing_w_per_k=.1,
                     shield={'heat_load_w': 0, 'cooling_capacity_w': 0},
                     cold_plate={'initial_temperature_k': 4, 'heat_capacity_j_per_k': 2, 'heat_load_w': 0, 'cooling_capacity_w': 0},
                     mixing_chamber={'initial_temperature_k': 1, 'heat_capacity_j_per_k': 1, 'heat_load_w': 0, 'cooling_capacity_w': 0})
    result = simulate(config, 200)
    assert stage(result, 'cold_plate')['temperature_k'] == pytest.approx(3, abs=1e-7)
    assert stage(result)['temperature_k'] == pytest.approx(3, abs=1e-7)
    assert abs(result['energy']['stored_change_j']) < 1e-8
    assert abs(result['energy']['residual_j']) < 1e-8


def test_default_network_energy_balance_and_heat_load_sensitivity():
    cold = simulate(network(), 1800)
    warm = simulate(network(mixing_chamber={'heat_load_w': .00005}), 1800)
    assert cold['valid'] and warm['valid']
    assert stage(warm)['temperature_k'] > stage(cold)['temperature_k'] + .02
    assert stage(cold)['temperature_k'] < .03
    assert all(check['passed'] for check in cold['checks'])
    assert all(row['cooling_power_w'] >= 0 for row in cold['stages'])
    energy = cold['energy']
    assert energy['stored_change_j'] == pytest.approx(energy['heat_input_j'] + energy['boundary_heat_j'] - energy['cooling_removed_j'], abs=1e-5)


def test_independent_dop853_solution_matches_radau_and_tolerance_refinement():
    # Moderate stiffness permits an explicit independent integrator. Formula is
    # written independently here, with no production rate/flux helper reused.
    config = isolated(mixing_chamber={'heat_capacity_j_per_k': .5, 'cooling_conductance_w_per_k': .2,
                                     'cooling_capacity_w': .005, 'heat_load_w': .001})
    def reference_rhs(t, y):
        return [.002 - min(.005, max(0., .2 * (y[0] - .02))) / .5]
    reference = solve_ivp(reference_rhs, (0, 30), [.1], method='DOP853', rtol=1e-11, atol=1e-13)
    result = simulate(config, 30)
    assert stage(result)['temperature_k'] == pytest.approx(reference.y[0, -1], abs=2e-9)
    from backend.thermal import simulate_thermal
    finer = simulate_thermal(config, 30, rtol=1e-10, atol=1e-12)
    assert stage(finer)['temperature_k'] == pytest.approx(stage(result)['temperature_k'], abs=2e-9)


def test_boundary_heat_sign_and_stage_capacity_are_recorded():
    result = simulate(network(), 10)
    assert result['energy']['boundary_heat_j'] > 0
    room = stage(result, 'room')
    assert room['temperature_k'] == 300
    assert room['heat_capacity_j_per_k'] is None
    assert stage(result, 'shield')['heat_capacity_j_per_k'] == 500


def test_upper_boundary_allows_cooling_and_stationary_initial_state_but_stops_heating():
    stable = isolated(mixing_chamber={'initial_temperature_k': 350, 'heat_load_w': 0, 'cooling_capacity_w': 0})
    assert simulate(stable, 1)['valid']
    cooling = isolated(mixing_chamber={'initial_temperature_k': 350, 'heat_load_w': 0})
    assert simulate(cooling, 1)['valid']
    heating = isolated(mixing_chamber={'initial_temperature_k': 350, 'heat_load_w': 1, 'cooling_capacity_w': 0})
    assert not simulate(heating, 1)['valid']


def test_out_of_model_temperature_stops_trace_and_cannot_run_quantum_experiment():
    from backend.instruments import ApparatusConfig, apparatus_status, validate_runnable
    hot = isolated(mixing_chamber={'initial_temperature_k': 349, 'heat_capacity_j_per_k': .001,
                                  'heat_load_w': 100, 'cooling_capacity_w': 0})
    result = simulate(hot, 10)
    assert not result['valid']
    assert result['elapsed_s'] < 10
    assert stage(result)['temperature_k'] == pytest.approx(350, abs=1e-6)
    apparatus = ApparatusConfig.model_validate({'cryostat': {'thermal_model': 'thermal_network', 'network': hot.model_dump(), 'elapsed_s': 10}})
    status = apparatus_status(apparatus)
    assert not status['ready']
    assert any(issue['code'] == 'thermal_model_limit' for issue in status['issues'])
    with pytest.raises(ValueError, match='thermal|Thermal'):
        validate_runnable(apparatus)


def test_network_temperature_drives_actual_bath_rates_and_legacy_remains_exact():
    from backend.instruments import ApparatusConfig, apparatus_status
    legacy = apparatus_status(ApparatusConfig())
    assert legacy['derived']['temperature_k'] == .02 + 3.98 * math.exp(-10)
    cold_config = ApparatusConfig.model_validate({'cryostat': {'thermal_model': 'thermal_network'}})
    cold = apparatus_status(cold_config)
    warm_data = cold_config.model_dump()
    warm_data['cryostat']['network']['mixing_chamber']['heat_load_w'] = .00005
    warm = apparatus_status(ApparatusConfig.model_validate(warm_data))
    assert warm['derived']['thermal_population'] > cold['derived']['thermal_population']
    assert warm['derived']['gamma_up_per_us'] > cold['derived']['gamma_up_per_us']
    assert warm['derived']['effective_t1_us'] < cold['derived']['effective_t1_us']


@pytest.mark.parametrize('patch', [
    {'room_temperature_k': float('nan')}, {'mixing_chamber': {'heat_capacity_j_per_k': 0}},
    {'mixing_chamber': {'cooling_capacity_w': -1}}, {'cold_plate_to_mixing_w_per_k': -1},
    {'mixing_chamber': {'initial_temperature_k': 351}}, {'unexpected': 2},
])
def test_invalid_nonfinite_and_unbounded_network_settings_are_rejected(patch):
    with pytest.raises(ValidationError):
        network(**patch)


def test_solver_failure_is_explicit_and_not_replaced_by_fabricated_temperature(monkeypatch):
    import backend.thermal as thermal
    def broken_solver(*args, **kwargs):
        raise RuntimeError('injected solver failure')
    monkeypatch.setattr(thermal, 'solve_ivp', broken_solver)
    with pytest.raises(ArithmeticError, match='Thermal'):
        simulate(network(), 1)
