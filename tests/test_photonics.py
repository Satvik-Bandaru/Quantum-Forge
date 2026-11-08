"""Analytic classical optics fixtures, independent of the transfer-matrix code."""

import json
import math

import numpy as np
import pytest
from pydantic import ValidationError


def simulate(**kwargs):
    from backend.photonics import PhotonicsRequest, run_photonics

    return run_photonics(PhotonicsRequest(**kwargs))


@pytest.mark.parametrize('phase,expected', [
    (0, [0, 1]),
    (math.pi / 2, [.5, .5]),
    (math.pi, [1, 0]),
    (-math.pi, [1, 0]),
    (2 * math.pi, [0, 1]),
    (4 * math.pi, [0, 1]),
])
def test_balanced_interferometer_matches_sine_squared_fringe(phase, expected):
    result = simulate(phase_rad=phase, meter_noise_mw=0)
    metrics = result['metrics']
    assert [metrics['port0_mw'], metrics['port1_mw']] == pytest.approx(expected, abs=1e-14)
    assert metrics['visibility0'] == pytest.approx(1)
    assert metrics['visibility1'] == pytest.approx(1)
    assert metrics['loss_mw'] == pytest.approx(0, abs=1e-14)


def test_complex_output_fields_use_stated_beam_splitter_phase_convention():
    result = simulate(power_mw=4, phase_rad=math.pi / 2)
    np.testing.assert_allclose(result['output_fields'], [[-1, 1], [-1, 1]], atol=1e-14)
    assert sum(real * real + imag * imag for real, imag in result['output_fields']) == pytest.approx(4)


@pytest.mark.parametrize('wavelength,path,expected_phase,expected_powers', [
    (633, .15825, math.pi / 2, [.5, .5]),
    (633, .3165, math.pi, [1, 0]),
    (500, 1, 4 * math.pi, [0, 1]),
    (500, -.125, -math.pi / 2, [.5, .5]),
])
def test_path_difference_converts_micrometres_to_nanometres(wavelength, path, expected_phase, expected_powers):
    result = simulate(wavelength_nm=wavelength, path_difference_um=path)
    metrics = result['metrics']
    assert metrics['effective_phase_rad'] == pytest.approx(expected_phase)
    assert [metrics['port0_mw'], metrics['port1_mw']] == pytest.approx(expected_powers, abs=1e-14)


def test_path_phase_and_phase_shifter_add():
    result = simulate(wavelength_nm=500, path_difference_um=.125, phase_rad=math.pi / 2)
    assert result['metrics']['effective_phase_rad'] == pytest.approx(math.pi)
    assert result['metrics']['port0_mw'] == pytest.approx(1)
    assert result['metrics']['port1_mw'] == pytest.approx(0, abs=1e-14)


def test_unbalanced_lossy_interferometer_matches_hand_calculated_extrema():
    metrics = simulate(power_mw=10, splitter1=.25, splitter2=.75,
                       upper_transmission=.8, lower_transmission=.2)['metrics']
    assert metrics['port0_mw'] == pytest.approx(.375)
    assert metrics['port1_mw'] == pytest.approx(3.125)
    assert metrics['total_output_mw'] == pytest.approx(3.5)
    assert metrics['loss_mw'] == pytest.approx(6.5)
    assert metrics['visibility0'] == pytest.approx(.8)
    assert metrics['visibility1'] == pytest.approx(12 / 13)
    assert [metrics['port0_min_mw'], metrics['port0_max_mw']] == pytest.approx([.375, 3.375])
    assert [metrics['port1_min_mw'], metrics['port1_max_mw']] == pytest.approx([.125, 3.125])


@pytest.mark.parametrize('upper,lower,powers', [(0, 1, [.25, .25]), (1, 0, [.25, .25])])
def test_blocking_either_arm_removes_interference(upper, lower, powers):
    result = simulate(upper_transmission=upper, lower_transmission=lower, path_difference_um=.123)
    assert [result['metrics']['port0_mw'], result['metrics']['port1_mw']] == pytest.approx(powers)
    assert result['metrics']['visibility0'] == 0
    assert result['metrics']['visibility1'] == 0
    for row in result['series']:
        assert [row['port0_mw'], row['port1_mw']] == pytest.approx(powers)


@pytest.mark.parametrize('splitter1,splitter2,powers', [
    (1, 1, [1, 0]), (1, 0, [0, 1]), (0, 1, [0, 1]), (0, 0, [1, 0]),
])
def test_extreme_splitters_route_power_without_interference(splitter1, splitter2, powers):
    metrics = simulate(splitter1=splitter1, splitter2=splitter2, phase_rad=.713)['metrics']
    assert [metrics['port0_mw'], metrics['port1_mw']] == pytest.approx(powers)
    for port, power in enumerate(powers):
        assert metrics[f'visibility{port}'] == (0 if power else None)


def test_no_signal_has_undefined_visibility_and_no_physical_power():
    result = simulate(upper_transmission=0, lower_transmission=0, meter_noise_mw=0)
    metrics = result['metrics']
    assert [metrics['port0_mw'], metrics['port1_mw'], metrics['total_output_mw']] == [0, 0, 0]
    assert metrics['loss_mw'] == 1
    assert metrics['visibility0'] is None
    assert metrics['visibility1'] is None
    assert result['output_fields'] == [[0, 0], [0, 0]]


def test_splitters_and_arm_losses_conserve_power_for_random_configurations():
    rng = np.random.default_rng(812)
    cases = [(a, b, upper, lower) for a in [0, .5, 1] for b in [0, .5, 1]
             for upper, lower in [(0, 0), (0, 1), (1, 0), (1, 1)]]
    cases.extend(tuple(row) for row in rng.uniform(0, 1, size=(50, 4)))
    for first, second, upper, lower in cases:
        result = simulate(power_mw=7.2, splitter1=first, splitter2=second,
                          upper_transmission=upper, lower_transmission=lower,
                          phase_rad=float(rng.uniform(-4 * math.pi, 4 * math.pi)), points=51)
        expected_output = 7.2 * (first * upper + (1 - first) * lower)
        metrics = result['metrics']
        assert metrics['total_output_mw'] == pytest.approx(expected_output, abs=2e-14)
        assert metrics['loss_mw'] == pytest.approx(7.2 - expected_output, abs=2e-14)
        assert metrics['power_balance_error_mw'] == pytest.approx(0, abs=2e-14)
        for row in result['series']:
            assert row['port0_mw'] >= 0
            assert row['port1_mw'] >= 0
            assert row['total_output_mw'] == pytest.approx(expected_output, abs=2e-14)


def test_visibility_uses_exact_extrema_independent_of_phase_grid_and_path_offset():
    fine = simulate(splitter1=.25, splitter2=.75, upper_transmission=.8,
                    lower_transmission=.2, path_difference_um=.123, points=721)
    coarse = simulate(splitter1=.25, splitter2=.75, upper_transmission=.8,
                      lower_transmission=.2, path_difference_um=.123, points=51)
    for result in [fine, coarse]:
        assert result['metrics']['visibility0'] == pytest.approx(.8)
        assert result['metrics']['visibility1'] == pytest.approx(12 / 13)
    assert len(coarse['series']) == 51
    assert coarse['series'][0]['phase_rad'] == 0
    assert coarse['series'][-1]['phase_rad'] == pytest.approx(2 * math.pi)
    assert coarse['series'][-1]['phase_pi'] == pytest.approx(2)
    assert coarse['series'][0]['port0_mw'] == pytest.approx(coarse['series'][-1]['port0_mw'])
    assert coarse['series'][0]['port0_mw'] != pytest.approx(.0375)


def test_zero_noise_meter_readings_equal_predicted_powers():
    result = simulate(power_mw=3, phase_rad=math.pi / 2, meter_noise_mw=0, shots=16)
    for port in (0, 1):
        readings = result['meter_readings'][f'port{port}']
        assert len(readings) == 16
        assert readings == pytest.approx([1.5] * 16)
        assert result['metrics'][f'meter{port}_mean_mw'] == pytest.approx(1.5)
        assert result['metrics'][f'meter{port}_stderr_mw'] == 0
        assert result['metrics'][f'meter{port}_expected_stderr_mw'] == 0


def test_seed_reproduces_independent_gaussian_meter_data_and_retains_negative_readings():
    first = simulate(meter_noise_mw=.2, shots=4096, seed=34)
    same = simulate(meter_noise_mw=.2, shots=4096, seed=34)
    different = simulate(meter_noise_mw=.2, shots=4096, seed=35)
    assert first['meter_readings'] == same['meter_readings']
    assert first['meter_readings'] != different['meter_readings']
    zero = np.array(first['meter_readings']['port0'])
    one = np.array(first['meter_readings']['port1'])
    assert np.any(zero < 0)
    assert np.std(zero, ddof=1) == pytest.approx(.2, rel=.04)
    assert np.std(one, ddof=1) == pytest.approx(.2, rel=.04)
    assert abs(np.corrcoef(zero, one)[0, 1]) < .05
    assert zero.mean() == pytest.approx(0, abs=.015)
    assert one.mean() == pytest.approx(1, abs=.015)
    for port, samples in enumerate([zero, one]):
        metrics = first['metrics']
        assert metrics[f'meter{port}_mean_mw'] == pytest.approx(samples.mean())
        assert metrics[f'meter{port}_std_mw'] == pytest.approx(samples.std(ddof=1))
        assert metrics[f'meter{port}_stderr_mw'] == pytest.approx(samples.std(ddof=1) / 64)
        assert metrics[f'meter{port}_expected_stderr_mw'] == pytest.approx(.2 / 64)


@pytest.mark.parametrize('payload', [
    {'power_mw': 0}, {'power_mw': 100.1}, {'power_mw': float('nan')},
    {'wavelength_nm': 399}, {'wavelength_nm': 1601},
    {'phase_rad': 4 * math.pi + .01}, {'phase_rad': -4 * math.pi - .01},
    {'path_difference_um': 101}, {'path_difference_um': -101},
    {'splitter1': -.01}, {'splitter2': 1.01},
    {'upper_transmission': -.01}, {'lower_transmission': 1.01},
    {'meter_noise_mw': -.01}, {'meter_noise_mw': 1.01},
    {'shots': 15}, {'shots': 4097}, {'points': 50}, {'points': 722},
    {'seed': -1}, {'seed': 2**31}, {'unknown_setting': 1},
    {'bench_components': []}, {'bench_components': ['source']},
    {'bench_components': ['source', 'bs1', 'upper_mirror', 'lower_mirror', 'phase', 'bs2', 'detector0', 'detector0']},
    {'bench_components': ['source', 'bs1', 'upper_mirror', 'lower_mirror', 'phase', 'bs2', 'detector0', 'unknown']},
])
def test_invalid_photonics_inputs_are_rejected_before_simulation(payload):
    from backend.photonics import PhotonicsRequest

    with pytest.raises(ValidationError):
        PhotonicsRequest(**payload)


def test_run_revalidates_a_request_modified_without_model_validation():
    from backend.photonics import PhotonicsRequest, run_photonics

    config = PhotonicsRequest().model_copy(update={'bench_components': ['source']})
    with pytest.raises(ValidationError):
        run_photonics(config)


def test_result_is_json_compatible_and_identifies_classical_meter_sampling():
    result = simulate()
    json.dumps(result, allow_nan=False)
    assert result['kind'] == 'photonics'
    assert result['qubits'] == 0
    assert result['shots'] == 256
    assert result['seed'] == 42
    assert result['runtime_s'] >= 0
    assert result['versions']['numpy'] == np.__version__
    assert result['backend']
    assert result['model']
    assert result['assumptions']
    assert result['limitations']
    assert len(result['series']) == 181
