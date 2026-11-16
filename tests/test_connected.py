"""Independent analytic and ODE references, not a second copy of the solver."""
import math

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.integrate import solve_ivp

from backend.connected import ConnectedRequest, evolve_segment, run_connected
from backend.instruments import ApparatusConfig


def request(sequence='rabi', **patch):
    data = {'sequence': sequence, 'points': 51, **patch}
    return ConnectedRequest.model_validate(data)


def near_ideal_apparatus():
    data = ApparatusConfig().model_dump()
    data['cryostat'].update(base_temperature_k=.005, initial_temperature_k=.005)
    data['device'].update(t1_us=1000, tphi_us=10000)
    data['readout'].update(error_0_to_1=0, error_1_to_0=0)
    return data


@pytest.mark.parametrize('omega,delta,time', [(2, 0, .125), (2, 1.7, .17), (0, 2, .25)])
def test_square_pulse_matches_exact_detuned_rabi(omega, delta, time):
    rho = evolve_segment(np.diag([1., 0.]).astype(complex), time, omega, delta)
    total = math.hypot(omega, delta)
    expected = omega**2 / total**2 * math.sin(math.pi * total * time)**2
    assert rho[1, 1].real == pytest.approx(expected, abs=1e-12)
    assert np.trace(rho) == pytest.approx(1)


def test_signed_detuning_respects_ground_z_positive_convention():
    rho = np.array([[.5, .5], [.5, .5]], complex)
    final = evolve_segment(rho, .125, 0, 1)
    # H/hbar = -2pi*delta*Z/2: initial +X rotates towards -Y.
    assert final[0, 1].imag == pytest.approx(math.sqrt(.125), abs=1e-12)


def test_thermal_t1_and_pure_dephasing_analytic():
    initial = np.diag([0., 1.]).astype(complex)
    result = evolve_segment(initial, 3, 0, 0, gamma_down=.2, gamma_up=.05)
    assert result[1, 1].real == pytest.approx(.2 + .8 * math.exp(-.25 * 3))
    coherent = evolve_segment(np.array([[.5, .5], [.5, .5]], complex), 3, 0, 0, gamma_down=.2, gamma_up=.05, gamma_phi=.1)
    assert coherent[0, 1].real == pytest.approx(.5 * math.exp(-(.125 + .1) * 3))


def test_lindblad_exponential_matches_independent_complex_ode():
    rho = np.array([[.7, .2 + .1j], [.2 - .1j, .3]], complex)
    omega, delta, phase = 3.1, -1.3, .8
    down, up, pure = .07, .02, .03
    x = np.array([[0, 1], [1, 0]], complex)
    y = np.array([[0, -1j], [1j, 0]], complex)
    z = np.diag([1., -1.])
    h = math.pi * (-delta * z + omega * (math.cos(phase) * x + math.sin(phase) * y))
    collapses = [math.sqrt(down) * np.array([[0, 1], [0, 0]]), math.sqrt(up) * np.array([[0, 0], [1, 0]]), math.sqrt(pure / 2) * z]
    def rhs(_, state):
        density = state.reshape(2, 2)
        derivative = -1j * (h @ density - density @ h)
        for c in collapses:
            cc = c.conj().T @ c
            derivative += c @ density @ c.conj().T - .5 * (cc @ density + density @ cc)
        return derivative.ravel()
    ode = solve_ivp(rhs, (0, .73), rho.ravel(), method='DOP853', rtol=1e-11, atol=1e-13)
    actual = evolve_segment(rho, .73, omega, delta, phase, down, up, pure)
    assert ode.success
    assert np.max(np.abs(actual - ode.y[:, -1].reshape(2, 2))) < 3e-11


def test_instantaneous_ramsey_and_echo_limit_reference():
    rho = np.diag([1., 0.]).astype(complex)
    x = np.array([[0, 1], [1, 0]], complex)
    half = (np.eye(2) - 1j * x) / math.sqrt(2)
    pi = -1j * x
    first = half @ rho @ half.conj().T
    tau, delta = .73, 1.4
    ramsey = evolve_segment(first, tau, 0, delta)
    ramsey = half @ ramsey @ half.conj().T
    assert ramsey[1, 1].real == pytest.approx((1 + math.cos(2 * math.pi * delta * tau)) / 2)
    echo = evolve_segment(first, tau / 2, 0, delta)
    echo = pi @ echo @ pi.conj().T
    echo = evolve_segment(echo, tau / 2, 0, delta)
    echo = half.conj().T @ echo @ half
    assert echo[1, 1].real == pytest.approx(1)


def test_finite_ramsey_approaches_instantaneous_formula_and_echo_refocuses_static_detuning():
    app = near_ideal_apparatus()
    app['microwave'].update(frequency_ghz=4.999, power_dbm=6.020599913279624, line_attenuation_db=0)
    app['controller']['pi_duration_us'] = .0025
    ramsey = run_connected(request('ramsey', apparatus=app, sweep_stop=1))
    echo = run_connected(request('echo', apparatus=app, sweep_stop=1))
    for row in ramsey['series']:
        assert row['probability'] == pytest.approx((1 + math.cos(2 * math.pi * row['x'])) / 2, abs=.011)
    assert min(row['probability'] for row in echo['series']) > .998
    assert max(row['probability'] for row in ramsey['series']) - min(row['probability'] for row in ramsey['series']) > .99


def test_t1_curve_includes_actual_finite_preparation_and_thermal_asymptote():
    result = run_connected(request('t1', sweep_stop=200))
    p0 = result['series'][0]['probability']
    derived = result['apparatus_status']['derived']
    thermal = derived['thermal_population']
    for row in result['series']:
        assert row['probability'] == pytest.approx(thermal + (p0 - thermal) * math.exp(-row['x'] / derived['effective_t1_us']), abs=2e-12)
    assert p0 < 1  # actual finite preparation includes loss and thermal population.


def test_readout_is_confusion_then_seeded_binomial_and_count_shots_agree():
    a = run_connected(request(shots=8192, seed=17))
    b = run_connected(request(shots=8192, seed=17))
    c = run_connected(request(shots=8192, seed=18))
    assert a['series'] == b['series']
    assert [r['probability'] for r in a['series']] == [r['probability'] for r in c['series']]
    assert [r['count_1'] for r in a['series']] != [r['count_1'] for r in c['series']]
    for row in a['series']:
        expected = .02 + .94 * row['probability']
        assert row['observed_probability'] == pytest.approx(expected)
        assert row['measured_probability'] == row['count_1'] / 8192
        assert abs(row['measured_probability'] - expected) < 6 * math.sqrt(expected * (1 - expected) / 8192) + .001


def test_readout_calibration_uses_seeded_counts_and_explicit_ideal_preparation_assumption():
    result = run_connected(request('readout_calibration', shots=8192))
    rows, cal = result['series'], result['calibration']
    assert len(rows) == 2
    assert [r['probability'] for r in rows] == [0, 1]
    assert cal['estimated_error_0_to_1'] == rows[0]['count_1'] / 8192
    assert cal['estimated_error_1_to_0'] == 1 - rows[1]['count_1'] / 8192
    assert abs(cal['estimated_error_0_to_1'] - .02) < .01
    assert abs(cal['estimated_error_1_to_0'] - .04) < .01
    assert 'ideal' in cal['preparation_assumption'].lower()


def test_source_frequency_power_and_controller_pulse_duration_affect_measurement():
    base = run_connected(request('rabi', sweep_stop=.1))
    app = ApparatusConfig().model_dump()
    app['microwave']['power_dbm'] = -6.020599913279624
    slower = run_connected(request('rabi', apparatus=app, sweep_stop=.1))
    assert base['series'][-1]['probability'] < .01
    assert slower['series'][-1]['probability'] > .99
    app['microwave']['frequency_ghz'] = 4.99
    detuned = run_connected(request('rabi', apparatus=app, sweep_stop=.1))
    assert max(r['probability'] for r in detuned['series']) < .21
    app = ApparatusConfig().model_dump()
    app['controller']['pi_duration_us'] = .1
    overrotated = run_connected(request('t1', apparatus=app, sweep_stop=10))
    assert overrotated['series'][0]['probability'] < .01


def test_frequency_and_amplitude_sweeps_use_declared_units():
    frequency = run_connected(request('frequency_sweep', sweep_start=-20, sweep_stop=20))
    amplitude = run_connected(request('amplitude_sweep', sweep_start=0, sweep_stop=2))
    assert frequency['series'][25]['probability'] > .99
    assert frequency['series'][0]['probability'] == pytest.approx(frequency['series'][-1]['probability'])
    assert amplitude['series'][0]['probability'] < .001
    assert amplitude['series'][25]['probability'] > .99
    assert amplitude['series'][-1]['probability'] < .01


@pytest.mark.parametrize('sequence', ['rabi', 'ramsey', 'echo', 't1', 'frequency_sweep', 'amplitude_sweep', 'readout_calibration'])
def test_all_sequences_return_physical_results_checks_versions_and_measured_resources(sequence):
    result = run_connected(request(sequence, points=201, shots=8192))
    assert result['kind'] == 'connected' and result['qubits'] == 1
    assert all(check['passed'] for check in result['checks'])
    assert all(0 <= row[key] <= 1 for row in result['series'] for key in ('probability', 'observed_probability', 'measured_probability'))
    assert result['runtime']['wall_seconds'] > 0
    assert result['runtime']['process_rss_bytes'] > 0
    assert 'current process' in result['runtime']['memory_measurement']
    assert result['versions']['scipy'] and result['limitations']


@pytest.mark.parametrize('patch', [{'points': 202}, {'points': 50}, {'shots': 8193}, {'shots': 127}, {'seed': -1}, {'sequence': 'fake'}, {'sweep_stop': float('inf')}, {'sweep_start': 2, 'sweep_stop': 1}, {'sweep_start': -1}, {'sweep_stop': 101}, {'sequence': 'echo', 'sweep_stop': 501}, {'sequence': 'amplitude_sweep', 'sweep_stop': 3}, {'sequence': 'frequency_sweep', 'sweep_start': -101}])
def test_rejects_excessive_invalid_and_nonfinite_requests(patch):
    with pytest.raises(ValidationError):
        request(**patch)


def test_incomplete_and_faulted_apparatus_cannot_acquire():
    app = ApparatusConfig().model_dump()
    app['connections'] = []
    with pytest.raises(ValueError, match='not ready'):
        run_connected(request(apparatus=app))
    app = ApparatusConfig().model_dump()
    app['device']['fault'] = 'injected'
    with pytest.raises(ValueError, match='fault'):
        run_connected(request(apparatus=app))


def test_phase_sensitive_ramsey_fixes_the_absolute_frequency_sign():
    app = near_ideal_apparatus()
    app['microwave'].update(power_dbm=6.020599913279624, line_attenuation_db=0, frequency_ghz=4.999)
    app['controller'].update(pi_duration_us=.0025, analysis_phase_deg=90)
    positive_delta = run_connected(request('ramsey', apparatus=app, sweep_stop=.25))
    app['microwave']['frequency_ghz'] = 5.001
    negative_delta = run_connected(request('ramsey', apparatus=app, sweep_stop=.25))
    # +X90, free physical precession, +Y90: +delta yields ground after a quarter cycle.
    assert positive_delta['series'][-1]['probability'] < .001
    assert negative_delta['series'][-1]['probability'] > .999


def test_echo_with_finite_pulses_approaches_markovian_t2_envelope():
    app = near_ideal_apparatus()
    # Resonance isolates decoherence from finite off-axis pulse errors; static
    # detuning refocusing is constrained separately by the preceding tests.
    app['microwave'].update(power_dbm=6.020599913279624, line_attenuation_db=0, frequency_ghz=5)
    app['controller']['pi_duration_us'] = .0025
    app['device'].update(t1_us=10, tphi_us=20)
    result = run_connected(request('echo', apparatus=app, sweep_stop=30))
    for row in result['series']:
        assert row['probability'] == pytest.approx((1 + math.exp(-row['x'] / 10)) / 2, abs=.001)


def test_long_hot_strong_drive_envelope_is_physical_and_warns_about_undersampling():
    app = ApparatusConfig().model_dump()
    app['cryostat'].update(initial_temperature_k=1, base_temperature_k=1)
    app['device'].update(frequency_ghz=1, max_temperature_k=1, t1_us=1, tphi_us=1)
    app['microwave'].update(frequency_ghz=1, line_attenuation_db=6.020599913279624)
    app['controller']['pi_duration_us'] = 10
    for sequence, stop in [('rabi', 100), ('echo', 500)]:
        result = run_connected(request(sequence, apparatus=app, points=201, shots=8192, sweep_stop=stop))
        assert all(c['passed'] for c in result['checks'])
        assert all(0 <= row['probability'] <= 1 for row in result['series'])
        if sequence == 'rabi':
            assert result['model']['sampling']['warning']


def test_sweep_endpoint_outside_source_or_drive_limits_is_rejected():
    app = ApparatusConfig().model_dump()
    app['device']['frequency_ghz'] = 1
    app['microwave']['frequency_ghz'] = 1
    with pytest.raises(ValidationError, match='source range'):
        request('frequency_sweep', apparatus=app, sweep_start=-10, sweep_stop=10)
    app['microwave'].update(line_attenuation_db=6.020599913279624)
    with pytest.raises(ValidationError, match='drive model limit'):
        request('amplitude_sweep', apparatus=app, sweep_start=0, sweep_stop=2)


def test_result_json_contract_has_legacy_runtime_seconds_and_serializes_without_nan():
    import json
    result = run_connected(request())
    assert result['runtime_s'] == result['runtime']['wall_seconds']
    assert set(('kind', 'backend', 'qubits', 'series', 'metrics', 'checks', 'model', 'limitations', 'runtime', 'versions')).issubset(result)
    assert json.loads(json.dumps(result, allow_nan=False))['kind'] == 'connected'


def test_numerical_nonfinite_propagator_is_rejected_before_sampling(monkeypatch):
    import backend.connected as module
    monkeypatch.setattr(module, 'expm', lambda _: np.full((4, 4), np.nan + 0j))
    with pytest.raises(ArithmeticError, match='nonfinite'):
        run_connected(request())


def test_direct_execution_revalidates_copy_updates_to_preserve_resource_limits():
    invalid = ConnectedRequest().model_copy(update={'points': 202})
    with pytest.raises(ValidationError):
        run_connected(invalid)
    invalid = ConnectedRequest()
    invalid.apparatus.device.t1_us = -1
    with pytest.raises(ValidationError):
        run_connected(invalid)
