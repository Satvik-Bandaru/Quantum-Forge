"""Identity, commutation and relabelling checked on BOTH implementations."""

from itertools import permutations

import numpy as np
import pytest

from .helpers import (
    METAMORPHIC_GENERATOR_SEED, assert_same_state, production_amplitudes, random_gates,
)

pytestmark = pytest.mark.reference


def base_gates(qubits):
    gates = random_gates(np.random.default_rng(METAMORPHIC_GENERATOR_SEED+qubits), qubits, 16)
    return gates[:-qubits] + [
        {'name': 'CNOT', 'target': 0, 'control': qubits-1},
        {'name': 'CP', 'target': qubits-1, 'control': 1, 'angle': .413},
        {'name': 'CCX', 'target': 1, 'control': 0, 'control2': qubits-1},
    ] + gates[-qubits:]


def check_transformation(qubits, original, transformed, output_mapping=None):
    from backend.reference.statevector import simulate_statevector

    reference_before = simulate_statevector(qubits, original)
    production_before = production_amplitudes(qubits, original)
    reference_after = simulate_statevector(qubits, transformed)
    production_after = production_amplitudes(qubits, transformed)
    assert_same_state(reference_before, production_before)
    assert_same_state(reference_after, production_after)
    if output_mapping is not None:
        reference_before = permute_outputs(reference_before, output_mapping)
        production_before = permute_outputs(production_before, output_mapping)
    assert_same_state(reference_after, reference_before)
    assert_same_state(production_after, production_before)


@pytest.mark.parametrize('pair', [('H', 'H'), ('X', 'X'), ('S', 'SDG'), ('T', 'TDG')])
@pytest.mark.parametrize('position', ['start', 'middle', 'end'])
def test_identity_insertions_preserve_reference_and_production(pair, position):
    gates = base_gates(4)
    unitary_end = len(gates)-4
    location = {'start': 0, 'middle': unitary_end//2, 'end': unitary_end}[position]
    inserted = [{'name': name, 'target': 2} for name in pair]
    check_transformation(4, gates, gates[:location]+inserted+gates[location:])


@pytest.mark.parametrize('disjoint', [
    [{'name': 'RX', 'target': 0, 'angle': -.73}, {'name': 'RZ', 'target': 1, 'angle': .29}],
    [{'name': 'CNOT', 'target': 2, 'control': 0},
     {'name': 'CP', 'target': 1, 'control': 3, 'angle': -1.32}],
    [{'name': 'SWAP', 'target': 0, 'control': 2}, {'name': 'H', 'target': 3}],
    [{'name': 'CCX', 'target': 1, 'control': 0, 'control2': 2},
     {'name': 'P', 'target': 3, 'angle': .481}],
])
def test_disjoint_gates_commute_in_reference_and_production(disjoint):
    gates = base_gates(4)
    location = (len(gates)-4)//2
    first = gates[:location]+disjoint+gates[location:]
    second = gates[:location]+list(reversed(disjoint))+gates[location:]
    check_transformation(4, first, second)


def relabel_gates(gates, mapping):
    return [{key: mapping[value] if key in ('target', 'control', 'control2') else value
             for key, value in gate.items()} for gate in gates]


def permute_outputs(state, mapping):
    """Explicit q0-leftmost bit permutation, independent of tensor kernels."""
    qubits = len(mapping)
    permuted = np.empty_like(state)
    for old_index, amplitude in enumerate(state):
        old_bits = format(old_index, f'0{qubits}b')
        new_bits = ['0'] * qubits
        for old_wire, new_wire in enumerate(mapping):
            new_bits[new_wire] = old_bits[old_wire]
        permuted[int(''.join(new_bits), 2)] = amplitude
    return permuted


@pytest.mark.parametrize('mapping', [
    *list(permutations(range(3))), (2, 3, 1, 0), (3, 0, 4, 1, 2),
])
def test_full_qubit_relabelling_permutates_both_outputs(mapping):
    qubits = len(mapping)
    gates = base_gates(qubits)
    check_transformation(qubits, gates, relabel_gates(gates, mapping), mapping)
