"""Calibration uses sampled evidence; references use independent Bloch solutions."""
import copy
import math

import numpy as np
import pytest
from pydantic import ValidationError
from scipy.stats import binomtest

import backend.connected as connected
from backend.instruments import ApparatusConfig, apparatus_status


def request(sequence='amplitude_calibration', **patch):
    return connected.ConnectedRequest.model_validate({
        'sequence': sequence, 'points': 101, 'sweep_start': 0, 'sweep_stop': 2,
        **patch,
    })


@pytest.mark.parametrize('count', [0, 1, 61, 127, 128])
def test_sample_intervals_match_independent_wilson_reference_even_at_boundaries(count):
    assert hasattr(connected, 'wilson_interval')
    low, high = connected.wilson_interval(count, 128)
    reference = binomtest(count, 128).proportion_ci(confidence_level=.95, method='wilson')
    assert low == pytest.approx(reference.low, abs=1e-12)
    assert high == pytest.approx(reference.high, abs=1e-12)
    assert low <= count / 128 <= high
    assert high > low


def test_all_samples_have_intervals_derived_from_returned_counts():
    result = connected.run_connected(request('readout_calibration', shots=128))
    for row in result['series']:
        reference = binomtest(row['count_1'], row['shots']).proportion_ci(method='wilson')
        assert row['confidence_low'] == pytest.approx(reference.low)
        assert row['confidence_high'] == pytest.approx(reference.high)
    assert result['calibration']['confidence_interval_error_0_to_1'] == pytest.approx([
        result['series'][0]['confidence_low'], result['series'][0]['confidence_high']])
    assert result['calibration']['confidence_interval_error_1_to_0'] == pytest.approx([
        1-result['series'][1]['confidence_high'], 1-result['series'][1]['confidence_low']])


def test_default_amplitude_calibration_fits_counts_and_reports_conditional_interval():
    result = connected.run_connected(request(shots=8192))
    estimate = result['amplitude_calibration']
    assert estimate['status'] == 'estimated'
    assert estimate['estimated_pi_factor'] == pytest.approx(1, abs=.004)
    lo, hi = estimate['confidence_interval_95']
    assert lo < estimate['estimated_pi_factor'] < hi
    assert hi-lo < .02
    assert estimate['reference_pi_factor'] == pytest.approx(1)
    assert estimate['estimated_drive_mhz'] == pytest.approx(10, rel=.004)
    assert any('conditional' in text.lower() for text in estimate['assumptions'])
    assert result['reference']['max_absolute_error'] < 1e-11
    assert all(check['passed'] for check in result['checks'])


def test_calibration_follows_changed_source_power_and_repeats_seeded_evidence():
    apparatus = ApparatusConfig().model_dump()
    apparatus['microwave']['power_dbm'] = -2
    actual = connected.run_connected(request(apparatus=apparatus, shots=8192))
    repeated = connected.run_connected(request(apparatus=apparatus, shots=8192))
    assert actual['series'] == repeated['series']
    assert actual['amplitude_calibration'] == repeated['amplitude_calibration']
    assert actual['amplitude_calibration']['estimated_pi_factor'] == pytest.approx(10**.1, abs=.006)
    assert actual['apparatus']['microwave']['power_dbm'] == -2


def test_estimator_uses_counts_not_hidden_simulation_predictions():
    assert hasattr(connected, 'estimate_amplitude_calibration')
    original = request(shots=8192)
    alternate = original.model_dump()
    alternate['apparatus']['microwave']['power_dbm'] = -2
    evidence = connected.run_connected(connected.ConnectedRequest.model_validate(alternate))['series']
    falsified_predictions = copy.deepcopy(evidence)
    for row in falsified_predictions:
        row['probability'] = .123
        row['observed_probability'] = .456
        row['measured_probability'] = .789
    fitted = connected.estimate_amplitude_calibration(original, apparatus_status(original.apparatus)['derived'], evidence)
    again = connected.estimate_amplitude_calibration(original, apparatus_status(original.apparatus)['derived'], falsified_predictions)
    assert fitted == again
    assert fitted['estimated_pi_factor'] == pytest.approx(10**.1, abs=.006)


@pytest.mark.parametrize('change,stop,reason', [
    ({'microwave': {'frequency_ghz': 5.001}}, 2, 'resonance'),
    ({}, .2, 'bracket'),
    ({'readout': {'error_0_to_1': .49, 'error_1_to_0': .49}}, 2, 'contrast'),
])
def test_unsupported_or_unidentifiable_calibration_keeps_measurements_without_fake_estimate(change, stop, reason):
    apparatus = ApparatusConfig().model_dump()
    for name, values in change.items():
        apparatus[name].update(values)
    result = connected.run_connected(request(apparatus=apparatus, sweep_stop=stop, shots=8192))
    estimate = result['amplitude_calibration']
    assert estimate['status'] == 'inconclusive'
    assert estimate['estimated_pi_factor'] is None
    assert estimate['confidence_interval_95'] is None
    assert any(reason in warning.lower() for warning in estimate['warnings'])
    assert len(result['series']) == 101


@pytest.mark.parametrize('patch', [{'sweep_stop': 2.01}, {'sweep_start': -.1}, {'sweep_stop': float('nan')}])
def test_amplitude_calibration_rejects_invalid_sweep(patch):
    with pytest.raises(ValidationError):
        request(**patch)


def test_dephasing_uses_actual_finite_pulses_and_documents_t2_not_pure_tphi():
    apparatus = ApparatusConfig().model_dump()
    apparatus['cryostat'].update(base_temperature_k=.005, initial_temperature_k=.005)
    apparatus['device'].update(t1_us=10, tphi_us=20)
    actual = connected.run_connected(request('dephasing', apparatus=apparatus, sweep_stop=30))
    ramsey = connected.run_connected(request('ramsey', apparatus=apparatus, sweep_stop=30))
    assert actual['series'] == ramsey['series']
    assert actual['apparatus_status']['derived']['effective_t2_us'] == pytest.approx(10)
    assert any('relaxation' in statement for statement in actual['reference']['assumptions'])
    for row in actual['reference']['series']:
        assert row['probability'] == pytest.approx((1 + math.exp(-row['x']/10)) / 2)
    assert actual['reference']['max_absolute_error'] < .005


def test_resonant_bloch_reference_matches_direct_density_matrix_for_damping_regimes():
    assert hasattr(connected, 'resonant_excited_probability')
    thermal, gamma1, gamma2 = .12, .4, .7
    for omega in [0, .001, .03, .3, 10, 200]:
        for duration in [0, .001, .2, 10]:
            expected = connected.evolve_segment(np.diag([1-thermal, thermal]).astype(complex),
                duration, omega, 0, gamma_down=(1-thermal)*gamma1,
                gamma_up=thermal*gamma1, gamma_phi=gamma2-gamma1/2)[1, 1].real
            actual = connected.resonant_excited_probability(np.array([omega]), duration, thermal, gamma1, gamma2)[0]
            assert actual == pytest.approx(expected, abs=2e-12)


def test_optimizer_failure_is_explicit_and_keeps_completed_acquisition(monkeypatch):
    assert hasattr(connected, 'minimize_scalar')
    def broken(*args, **kwargs):
        raise ArithmeticError('Injected optimizer failure')
    monkeypatch.setattr(connected, 'minimize_scalar', broken)
    result = connected.run_connected(request())
    assert result['amplitude_calibration']['status'] == 'inconclusive'
    assert any('fit failed' in text.lower() for text in result['amplitude_calibration']['warnings'])
    assert len(result['series']) == 101


def test_undersampled_source_cannot_alias_into_a_confident_calibration():
    apparatus = ApparatusConfig().model_dump()
    # q=50.5 cycles per field unit, sampled every .02: apparent low-frequency
    # oscillations can alias to q=.5. The declared acquisition is unresolved.
    apparatus['controller']['pi_duration_us'] = 5.05
    result = connected.run_connected(request(apparatus=apparatus, shots=8192))
    estimate = result['amplitude_calibration']
    assert estimate['status'] == 'inconclusive'
    assert estimate['estimated_pi_factor'] is None
    assert any('resolution' in warning.lower() for warning in estimate['warnings'])


def test_subnormal_scan_preserves_acquisition_without_division_failure():
    result = connected.run_connected(request(sweep_stop=float.fromhex('0x0.0000000000001p-1022')))
    assert len(result['series']) == 101
    assert result['amplitude_calibration']['status'] == 'inconclusive'
    assert result['amplitude_calibration']['estimated_pi_factor'] is None
    assert any('resolution' in warning.lower() for warning in result['amplitude_calibration']['warnings'])
