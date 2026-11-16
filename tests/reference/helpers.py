"""Test-only generators and comparisons; never imported by either simulator."""

import numpy as np

IDEAL_GENERATOR_SEED = 2026111501
NOISY_GENERATOR_SEED = 2026111502
METAMORPHIC_GENERATOR_SEED = 2026111503
AER_SEED_BASE = 1618033
IDEAL_CASES = 300
NOISY_CASES = 30
SHOTS = 8192
FAMILY_ALPHA = 0.001
AMPLITUDE_ATOL = 1e-10

SINGLE_GATES = ('X', 'Y', 'Z', 'H', 'S', 'SDG', 'T', 'TDG', 'P', 'RX', 'RY', 'RZ')
DOUBLE_GATES = ('CNOT', 'CZ', 'CP', 'SWAP')
ANGLED_GATES = ('P', 'RX', 'RY', 'RZ', 'CP')
ALL_GATES = frozenset((*SINGLE_GATES, *DOUBLE_GATES, 'CCX', 'M'))


def random_gates(rng, qubits, extra_gates):
    """Prepare asymmetric complex states, then sample gates without replacement wires.

    Seeds, size schedules, angle choices, and noise schedules were selected before
    any differential result. Terminal M gates exercise the production no-op rule.
    """
    gates = []
    for target in range(qubits):
        gates.extend([
            {'name': 'H', 'target': target},
            {'name': 'RY', 'target': target, 'angle': float(rng.uniform(-np.pi, np.pi))},
            {'name': 'P', 'target': target, 'angle': float(rng.uniform(-2*np.pi, 2*np.pi))},
        ])
    available = list(SINGLE_GATES)
    if qubits >= 2:
        available.extend(DOUBLE_GATES)
    if qubits >= 3:
        available.append('CCX')
    special_angles = np.pi * np.array([-100, -2, -1, -.5, 0, .5, 1, 2, 100])
    for _ in range(extra_gates):
        name = str(rng.choice(available))
        arity = 3 if name == 'CCX' else 2 if name in DOUBLE_GATES else 1
        wires = rng.choice(qubits, size=arity, replace=False).tolist()
        gate = {'name': name, 'target': wires[0]}
        if arity >= 2:
            gate['control'] = wires[1]
        if arity == 3:
            gate['control2'] = wires[2]
        if name in ANGLED_GATES:
            gate['angle'] = float(rng.choice(special_angles) if rng.random() < .25
                                  else rng.uniform(-2*np.pi, 2*np.pi))
        gates.append(gate)
    gates.extend({'name': 'M', 'target': target} for target in range(qubits))
    return gates


def ideal_cases():
    rng = np.random.default_rng(IDEAL_GENERATOR_SEED)
    for index in range(IDEAL_CASES):
        qubits = 1 + index % 8
        yield {'case': index, 'qubits': qubits,
               'gates': random_gates(rng, qubits, int(rng.integers(8, 33)))}


def noisy_cases():
    rng = np.random.default_rng(NOISY_GENERATOR_SEED)
    for index in range(NOISY_CASES):
        qubits = 2 + index % 3
        yield {'case': index, 'qubits': qubits,
               'gates': random_gates(rng, qubits, int(rng.integers(8, 17))),
               'shots': SHOTS, 'seed': AER_SEED_BASE + index,
               'gate_error': .06 + .02 * (index % 4),
               'readout_error': .20 + .02 * (index % 3)}


def production_amplitudes(qubits, gates):
    """Use the real request -> circuit -> Qiskit -> inspect_state path."""
    from backend.models import CircuitRequest
    from backend.quantum import circuit_from_config, inspect_state
    from qiskit.quantum_info import Statevector

    request = CircuitRequest(qubits=qubits, gates=gates)
    result = inspect_state(Statevector.from_instruction(circuit_from_config(request)))
    return np.array([complex(real, imag) for real, imag in result['amplitudes']])


def phase_aligned_error(actual, expected):
    actual, expected = np.asarray(actual), np.asarray(expected)
    assert actual.shape == expected.shape
    assert np.isfinite(actual).all() and np.isfinite(expected).all()
    np.testing.assert_allclose(np.linalg.norm(actual), 1, atol=AMPLITUDE_ATOL, rtol=0)
    np.testing.assert_allclose(np.linalg.norm(expected), 1, atol=AMPLITUDE_ATOL, rtol=0)
    pivot = int(np.argmax(np.abs(expected)))
    assert abs(actual[pivot]) > 0, 'Reference pivot amplitude disappeared'
    phase = actual[pivot] / expected[pivot]
    phase /= abs(phase)
    return actual / phase - expected


def assert_same_state(actual, expected):
    difference = phase_aligned_error(actual, expected)
    np.testing.assert_allclose(difference, 0, atol=AMPLITUDE_ATOL, rtol=0)
    return float(np.max(np.abs(difference)))


def holm_adjusted(pvalues):
    """Holm step-down adjusted p-values, restored to the input order."""
    pvalues = np.asarray(pvalues, dtype=float)
    assert pvalues.ndim == 1 and pvalues.size
    assert np.isfinite(pvalues).all() and ((0 <= pvalues) & (pvalues <= 1)).all()
    order = np.argsort(pvalues, kind='stable')
    adjusted = np.empty_like(pvalues)
    adjusted[order] = np.minimum(1, np.maximum.accumulate(
        (len(pvalues) - np.arange(len(pvalues))) * pvalues[order]))
    return adjusted


def pearson_comparison(probabilities, counts, qubits, shots):
    """All 2**n bins, no fitting/pooling; fail if chi-square assumptions fail."""
    from scipy.stats import chisquare

    probabilities = np.asarray(probabilities, dtype=float)
    assert probabilities.shape == (2**qubits,)
    assert np.isfinite(probabilities).all() and (probabilities >= 0).all()
    np.testing.assert_allclose(probabilities.sum(), 1, atol=1e-12, rtol=0)
    assert set(counts).issubset({format(i, f'0{qubits}b') for i in range(2**qubits)})
    observed = np.array([counts.get(format(i, f'0{qubits}b'), 0)
                         for i in range(2**qubits)], dtype=int)
    expected = shots * probabilities
    assert observed.sum() == shots
    assert np.all(expected >= 5), f'Expected count below 5: {expected}'
    assert np.all(observed >= 5), f'Observed count below 5: {observed}'
    statistic, pvalue = chisquare(observed, expected, ddof=0)
    return {'statistic': float(statistic), 'pvalue': float(pvalue),
            'degrees_of_freedom': len(expected)-1,
            'min_expected_count': float(expected.min()),
            'min_observed_count': int(observed.min()),
            'probabilities': probabilities.tolist(),
            'expected_counts': expected.tolist(), 'observed_counts': observed.tolist()}
