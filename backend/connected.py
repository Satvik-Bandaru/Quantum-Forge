"""Finite square-pulse, one-qubit Lindblad experiments for connected instruments."""
from __future__ import annotations

import math
import platform
from statistics import NormalDist
import time
from typing import Literal

import numpy as np
import psutil
import scipy
from pydantic import Field, model_validator
from scipy.linalg import expm
from scipy.optimize import brentq, minimize_scalar
from scipy.special import xlog1py, xlogy

from .instruments import ApparatusConfig, apparatus_status, validate_runnable
from .models import StrictModel

Sequence = Literal['rabi', 'ramsey', 'echo', 't1', 'frequency_sweep', 'amplitude_sweep', 'readout_calibration', 'amplitude_calibration', 'dephasing']
AMPLITUDE_SEQUENCES = ('amplitude_sweep', 'amplitude_calibration')


class ConnectedRequest(StrictModel):
    apparatus: ApparatusConfig = Field(default_factory=ApparatusConfig)
    sequence: Sequence = 'rabi'
    points: int = Field(default=101, ge=51, le=201)
    shots: int = Field(default=1024, ge=128, le=8192)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    sweep_start: float = Field(default=0, ge=-100, le=500)
    sweep_stop: float = Field(default=1, ge=-100, le=500)

    @model_validator(mode='after')
    def valid_sweep(self):
        if self.sequence == 'readout_calibration':
            return self
        if self.sweep_stop <= self.sweep_start:
            raise ValueError('Sweep stop must exceed sweep start.')
        lo, hi = (-100, 100) if self.sequence == 'frequency_sweep' else (0, 2 if self.sequence in AMPLITUDE_SEQUENCES else 100 if self.sequence == 'rabi' else 500)
        if self.sweep_start < lo or self.sweep_stop > hi:
            raise ValueError(f'{self.sequence} sweep must stay within [{lo}, {hi}].')
        if self.sequence == 'frequency_sweep':
            f = self.apparatus.device.frequency_ghz
            if f + self.sweep_start / 1000 < 1 or f + self.sweep_stop / 1000 > 10:
                raise ValueError('Frequency sweep must remain within the source range 1–10 GHz.')
        if self.sequence in AMPLITUDE_SEQUENCES:
            drive = apparatus_status(self.apparatus)['derived']['rabi_frequency_mhz']
            if drive * self.sweep_stop > min(200, 50 * self.apparatus.device.frequency_ghz) + 1e-10:
                raise ValueError('Amplitude sweep exceeds the drive model limit (200 MHz or 5% of device frequency).')
        return self


_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.diag([1., -1.]).astype(complex)
_I = np.eye(2, dtype=complex)
_LOWER = np.array([[0, 1], [0, 0]], dtype=complex)


def _liouvillian(omega_mhz, detuning_mhz, phase_rad, gamma_down, gamma_up, gamma_phi):
    # |0> is the ground state (Z=+1), delta = f_device - f_source.
    h = math.pi * (-detuning_mhz * _Z + omega_mhz * (math.cos(phase_rad) * _X + math.sin(phase_rad) * _Y))
    generator = -1j * (np.kron(_I, h) - np.kron(h.T, _I))
    for rate, operator in ((gamma_down, _LOWER), (gamma_up, _LOWER.conj().T), (gamma_phi / 2, _Z)):
        product = operator.conj().T @ operator
        generator += rate * (np.kron(operator.conj(), operator) - .5 * (np.kron(_I, product) + np.kron(product.T, _I)))
    return generator


def evolve_segment(rho: np.ndarray, duration_us: float, omega_mhz: float, detuning_mhz: float,
                   phase_rad: float = 0, gamma_down: float = 0, gamma_up: float = 0,
                   gamma_phi: float = 0) -> np.ndarray:
    """Propagate a constant segment; rates/us, frequencies cycles/us, phase radians.

    Internal scientific kernel: external input is bounded by ConnectedRequest.
    No renormalization or PSD projection hides numerical errors.
    """
    generator = _liouvillian(omega_mhz, detuning_mhz, phase_rad, gamma_down, gamma_up, gamma_phi)
    return (expm(generator * duration_us) @ np.asarray(rho, dtype=complex).reshape(4, order='F')).reshape((2, 2), order='F')


def _segments(request: ConnectedRequest, x: float, derived: dict):
    omega, delta = derived['rabi_frequency_mhz'], derived['detuning_mhz']
    phase = math.radians(request.apparatus.microwave.phase_deg)
    analysis = math.radians(request.apparatus.controller.analysis_phase_deg)
    pi_time = request.apparatus.controller.pi_duration_us
    pulse = lambda duration, phi=phase: (duration, omega, delta, phi)
    free = lambda duration: (duration, 0., delta, 0.)
    if request.sequence == 'rabi':
        return [pulse(x)]
    if request.sequence in ('ramsey', 'dephasing'):
        return [pulse(pi_time / 2), free(x), pulse(pi_time / 2, phase + analysis)]
    if request.sequence == 'echo':
        return [pulse(pi_time / 2), free(x / 2), pulse(pi_time), free(x / 2), pulse(pi_time / 2, phase + math.pi + analysis)]
    if request.sequence == 't1':
        return [pulse(pi_time), free(x)]
    if request.sequence == 'frequency_sweep':
        return [(pi_time, omega, -x, phase)]
    if request.sequence in AMPLITUDE_SEQUENCES:
        return [(pi_time, omega * x, delta, phase)]
    return []


def wilson_interval(count: int, shots: int, confidence: float = .95) -> tuple[float, float]:
    """Pointwise binomial score interval; not a physical-model error bar."""
    if shots <= 0 or count < 0 or count > shots or not 0 < confidence < 1:
        raise ValueError('Wilson interval requires valid binomial counts and confidence.')
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    p = count / shots
    denominator = 1 + z*z / shots
    center = (p + z*z / (2*shots)) / denominator
    radius = z * math.sqrt(p*(1-p)/shots + z*z/(4*shots*shots)) / denominator
    return max(0., center-radius), min(1., center+radius)


def resonant_excited_probability(omega_mhz: np.ndarray, duration_us: float,
                                thermal_population: float, gamma1: float,
                                gamma2: float) -> np.ndarray:
    """Independent closed-form resonant Bloch solution, initially at equilibrium.

    z''+(gamma1+gamma2)z'+(gamma1*gamma2+w²)z=gamma1*gamma2*z_eq.
    Complex square roots cover under/over/critical damping without branch formulas.
    This does not call the production Liouvillian or matrix exponential.
    """
    angular = 2*math.pi*np.asarray(omega_mhz, dtype=float)
    equilibrium = 1 - 2*thermal_population
    product = gamma1*gamma2
    steady = equilibrium*product / (product + angular*angular)
    decay = (gamma1+gamma2)/2
    frequency = np.sqrt((angular*angular - ((gamma1-gamma2)/2)**2).astype(complex))
    argument = frequency*duration_us
    envelope = np.exp(-decay*duration_us) * (
        np.cos(argument) + decay*duration_us*np.sinc(argument/math.pi))
    z = steady + (equilibrium-steady)*envelope.real
    return (1-z)/2


def estimate_amplitude_calibration(request: ConnectedRequest, derived: dict,
                                   series: list[dict]) -> dict:
    """Conditional one-parameter binomial MLE using counts, never predicted rows.

    Fit the cyclic pulse area q=Omega*t_pi with declared nuisance settings fixed.
    A bounded global scan finds modes before local minimization. The asymptotic
    95% profile interval uses 2*Delta(NLL)<=3.841458820694124. This interval is
    conditional on the declared thermal/decoherence/assignment model being exact.
    """
    duration = request.apparatus.controller.pi_duration_us
    step = (request.sweep_stop-request.sweep_start)/(request.points-1)
    max_field = request.sweep_stop
    estimate = {
        'status': 'inconclusive',
        'method': 'Conditional binomial maximum likelihood; resonant damped Bloch solution; 95% likelihood-ratio interval',
        'estimated_pi_factor': None, 'confidence_interval_95': None,
        'reference_pi_factor': 1/(2*derived['rabi_frequency_mhz']*duration),
        'estimated_drive_mhz': None, 'negative_log_likelihood': None,
        'fit_bounds': [],
        'assumptions': [
            'Only drive gain is inferred from returned count_1 and shots. Temperature, T1, Tphi and readout assignment probabilities are held at their declared values.',
            'The asymptotic 95% interval is conditional on that model; it excludes uncertainty in the fixed settings, model discrepancy and hardware drift.',
            'The pi factor means a resonant pi pulse area, not necessarily the exact population maximum with damping. It does not rewrite instrument settings.',
            'The scan must start at zero, resolve at least ten points per candidate oscillation and bracket a single identifiable pi-factor interval.',
        ],
        'warnings': [],
    }
    warnings = estimate['warnings']
    if max_field < 1e-12 or step <= 0:
        warnings.append('Sweep resolution is below the supported field-factor range; widen the scan before fitting.')
        return estimate
    if step * derived['rabi_frequency_mhz'] * duration > .1 + 1e-12:
        warnings.append('Acquisition resolution is below ten samples per declared drive oscillation; aliased measurements cannot support this calibration. Narrow the sweep, shorten the pulse or increase points.')
        return estimate
    q_min = 1/(4*max_field)  # allows a pi factor as large as twice the scan range
    q_max = min(1/(10*step), min(200, 50*request.apparatus.device.frequency_ghz)*duration/max_field)
    estimate['fit_bounds'] = [1/(2*q_max), 1/(2*q_min)]
    if abs(derived['detuning_mhz']) > 1e-9:
        warnings.append('Amplitude calibration requires source/device resonance; the acquired detuned trace is retained without an estimate.')
        return estimate
    if request.sweep_start != 0 or q_max <= q_min:
        warnings.append('The sweep cannot bracket the supported pi-factor fit; start at zero and widen the field-factor range.')
        return estimate
    readout = request.apparatus.readout
    if 1-readout.error_0_to_1-readout.error_1_to_0 < .05:
        warnings.append('Declared assignment contrast is below 0.05; calibration is not identifiable with this bounded acquisition.')
        return estimate
    simultaneous = [wilson_interval(row['count_1'], row['shots'], 1-.05/len(series)) for row in series]
    if max(pair[0] for pair in simultaneous) <= min(pair[1] for pair in simultaneous):
        warnings.append('Sampled contrast is unresolved by conservative simultaneous score intervals; increase shots or improve pulse/readout contrast.')
        return estimate
    xs = np.array([row['x'] for row in series])
    counts = np.array([row['count_1'] for row in series])
    shots = np.array([row['shots'] for row in series])
    gamma1, gamma2 = 1/derived['effective_t1_us'], 1/derived['effective_t2_us']

    def nll(q):
        population = resonant_excited_probability(xs*q/duration, duration,
            derived['thermal_population'], gamma1, gamma2)
        observed = np.clip(readout.error_0_to_1 + (1-readout.error_0_to_1-readout.error_1_to_0)*population, 0, 1)
        return float(-np.sum(xlogy(counts, observed) + xlog1py(shots-counts, -observed)))

    try:
        grid = np.linspace(q_min, q_max, 2049)
        profile = np.array([nll(q) for q in grid])
        if not np.isfinite(profile).all():
            raise ArithmeticError('Nonfinite likelihood')
        minima = np.flatnonzero((profile[1:-1] <= profile[:-2]) & (profile[1:-1] <= profile[2:])) + 1
        candidates = [(profile[0], q_min), (profile[-1], q_max)]
        for index in minima:
            fit = minimize_scalar(nll, bounds=(grid[index-1], grid[index+1]), method='bounded',
                                  options={'xatol': 1e-12, 'maxiter': 128})
            if not fit.success or not math.isfinite(fit.fun):
                raise ArithmeticError('Likelihood optimizer did not converge')
            candidates.append((float(fit.fun), float(fit.x)))
        candidates.sort()
        best, q = candidates[0]
        threshold = best + 1.920729410347062
        if len([value for value, _ in candidates if value <= threshold]) > 1:
            warnings.append('Multiple fitted pulse areas are statistically unresolved; narrow the sweep or improve resolution and contrast.')
            return estimate
        left = np.flatnonzero((grid < q) & (profile >= threshold))
        right = np.flatnonzero((grid > q) & (profile >= threshold))
        if not len(left) or not len(right):
            warnings.append('The likelihood interval reaches a fit boundary; the acquisition does not bracket a supported calibration.')
            return estimate
        q_low = brentq(lambda trial: nll(trial)-threshold, grid[left[-1]], q, xtol=1e-12)
        q_high = brentq(lambda trial: nll(trial)-threshold, q, grid[right[0]], xtol=1e-12)
        interval = [1/(2*q_high), 1/(2*q_low)]
        if interval[0] <= request.sweep_start+step or interval[1] >= request.sweep_stop-step:
            warnings.append('The measured range does not bracket the pi-factor confidence interval; widen the field-factor sweep.')
            return estimate
        estimate.update(status='estimated', estimated_pi_factor=1/(2*q),
                        confidence_interval_95=interval, estimated_drive_mhz=q/duration,
                        negative_log_likelihood=best)
    except (ArithmeticError, ValueError, RuntimeError, FloatingPointError) as error:
        warnings.append(f'Calibration fit failed ({type(error).__name__}); the completed acquisition is retained without a fitted estimate.')
    return estimate


def run_connected(request: ConnectedRequest) -> dict:
    started = time.perf_counter()
    # Pydantic model_copy updates and nested assignment can bypass constructors.
    # Revalidate the complete execution snapshot before allocating sweep arrays.
    request = ConnectedRequest.model_validate(request.model_dump())
    status = validate_runnable(request.apparatus)
    derived = status['derived']
    rng = np.random.default_rng(request.seed)
    calibration = request.sequence == 'readout_calibration'
    xs = [0., 1.] if calibration else np.linspace(request.sweep_start, request.sweep_stop, request.points).tolist()
    initial = np.diag([1 - derived['thermal_population'], derived['thermal_population']]).astype(complex)
    down, up, pure = derived['gamma_down_per_us'], derived['gamma_up_per_us'], 1 / request.apparatus.device.tphi_us
    trace_error = hermiticity_error = subdivision_error = 0.
    min_eigenvalue = 1.
    probabilities = []
    cache = {}

    def monitor(rho):
        nonlocal trace_error, hermiticity_error, min_eigenvalue
        if not np.isfinite(rho).all():
            raise ArithmeticError('Numerical propagation produced a nonfinite density matrix.')
        trace_error = max(trace_error, float(abs(np.trace(rho) - 1)))
        hermiticity_error = max(hermiticity_error, float(np.max(np.abs(rho - rho.conj().T))))
        min_eigenvalue = min(min_eigenvalue, float(np.min(np.linalg.eigvalsh((rho + rho.conj().T) / 2))))

    for x in xs:
        rho = np.diag([1 - x, x]).astype(complex) if calibration else initial.copy()
        refined = rho.copy()
        monitor(rho)
        for duration, omega, delta, phase in _segments(request, x, derived):
            key = (duration, omega, delta, phase)
            if key not in cache:
                generator = _liouvillian(omega, delta, phase, down, up, pure)
                whole = expm(generator * duration)
                half = expm(generator * (duration / 2))
                cache[key] = whole, half @ half
            whole, divided = cache[key]
            rho = (whole @ rho.reshape(4, order='F')).reshape((2, 2), order='F')
            refined = (divided @ refined.reshape(4, order='F')).reshape((2, 2), order='F')
            monitor(rho)
            if not np.isfinite(refined).all():
                raise ArithmeticError('Subdivision propagation produced a nonfinite density matrix.')
            subdivision_error = max(subdivision_error, float(np.max(np.abs(rho - refined))))
        probabilities.append(float(rho[1, 1].real))
    physical_tolerance = 1e-8
    probability_error = max(0., -min(probabilities), max(probabilities) - 1.)
    checks = [
        {'name': 'Density matrix trace', 'passed': trace_error <= physical_tolerance, 'value': trace_error, 'tolerance': physical_tolerance},
        {'name': 'Hermiticity', 'passed': hermiticity_error <= physical_tolerance, 'value': hermiticity_error, 'tolerance': physical_tolerance},
        {'name': 'Positive density matrix (negative eigenvalue magnitude)', 'passed': min_eigenvalue >= -physical_tolerance, 'value': max(0., -min_eigenvalue), 'tolerance': physical_tolerance},
        {'name': 'Probability bounds', 'passed': probability_error <= physical_tolerance, 'value': probability_error, 'tolerance': physical_tolerance},
        {'name': 'Segment subdivision consistency (same exponential algorithm)', 'passed': subdivision_error <= physical_tolerance, 'value': subdivision_error, 'tolerance': physical_tolerance},
    ]
    if not all(check['passed'] for check in checks):
        raise ArithmeticError('Numerical physicality or subdivision check failed; acquisition was not returned.')
    readout = request.apparatus.readout
    series = []
    for x, probability in zip(xs, probabilities):
        # Clip only roundoff after enforcing physicality above, never a bad state.
        probability = float(np.clip(probability, 0, 1))
        observed = float(np.clip(readout.error_0_to_1 + (1 - readout.error_0_to_1 - readout.error_1_to_0) * probability, 0, 1))
        count = int(rng.binomial(request.shots, observed))
        confidence_low, confidence_high = wilson_interval(count, request.shots)
        series.append({'x': float(x), 'probability': probability, 'observed_probability': observed,
                       'measured_probability': count / request.shots, 'count_1': count, 'shots': request.shots,
                       'confidence_low': confidence_low, 'confidence_high': confidence_high})
    unit = 'MHz' if request.sequence == 'frequency_sweep' else 'field scale' if request.sequence in AMPLITUDE_SEQUENCES else 'state' if calibration else 'µs'
    label = 'Source offset from device resonance' if request.sequence == 'frequency_sweep' else 'Microwave field amplitude factor' if request.sequence in AMPLITUDE_SEQUENCES else 'Ideally prepared state' if calibration else 'Pulse duration' if request.sequence == 'rabi' else 'Total free evolution delay'
    thermal_description = ('Cryostat uses the configured lumped thermal network, not calibrated dilution refrigeration; '
                           if getattr(request.apparatus.cryostat, 'thermal_model', 'legacy_exponential') == 'thermal_network'
                           else 'Cryostat is an explicit elapsed-time exponential approximation; ')
    limitations = [
        'Synthetic one-device two-level rotating-wave model; no hardware execution or manufacturer calibration.',
        'Markovian thermal amplitude damping and pure dephasing; excludes leakage, non-Markovian noise, crosstalk and resonator dynamics.',
        thermal_description + 'temperature is frozen during each acquisition and the state is thermally reset before each point.',
        'Declared coupling converts attenuated source power to drive; finite square pulses include detuning and decoherence. Pi duration is user configured, never automatically calibrated.',
        'Readout is a state-independent binary confusion channel plus independent binomial shot noise; counts do not include amplifier waveforms or acquisition latency.',
        'Subdivision is a floating-point consistency diagnostic using the same exponential method, not independent solver validation or an estimate of physical-model error.',
        'Discrete exact sample predictions can miss oscillations between points; plotted interpolation is not an additional simulation.',
        'Per-point 95% Wilson intervals describe finite independent binomial sampling of the assignment-channel probability, not uncertainty in the physical model; they are not simultaneous confidence bands.',
    ]
    spacing = 0. if calibration else (request.sweep_stop - request.sweep_start) / (request.points - 1)
    cycles_per_step = 0.
    if request.sequence == 'rabi':
        cycles_per_step = spacing * math.hypot(derived['rabi_frequency_mhz'], derived['detuning_mhz'])
    elif request.sequence in ('ramsey', 'echo', 'dephasing'):
        cycles_per_step = spacing * abs(derived['detuning_mhz'])
    elif request.sequence in AMPLITUDE_SEQUENCES:
        cycles_per_step = spacing * derived['rabi_frequency_mhz'] * request.apparatus.controller.pi_duration_us
    elif request.sequence == 'frequency_sweep':
        cycles_per_step = spacing * request.apparatus.controller.pi_duration_us
    sampling_warning = None
    if cycles_per_step > .1 + 1e-12:
        sampling_warning = 'Sweep resolution is below 10 samples per estimated fastest oscillation; narrow the range or raise points. Predictions are valid only at returned samples.'
        limitations.append(sampling_warning)
    result = {
        'kind': 'connected', 'backend': 'SciPy finite-segment Lindblad simulator', 'qubits': 1,
        'sequence': request.sequence, 'seed': request.seed, 'shots': request.shots,
        'apparatus': request.apparatus.model_dump(), 'apparatus_status': status,
        'series': series, 'axes': {'x_label': label, 'x_unit': unit, 'y_label': 'Excited-state probability'},
        'metrics': [
            {'label': 'Model temperature', 'value': derived['temperature_k'], 'unit': 'K'},
            {'label': 'Thermal excited population', 'value': derived['thermal_population'], 'unit': ''},
            {'label': 'Model drive frequency', 'value': derived['rabi_frequency_mhz'], 'unit': 'MHz'},
            {'label': 'Model effective T1', 'value': derived['effective_t1_us'], 'unit': 'µs'},
            {'label': 'Model effective T2', 'value': derived['effective_t2_us'], 'unit': 'µs'},
            {'label': 'Sampled probability range', 'value': max(r['measured_probability'] for r in series) - min(r['measured_probability'] for r in series), 'unit': ''},
        ],
        'checks': checks,
        'model': {
            'name': 'One-qubit finite-temperature Lindblad model',
            'basis': '|0> ground, |1> excited; Z=diag(1,-1)',
            'hamiltonian': 'H/hbar = pi * [-detuning_MHz Z + drive_MHz (cos(phase) X + sin(phase) Y)] per microsecond',
            'detuning_convention': 'device frequency minus source frequency; frequency sweep x is source minus device in MHz',
            'thermal_rates': 'gamma_down=(nbar+1)/T1_zero, gamma_up=nbar/T1_zero; nbar=1/expm1(h*f/(k*T))',
            'pulse_convention': 'Ramsey: +half, free, +half with analysis phase; echo: +half, free/2, +pi, free/2, -half with analysis phase.',
            'initial_state': 'Ideal |0> or |1> for readout calibration only' if calibration else 'Thermal equilibrium density matrix at the inspected temperature',
            'sampling': {'spacing': spacing, 'unit': unit, 'estimated_cycles_per_step': cycles_per_step, 'warning': sampling_warning},
            'measurement_uncertainty': '95% pointwise Wilson score interval for assignment-channel binomial probability; fixed physical settings and independent shots',
            'sources': [
                {'title': 'QuTiP Lindblad master equation and assumptions', 'url': 'https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-master.html'},
                {'title': 'QuTiP thermal bath collapse operators', 'url': 'https://qutip.readthedocs.io/en/stable/guide/guide-steady.html'},
                {'title': 'SciPy matrix exponential', 'url': 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html'},
                {'title': 'NIST binomial confidence intervals', 'url': 'https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm'},
            ],
        },
        'limitations': limitations,
        'versions': {'python': platform.python_version(), 'numpy': np.__version__, 'scipy': scipy.__version__, 'model': 'connected-lindblad-2'},
    }
    if calibration:
        e01, e10 = series[0]['measured_probability'], 1 - series[1]['measured_probability']
        result['calibration'] = {
            'preparation_assumption': 'Ideal independently prepared |0> and |1>; preparation and pulse errors are excluded, so estimates identify only the synthetic assignment channel.',
            'estimated_error_0_to_1': e01, 'estimated_error_1_to_0': e10,
            'estimated_assignment_fidelity': 1 - (e01 + e10) / 2,
            'standard_error_0_to_1': math.sqrt(e01 * (1 - e01) / request.shots),
            'standard_error_1_to_0': math.sqrt(e10 * (1 - e10) / request.shots),
            'confidence_interval_error_0_to_1': [series[0]['confidence_low'], series[0]['confidence_high']],
            'confidence_interval_error_1_to_0': [1-series[1]['confidence_high'], 1-series[1]['confidence_low']],
        }
        result['metrics'] = [
            {'label': 'Estimated P(1 | prepared 0)', 'value': e01, 'unit': ''},
            {'label': 'Estimated P(0 | prepared 1)', 'value': e10, 'unit': ''},
            {'label': 'Estimated assignment fidelity', 'value': 1 - (e01 + e10) / 2, 'unit': ''},
        ]
        limitations.append(result['calibration']['preparation_assumption'])
    if request.sequence == 'amplitude_calibration':
        result['amplitude_calibration'] = estimate_amplitude_calibration(request, derived, series)
        limitations.extend(result['amplitude_calibration']['assumptions'])
        limitations.extend(result['amplitude_calibration']['warnings'])
        if abs(derived['detuning_mhz']) <= 1e-9:
            analytic = resonant_excited_probability(np.asarray(xs)*derived['rabi_frequency_mhz'],
                request.apparatus.controller.pi_duration_us, derived['thermal_population'],
                1/derived['effective_t1_us'], 1/derived['effective_t2_us'])
            difference = float(np.max(np.abs(analytic-np.asarray(probabilities))))
            result['reference'] = {
                'label': 'Independent resonant damped Bloch analytical solution',
                'assumptions': ['Exact resonance, initial thermal equilibrium, constant square drive and the same declared Markovian rates. This evaluates declared settings, not the fitted gain.'],
                'max_absolute_error': difference,
                'series': [{'x': x, 'probability': float(p)} for x, p in zip(xs, analytic)],
            }
            checks.append({'name': 'Independent resonant Bloch analytical reference',
                           'passed': difference <= 1e-8, 'value': difference, 'tolerance': 1e-8})
            if difference > 1e-8 or not math.isfinite(difference):
                raise ArithmeticError('Independent resonant Bloch reference check failed.')
    if request.sequence == 'dephasing':
        analytic = [.5*(1+(1-2*derived['thermal_population'])*math.exp(-x/derived['effective_t2_us'])*
                        math.cos(2*math.pi*derived['detuning_mhz']*x+math.radians(request.apparatus.controller.analysis_phase_deg))) for x in xs]
        result['reference'] = {
            'label': 'Instantaneous calibrated half-pulse T2 reference',
            'assumptions': [
                'Reference assumes ideal instantaneous calibrated half pulses; the executed trace includes the configured finite pulses, their errors and damping.',
                'T2 includes both relaxation and pure dephasing: 1/T2 = 1/(2*T1_effective) + 1/Tphi. It is not a fitted estimate of Tphi.',
                'Detuning adds Ramsey fringes; at resonance and zero analysis phase the reference is a decay envelope.',
            ],
            'max_absolute_error': max(abs(row['probability']-p) for row, p in zip(series, analytic)),
            'series': [{'x': x, 'probability': p} for x, p in zip(xs, analytic)],
        }
        limitations.extend(result['reference']['assumptions'])
    result['runtime'] = {'wall_seconds': time.perf_counter() - started,
                         'process_rss_bytes': psutil.Process().memory_info().rss,
                         'memory_measurement': 'current process resident set after run; includes interpreter and imported libraries, not incremental job memory or a peak',
                         'points': len(series), 'shots_per_point': request.shots,
                         'solver': 'scipy.linalg.expm', 'matrix_dimension': 4}
    result['runtime_s'] = result['runtime']['wall_seconds']
    return result
