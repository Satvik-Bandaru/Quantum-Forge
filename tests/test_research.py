"""Independent analytic references for bounded QEC and one-photon experiments."""
import json
import math

import numpy as np
import pytest
from pydantic import ValidationError


def run(**kwargs):
    from backend.research import ResearchRequest, run_research
    return run_research(ResearchRequest(**kwargs))


def density(result, key='final_density_matrix'):
    encoded = np.asarray(result[key])
    return encoded[..., 0] + 1j * encoded[..., 1]


@pytest.mark.parametrize('p,logical', [(0, 0), (.1, .028), (.25, .15625), (.5, .5), (.75, .84375), (1, 1)])
def test_repetition_density_matches_independent_majority_failure_polynomial(p, logical):
    result = run(bit_flip_probability=p)
    np.testing.assert_allclose(density(result), np.diag([1-logical, logical]), atol=2e-12)
    assert result['metrics']['logical_error_probability'] == pytest.approx(logical)
    assert result['metrics']['analytic_logical_error_probability'] == pytest.approx(logical)
    assert result['metrics']['corrected_fidelity'] == pytest.approx(1-logical)
    assert result['metrics']['uncorrected_fidelity'] == pytest.approx(1-p)
    assert result['checks']['passed']


def test_repetition_preserves_complex_amplitudes_through_encoding_syndrome_and_decoding():
    result = run(bit_flip_probability=.1, theta_rad=math.pi/2, relative_phase_rad=math.pi/2)
    expected = np.array([[.5, -.472j], [.472j, .5]])
    np.testing.assert_allclose(density(result), expected, atol=2e-12)
    encoded = density(result, 'encoded_density_matrix')
    assert encoded.shape == (8, 8)
    assert encoded[0, 7] == pytest.approx(-.5j)
    assert encoded[7, 0] == pytest.approx(.5j)
    assert np.trace(encoded) == pytest.approx(1)
    corrected = np.zeros((8, 8), dtype=complex)
    corrected[np.ix_([0, 7], [0, 7])] = expected
    np.testing.assert_allclose(density(result, 'corrected_density_matrix'), corrected, atol=2e-12)
    assert result['metrics']['corrected_fidelity'] == pytest.approx(.972)
    assert result['metrics']['uncorrected_fidelity'] == pytest.approx(.9)
    assert result['syndrome_probabilities'] == pytest.approx({'00': .73, '01': .09, '10': .09, '11': .09})


@pytest.mark.parametrize('theta,phase', [(.43, -.9), (1.7, 2.2), (math.pi, 0)])
def test_arbitrary_pure_states_follow_the_logical_pauli_channel(theta, phase):
    result = run(bit_flip_probability=.3, theta_rad=theta, relative_phase_rad=phase)
    ket = np.array([math.cos(theta/2), np.exp(1j*phase)*math.sin(theta/2)])
    initial = np.outer(ket, ket.conj())
    expected = .784*initial + .216*initial[::-1, ::-1]
    np.testing.assert_allclose(density(result), expected, atol=2e-12)
    assert result['metrics']['corrected_fidelity'] == pytest.approx(float(np.vdot(ket, expected @ ket).real))


def test_logical_error_rate_is_not_misrepresented_as_infidelity_for_x_eigenstate():
    result = run(theta_rad=math.pi/2, bit_flip_probability=.75)
    assert result['metrics']['logical_error_probability'] == pytest.approx(.84375)
    assert result['metrics']['corrected_fidelity'] == pytest.approx(1)
    assert result['metrics']['purity'] == pytest.approx(1)


def test_qec_patterns_syndromes_and_measurements_are_seeded_joint_trials():
    first = run(bit_flip_probability=.25, shots=8192, seed=19)
    again = run(bit_flip_probability=.25, shots=8192, seed=19)
    different = run(bit_flip_probability=.25, shots=8192, seed=20)
    for key in ['counts', 'pattern_counts', 'syndrome_counts', 'measurement_counts', 'trial_preview']:
        assert first[key] == again[key]
    assert first['pattern_counts'] != different['pattern_counts']
    assert sum(first['counts'].values()) == 8192
    assert sum(first['pattern_counts'].values()) == 8192
    assert sum(first['syndrome_counts'].values()) == 8192
    assert first['measurement_counts']['1'] == first['counts']['logical_X']
    assert abs(first['counts']['logical_X']/8192 - .15625) < .025
    expected = {'000': ('00', False), '001': ('01', False), '010': ('11', False), '100': ('10', False),
                '011': ('10', True), '101': ('11', True), '110': ('01', True), '111': ('00', True)}
    for trial in first['trial_preview']:
        syndrome, logical = expected[trial['error_pattern']]
        assert trial['syndrome'] == syndrome
        assert trial['logical_error'] is logical


@pytest.mark.parametrize('p,pattern,logical', [(0, '000', 'logical_I'), (1, '111', 'logical_X')])
def test_qec_deterministic_error_endpoints(p, pattern, logical):
    result = run(bit_flip_probability=p, shots=128)
    assert result['pattern_counts'][pattern] == 128
    assert result['counts'][logical] == 128
    assert result['syndrome_counts']['00'] == 128


@pytest.mark.parametrize('phase,port0,port1', [(0, 0, 1), (math.pi/2, .5, .5), (math.pi, 1, 0), (2*math.pi, 0, 1)])
def test_single_photon_interference_matches_sine_squared_formula(phase, port0, port1):
    result = run(experiment='single_photon_mzi', phase_rad=phase)
    assert result['probabilities'] == pytest.approx({'detector0': port0, 'detector1': port1, 'no_click': 0}, abs=2e-12)
    assert result['metrics']['survival_probability'] == pytest.approx(1)
    assert result['metrics']['purity'] == pytest.approx(1)
    for row in result['series']:
        assert row['detector0_probability'] == pytest.approx(math.sin(row['phase_rad']/2)**2, abs=2e-12)
        assert row['detector1_probability'] == pytest.approx(math.cos(row['phase_rad']/2)**2, abs=2e-12)


def test_photon_loss_vacuum_and_inefficient_detection_remain_distinct():
    result = run(experiment='single_photon_mzi', lower_transmission=.25,
                 detector0_efficiency=.8, detector1_efficiency=.4)
    assert result['probabilities'] == pytest.approx({'detector0': .05, 'detector1': .225, 'no_click': .725})
    assert result['metrics']['optical_loss_probability'] == pytest.approx(.375)
    assert result['metrics']['missed_detection_probability'] == pytest.approx(.35)
    assert result['metrics']['survival_probability'] == pytest.approx(.625)
    assert density(result)[0, 0] == pytest.approx(.375)
    assert density(result)[1, 1] == pytest.approx(.0625)
    assert density(result)[2, 2] == pytest.approx(.5625)
    assert result['metrics']['visibility0'] == pytest.approx(.8)
    assert result['metrics']['visibility1'] == pytest.approx(.8)


def test_complex_single_photon_density_has_coherence_and_no_vacuum_coherence():
    result = run(experiment='single_photon_mzi', phase_rad=math.pi/2)
    np.testing.assert_allclose(density(result), [[0, 0, 0], [0, .5, .5], [0, .5, .5]], atol=2e-12)


def test_path_dephasing_removes_interference_without_relabeling_power_noise():
    coherent = run(experiment='single_photon_mzi')
    incoherent = run(experiment='single_photon_mzi', path_coherence=0)
    partial = run(experiment='single_photon_mzi', path_coherence=.2)
    assert coherent['probabilities']['detector0'] == pytest.approx(0, abs=2e-12)
    assert incoherent['probabilities'] == pytest.approx({'detector0': .5, 'detector1': .5, 'no_click': 0})
    assert incoherent['metrics']['purity'] == pytest.approx(.5)
    assert partial['probabilities']['detector0'] == pytest.approx(.4)
    assert partial['metrics']['visibility0'] == pytest.approx(.2)
    for row in incoherent['series']:
        assert row['detector0_probability'] == pytest.approx(.5)


@pytest.mark.parametrize('first,second,expected', [(1, 1, [1, 0]), (1, 0, [0, 1]), (0, 1, [0, 1]), (0, 0, [1, 0])])
def test_splitter_endpoints_route_one_photon_deterministically(first, second, expected):
    result = run(experiment='single_photon_mzi', splitter1=first, splitter2=second)
    assert [result['probabilities']['detector0'], result['probabilities']['detector1']] == pytest.approx(expected)
    assert result['counts'][f'detector{expected.index(1)}'] == 1024


@pytest.mark.parametrize('first,second,phase,port0', [(.25, .75, 0, 0), (.25, .75, math.pi, .75), (.25, .25, 0, .25)])
def test_unbalanced_splitters_interfere_with_amplitude_not_probability_addition(first, second, phase, port0):
    result = run(experiment='single_photon_mzi', splitter1=first, splitter2=second, phase_rad=phase)
    assert result['probabilities']['detector0'] == pytest.approx(port0, abs=2e-12)
    assert result['probabilities']['detector1'] == pytest.approx(1-port0, abs=2e-12)


@pytest.mark.parametrize('options,optical_loss', [
    ({'upper_transmission': 0, 'lower_transmission': 0}, 1),
    ({'detector0_efficiency': 0, 'detector1_efficiency': 0}, 0),
])
def test_all_lost_or_undetected_photons_produce_only_no_click(options, optical_loss):
    result = run(experiment='single_photon_mzi', shots=128, **options)
    assert result['counts'] == {'detector0': 0, 'detector1': 0, 'no_click': 128}
    assert result['metrics']['optical_loss_probability'] == pytest.approx(optical_loss)
    assert result['metrics']['visibility0'] is None
    assert result['metrics']['visibility1'] is None


def test_photon_counts_are_seeded_exclusive_trials_with_conserved_probability():
    options = dict(experiment='single_photon_mzi', phase_rad=1.1, upper_transmission=.4,
                   lower_transmission=.8, detector0_efficiency=.7, detector1_efficiency=.2, shots=8192)
    result = run(**options)
    assert result['counts'] == run(**options)['counts']
    assert result['counts'] != run(seed=43, **options)['counts']
    assert sum(result['counts'].values()) == 8192
    assert sum(result['probabilities'].values()) == pytest.approx(1)
    assert result['metrics']['double_click_probability'] == 0
    for key, probability in result['probabilities'].items():
        assert abs(result['counts'][key]/8192-probability) < .03


@pytest.mark.parametrize('experiment', ['repetition_code', 'single_photon_mzi'])
def test_density_matrices_are_physical_and_outputs_are_json_safe(experiment):
    result = run(experiment=experiment, bit_flip_probability=.31, theta_rad=1.2, relative_phase_rad=-.7,
                 phase_rad=-1.3, splitter1=.13, splitter2=.84, upper_transmission=.51,
                 lower_transmission=.91, path_coherence=.42)
    rho = density(result)
    np.testing.assert_allclose(rho, rho.conj().T, atol=2e-12)
    assert np.trace(rho) == pytest.approx(1)
    assert np.linalg.eigvalsh(rho).min() >= -2e-12
    assert result['checks']['passed']
    assert result['kind'] == 'research'
    assert result['experiment'] == experiment
    assert result['qubits'] == (3 if experiment == 'repetition_code' else 0)
    assert result['versions']['numpy']
    assert result['runtime_s'] >= 0
    json.dumps(result, allow_nan=False)


@pytest.mark.parametrize('field,value', [
    ('shots', 127), ('shots', 8193), ('shots', 1.5), ('seed', -1), ('seed', 2**31),
    ('bit_flip_probability', -.01), ('bit_flip_probability', 1.01), ('theta_rad', -1),
    ('theta_rad', 4), ('relative_phase_rad', 7), ('splitter1', 1.01), ('splitter2', -.1),
    ('phase_rad', 13), ('upper_transmission', -.1), ('lower_transmission', 1.1),
    ('detector0_efficiency', -.1), ('detector1_efficiency', 1.1), ('path_coherence', 1.1),
    ('phase_rad', float('nan')), ('theta_rad', float('inf')), ('experiment', 'unbounded_fock'),
    ('unknown', 0),
])
def test_invalid_or_unbounded_requests_are_rejected(field, value):
    from backend.research import ResearchRequest
    with pytest.raises(ValidationError):
        ResearchRequest(**{field: value})


def test_execution_revalidates_model_copy_updates_before_numerical_work():
    from backend.research import ResearchRequest, run_research
    with pytest.raises(ValidationError):
        run_research(ResearchRequest().model_copy(update={'shots': 10**9}))
