"""Fixed-seed comparisons against the actual production quantum boundary.

QF_REFERENCE_REPORT may name a NEW JSON file in an existing directory. Normal
test runs have no report writes; an existing report is never overwritten.
"""

import json
import os
from pathlib import Path
from time import perf_counter
from typing import get_args

import numpy as np
import pytest

from .helpers import (
    AER_SEED_BASE, ALL_GATES, AMPLITUDE_ATOL, FAMILY_ALPHA, IDEAL_CASES,
    IDEAL_GENERATOR_SEED, NOISY_CASES, NOISY_GENERATOR_SEED, SHOTS,
    assert_same_state, holm_adjusted, ideal_cases, noisy_cases,
    pearson_comparison, production_amplitudes,
)

pytestmark = pytest.mark.reference


@pytest.fixture(scope='module')
def differential_report():
    report = {'ideal_generator_seed': IDEAL_GENERATOR_SEED,
              'noisy_generator_seed': NOISY_GENERATOR_SEED,
              'aer_seed_base': AER_SEED_BASE, 'shots': SHOTS,
              'family_alpha': FAMILY_ALPHA, 'amplitude_atol': AMPLITUDE_ATOL,
              'amplitude_rtol': 0, 'ideal': [], 'noisy': []}
    filename = os.environ.get('QF_REFERENCE_REPORT')
    path = Path(filename).resolve() if filename else None
    if path is not None:
        assert path.parent.is_dir(), 'Report parent directory must already exist'
        assert not path.exists(), 'Reference evidence must use a new report path'
    yield report
    if path is not None:
        with path.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2, allow_nan=False)
            stream.write('\n')


def test_300_seeded_circuits_match_production_amplitudes(differential_report):
    from backend.models import Gate
    from backend.reference.statevector import simulate_statevector

    started = perf_counter()
    cases = list(ideal_cases())
    assert len(cases) == IDEAL_CASES == 300
    assert {case['qubits'] for case in cases} == set(range(1, 9))
    generated_gates = [gate for case in cases for gate in case['gates']]
    assert {gate['name'] for gate in generated_gates} == ALL_GATES
    assert ALL_GATES == set(get_args(Gate.model_fields['name'].annotation))
    controlled = [gate for gate in generated_gates if 'control' in gate]
    assert {gate['control'] < gate['target'] for gate in controlled} == {True, False}
    ccx = [gate for gate in controlled if gate['name'] == 'CCX']
    assert {gate['control'] < gate['control2'] for gate in ccx} == {True, False}
    differential_report['ideal_gate_coverage'] = {
        name: sum(gate['name'] == name for gate in generated_gates)
        for name in sorted(ALL_GATES)}
    for case in cases:
        before = perf_counter()
        actual = production_amplitudes(case['qubits'], case['gates'])
        expected = simulate_statevector(case['qubits'], case['gates'])
        try:
            error = assert_same_state(actual, expected)
        except AssertionError as exc:
            raise AssertionError(f'Ideal case {case["case"]}: {case}') from exc
        differential_report['ideal'].append({
            **case, 'max_amplitude_error': error,
            'production_norm_deviation': float(abs(np.linalg.norm(actual)-1)),
            'reference_norm_deviation': float(abs(np.linalg.norm(expected)-1)),
            'elapsed_s': perf_counter()-before})
    differential_report['ideal_max_amplitude_error'] = max(
        case['max_amplitude_error'] for case in differential_report['ideal'])
    differential_report['ideal_elapsed_s'] = perf_counter()-started
    differential_report['ideal_max_norm_deviation'] = max(
        max(case['production_norm_deviation'], case['reference_norm_deviation'])
        for case in differential_report['ideal'])


def test_30_noisy_circuits_match_aer_with_holm_family(differential_report):
    from backend.models import CircuitRequest
    from backend.quantum import circuit_from_config, execute_circuit
    from backend.reference.density import simulate_probabilities

    started = perf_counter()
    cases = list(noisy_cases())
    assert len(cases) == NOISY_CASES == 30
    results = differential_report['noisy']
    for case in cases:
        before = perf_counter()
        config = CircuitRequest(**{key: value for key, value in case.items() if key != 'case'})
        expected = simulate_probabilities(config.qubits, case['gates'],
                                          gate_error=config.gate_error,
                                          readout_error=config.readout_error)
        reference_elapsed = perf_counter()-before
        actual = execute_circuit(circuit_from_config(config), shots=config.shots,
                                 seed=config.seed, readout_error=config.readout_error,
                                 gate_error=config.gate_error)
        comparison = pearson_comparison(expected, actual['counts'], config.qubits, config.shots)
        results.append({**case, **comparison, 'reference_elapsed_s': reference_elapsed,
                        'probability_normalization_deviation': float(abs(np.sum(expected)-1)),
                        'production_elapsed_s': actual['runtime_s'],
                        'elapsed_s': perf_counter()-before})
    adjusted = holm_adjusted([result['pvalue'] for result in results])
    for result, pvalue in zip(results, adjusted):
        result['holm_adjusted_pvalue'] = float(pvalue)
        result['rejected'] = bool(pvalue <= FAMILY_ALPHA)
    differential_report['noisy_elapsed_s'] = perf_counter()-started
    rejected = [result for result in results if result['rejected']]
    assert not rejected, 'Fixed-seed noisy scientific mismatch: ' + json.dumps(rejected)


@pytest.mark.parametrize(('pvalues', 'expected', 'rejected'), [
    ([.0001, .4, .9], [.0003, .8, .9], [True, False, False]),
    ([.9, .0004, .0001], [.9, .0008, .0003], [False, True, True]),
    ([.0004, .00045, .00046], [.0012, .0012, .0012], [False, False, False]),
    ([0, 1, .0005], [0, 1, .001], [True, False, True]),
])
def test_holm_step_down_hand_computed_examples(pvalues, expected, rejected):
    adjusted = holm_adjusted(pvalues)
    np.testing.assert_allclose(adjusted, expected, atol=1e-15, rtol=0)
    assert (adjusted <= FAMILY_ALPHA).tolist() == rejected


def test_global_phase_comparator_accepts_phase_but_rejects_relative_phase():
    state = np.array([1, 1j, -2, .3-.7j], dtype=complex)
    state /= np.linalg.norm(state)
    assert_same_state(np.exp(.73j)*state, state)
    wrong = state.copy()
    wrong[1] *= -1
    np.testing.assert_allclose(np.abs(wrong)**2, np.abs(state)**2, atol=1e-15, rtol=0)
    with pytest.raises(AssertionError):
        assert_same_state(wrong, state)


def test_mutation_guard_detects_wrong_reference_ry_sign():
    from backend.reference.statevector import simulate_statevector

    actual = production_amplitudes(1, [{'name': 'RY', 'target': 0, 'angle': .713}])
    mutated = simulate_statevector(1, [{'name': 'RY', 'target': 0, 'angle': -.713}])
    # This mutation has exactly the same probabilities, so probability-only
    # comparisons cannot pass this guard.
    np.testing.assert_allclose(np.abs(actual)**2, np.abs(mutated)**2, atol=1e-14, rtol=0)
    with pytest.raises(AssertionError):
        assert_same_state(actual, mutated)


def test_mutation_guard_detects_changed_noise_oracle():
    from backend.reference.density import simulate_probabilities

    # Exact known counts isolate the statistical checker from sampling luck.
    # X|0> with independent 0.2 readout flips yields (.2, .8); changing the
    # reference readout to 0.3 must be decisively rejected.
    gates = [{'name': 'X', 'target': 0}]
    correct = simulate_probabilities(1, gates, readout_error=.2)
    mutated = simulate_probabilities(1, gates, readout_error=.3)
    np.testing.assert_allclose(correct, [.2, .8], atol=1e-14, rtol=0)
    comparison = pearson_comparison(mutated, {'0': 1600, '1': 6400}, 1, 8000)
    assert holm_adjusted([comparison['pvalue']])[0] <= FAMILY_ALPHA
