"""Independent two-level analytic fixtures for the driven Lindblad engine."""
import json
import math

import numpy as np
import pytest
from pydantic import ValidationError


def run(**kwargs):
    from backend.physics import PhysicsRequest, run_physics
    return run_physics(PhysicsRequest(**kwargs))


def test_resonant_ground_state_follows_rabi_formula_in_cycles_per_microsecond():
    result = run(drive_mhz=1, duration_us=1, points=101, t1_us=None, tphi_us=None)
    times = np.array([row['time_us'] for row in result['series']])
    expected = np.sin(math.pi * times) ** 2
    np.testing.assert_allclose([row['ideal_p1'] for row in result['series']], expected, atol=2e-12)
    np.testing.assert_allclose([row['noisy_p1'] for row in result['series']], expected, atol=2e-12)
    assert result['series'][50]['noisy_p1'] == pytest.approx(1)
    assert result['series'][-1]['noisy_p1'] == pytest.approx(0, abs=2e-12)
    assert result['metrics']['t2_us'] is None


@pytest.mark.parametrize('detuning', [-4, 4])
def test_detuning_sets_independent_generalized_frequency_and_contrast(detuning):
    result = run(drive_mhz=3, detuning_mhz=detuning, duration_us=1, points=101,
                 t1_us=None, tphi_us=None)
    times = np.array([row['time_us'] for row in result['series']])
    # The 3-4-5 triangle gives generalized frequency 5 MHz and contrast 9/25.
    expected = (9 / 25) * np.sin(5 * math.pi * times) ** 2
    np.testing.assert_allclose([row['ideal_p1'] for row in result['series']], expected, atol=3e-12)
    np.testing.assert_allclose([row['noisy_p1'] for row in result['series']], expected, atol=3e-12)
    assert result['metrics']['rabi_frequency_mhz'] == pytest.approx(5)


@pytest.mark.parametrize('phase,expected', [
    (0, [0, -1, 0]), (math.pi / 2, [1, 0, 0]), (-math.pi / 2, [-1, 0, 0]),
])
def test_pulse_phase_sets_the_rotation_axis_and_bloch_sign(phase, expected):
    result = run(drive_mhz=1, duration_us=0.25, pulse_phase_rad=phase,
                 t1_us=None, tphi_us=None)
    final = result['series'][-1]
    assert [final['bloch_x'], final['bloch_y'], final['bloch_z']] == pytest.approx(expected, abs=2e-12)


@pytest.mark.parametrize('detuning,expected_y', [(1, 1), (-1, -1)])
def test_signed_detuning_rotates_initial_plus_in_the_declared_frame(detuning, expected_y):
    result = run(drive_mhz=0, detuning_mhz=detuning, duration_us=0.25,
                 initial_state='plus', t1_us=None, tphi_us=None)
    final = result['series'][-1]
    assert [final['bloch_x'], final['bloch_y'], final['bloch_z']] == pytest.approx([0, expected_y, 0], abs=2e-12)


def test_zero_drive_excited_state_relaxes_to_ground_with_t1():
    result = run(drive_mhz=0, duration_us=6, initial_state='excited', t1_us=2, tphi_us=0.3)
    times = np.array([row['time_us'] for row in result['series']])
    np.testing.assert_allclose([row['noisy_p1'] for row in result['series']], np.exp(-times / 2), atol=2e-12)
    np.testing.assert_allclose([row['ideal_p1'] for row in result['series']], np.ones(len(times)), atol=2e-12)
    assert result['series'][-1]['bloch_z'] == pytest.approx(1 - 2 * math.exp(-3))


@pytest.mark.parametrize('t1,tphi,decay_rate', [(None, 3, 1/3), (2, None, 1/4), (2, 3, 7/12)])
def test_plus_coherence_decays_at_the_combined_t2_rate(t1, tphi, decay_rate):
    result = run(drive_mhz=0, duration_us=6, initial_state='plus', t1_us=t1, tphi_us=tphi)
    times = np.array([row['time_us'] for row in result['series']])
    np.testing.assert_allclose([row['bloch_x'] for row in result['series']], np.exp(-decay_rate * times), atol=2e-12)
    np.testing.assert_allclose([row['bloch_y'] for row in result['series']], np.zeros(len(times)), atol=2e-12)
    assert result['metrics']['t2_us'] == pytest.approx(1 / decay_rate)


def test_dephased_plus_state_has_analytic_purity_and_pure_reference_fidelity():
    result = run(drive_mhz=0, duration_us=3, initial_state='plus', t1_us=None, tphi_us=3)
    assert result['metrics']['purity'] == pytest.approx((1 + math.exp(-2)) / 2)
    assert result['metrics']['fidelity_to_ideal'] == pytest.approx((1 + math.exp(-1)) / 2)


@pytest.mark.parametrize('initial_state', ['ground', 'excited', 'plus'])
def test_driven_density_states_preserve_trace_hermiticity_and_positivity(initial_state):
    result = run(drive_mhz=1.7, detuning_mhz=-0.8, pulse_phase_rad=1.2,
                 duration_us=4, t1_us=0.8, tphi_us=0.3, initial_state=initial_state)
    density = np.array([[complex(*entry) for entry in row] for row in result['final_density_matrix']])
    np.testing.assert_allclose(density, density.conj().T, atol=2e-12)
    assert np.trace(density) == pytest.approx(1, abs=2e-12)
    assert np.linalg.eigvalsh(density).min() >= -2e-12
    for row in result['series']:
        radius2 = row['bloch_x']**2 + row['bloch_y']**2 + row['bloch_z']**2
        assert radius2 <= 1 + 2e-12
        assert row['noisy_p1'] == pytest.approx((1 - row['bloch_z']) / 2, abs=2e-12)
    assert result['metrics']['max_trace_error'] < 2e-12
    assert result['metrics']['min_eigenvalue'] >= -2e-12
    assert result['checks']['passed'] is True


def test_readouts_are_reproducible_independent_binomial_experiments_with_theoretical_stderr():
    first = run(drive_mhz=0, initial_state='plus', t1_us=None, tphi_us=None,
                points=51, shots=1024, seed=7)
    second = run(drive_mhz=0, initial_state='plus', t1_us=None, tphi_us=None,
                 points=51, shots=1024, seed=7)
    samples = [row['sampled_p1'] for row in first['series']]
    assert samples == [row['sampled_p1'] for row in second['series']]
    # Initial |+> remains |+>; each time is a fresh 1024-shot experiment, not a collapse chain.
    assert len(set(samples)) > 10
    for row in first['series']:
        assert row['noisy_p1'] == pytest.approx(0.5)
        assert row['stderr'] == pytest.approx(1 / 64)
        assert row['sampled_p1'] * 1024 == pytest.approx(round(row['sampled_p1'] * 1024))


def test_result_schema_is_finite_json_and_includes_model_provenance():
    result = run()
    json.dumps(result, allow_nan=False)
    assert result['kind'] == 'physics'
    assert result['qubits'] == 1
    assert result['seed'] == 42
    assert result['shots'] == 1024
    assert result['runtime_s'] >= 0
    assert set(result['versions']) >= {'numpy', 'scipy'}
    assert len(result['series']) == 301
    assert result['series'][0]['time_us'] == 0
    assert result['series'][-1]['time_us'] == 3
    assert all(row['drive_mhz'] == 1 for row in result['series'])
    assert result['model']['basis'] == ['|0> ground', '|1> excited']
    assert result['limitations']


@pytest.mark.parametrize('payload', [
    {'drive_mhz': -1}, {'drive_mhz': 21}, {'detuning_mhz': 21}, {'detuning_mhz': -21},
    {'duration_us': 0}, {'duration_us': 51}, {'pulse_phase_rad': 7},
    {'t1_us': 0}, {'tphi_us': -1}, {'t1_us': float('inf')},
    {'drive_mhz': float('nan')}, {'points': 50}, {'points': 1002}, {'points': 100.5},
    {'shots': 127}, {'shots': 8193}, {'seed': -1}, {'seed': 2**31},
    {'initial_state': 'unknown'}, {'unexpected': 1},
])
def test_unphysical_or_unbounded_requests_are_rejected(payload):
    from backend.physics import PhysicsRequest
    with pytest.raises(ValidationError):
        PhysicsRequest(**payload)


def test_underresolved_rabi_traces_are_rejected_before_computation():
    from backend.physics import PhysicsRequest
    with pytest.raises(ValidationError, match='samples per'):
        PhysicsRequest(drive_mhz=3, detuning_mhz=4, duration_us=1, points=51)
    # Five cycles need 60 intervals, hence 61 samples including both endpoints.
    assert PhysicsRequest(drive_mhz=3, detuning_mhz=4, duration_us=1, points=61).points == 61
