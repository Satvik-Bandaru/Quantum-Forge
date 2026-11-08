"""Independent small-state references protect QUBO signs, scaling and bit order."""
import itertools
import json
import math
from types import SimpleNamespace

import numpy as np
import pytest
from pydantic import ValidationError


def qubo_module():
    # Keep the initial red test an assertion describing the absent feature.
    import importlib.util
    assert importlib.util.find_spec('backend.qubo') is not None, 'Generic QUBO engine is missing'
    from backend import qubo
    return qubo


def reference_energy(matrix, offset, bits):
    return offset + sum(matrix[i][i] * bits[i] for i in range(len(bits))) + sum(
        matrix[i][j] * bits[i] * bits[j]
        for i in range(len(bits)) for j in range(i + 1, len(bits))
    )


def test_upper_triangular_qubo_has_hand_derived_q0_first_energies():
    engine = qubo_module()
    config = engine.QuboRequest(matrix=[[-3, 4], [0, -2]], offset=1)
    problem = engine.build_qubo(config)
    assert problem['states'].tolist() == [[0, 0], [0, 1], [1, 0], [1, 1]]
    assert problem['energy'].tolist() == [1, -1, -2, 0]


def test_ising_mapping_matches_independent_binary_energy_for_every_state():
    engine = qubo_module()
    matrix = [[-3, 4, -1.5], [0, 2, 6], [0, 0, -5]]
    mapped = engine.qubo_to_ising(matrix, 7)
    assert mapped['h'] == pytest.approx([.875, -3.5, 1.375])
    assert mapped['J'] == [[0, 1, -.375], [0, 0, 1.5], [0, 0, 0]]
    assert mapped['offset'] == pytest.approx(6.125)
    for bits in itertools.product((0, 1), repeat=3):
        z = [1 - 2 * bit for bit in bits]
        spin_energy = mapped['offset'] + np.dot(mapped['h'], z) + sum(
            mapped['J'][i][j] * z[i] * z[j] for i in range(3) for j in range(i + 1, 3)
        )
        assert spin_energy == pytest.approx(reference_energy(matrix, 7, bits))


@pytest.mark.parametrize('payload', [
    {'matrix': [[0]]}, {'matrix': [[0] * 9 for _ in range(9)]},
    {'matrix': [[1, 2], [0]]}, {'matrix': [[1, 2], [1, 3]]},
    {'matrix': [[101, 0], [0, 0]]}, {'matrix': [[0, -100.01], [0, 0]]},
    {'matrix': [[float('nan'), 0], [0, 0]]}, {'matrix': [[0, float('inf')], [0, 0]]},
    {'offset': float('-inf')}, {'offset': 1001}, {'layers': 0}, {'layers': 4},
    {'iterations': 3}, {'layers': 3, 'iterations': 7}, {'iterations': 81},
    {'shots': 127}, {'shots': 4097}, {'seed': -1}, {'seed': 2**31},
    {'script': 'print(1)'}, {'constraints': []}, {'matrix': [[True, 0], [0, 0]]},
    {'layers': True}, {'shots': '512'}, {'matrix': [['1', 0], [0, 0]]},
])
def test_invalid_instances_fail_before_any_solver_allocation(payload):
    engine = qubo_module()
    with pytest.raises(ValidationError):
        engine.QuboRequest(**({'matrix': [[0, 0], [0, 0]]} | payload))


def test_bounds_and_defaults_are_usable_without_extra_fields():
    engine = qubo_module()
    config = engine.QuboRequest(matrix=[[0, -100], [0, 100]])
    assert (config.layers, config.iterations, config.shots, config.seed, config.offset) == (1, 35, 512, 42, 0)
    for config in [
        engine.QuboRequest(matrix=[[0] * 8 for _ in range(8)], layers=3, iterations=8,
                           shots=4096, seed=2**31 - 1, offset=-1000),
        engine.QuboRequest(matrix=[[0, 0], [0, 0]], layers=1, iterations=4,
                           shots=128, seed=0, offset=1000),
    ]:
        assert len(config.matrix) in (2, 8)


def test_fixed_qaoa_angles_prepare_the_analytically_known_single_bit_minimum():
    engine = qubo_module()
    config = engine.QuboRequest(matrix=[[-1, 0], [0, 0]])
    probabilities = engine.qaoa_probabilities(config, [math.pi / 2, -math.pi / 4])
    # Cost phase +i on x0=1 followed by RX(-pi/2) prepares x0=1 exactly.
    assert probabilities == pytest.approx([0, 0, .5, .5], abs=1e-10)


def test_qaoa_matches_independent_complex_state_evolution_with_coupling():
    engine = qubo_module()
    matrix = [[-2, 3, .75], [0, 1, -1.25], [0, 0, .5]]
    config = engine.QuboRequest(matrix=matrix, offset=11, layers=2)
    parameters = [.43, -.71, .27, .56]
    # Independently expand E(x); derive norm from explicit Ising coefficients.
    energies = np.array([reference_energy(matrix, 11, bits)
                         for bits in itertools.product((0, 1), repeat=3)])
    scale = max(1, abs(2 / 2 - 3 / 4 - .75 / 4) + abs(-1 / 2 - 3 / 4 + 1.25 / 4)
                + abs(-.5 / 2 - .75 / 4 + 1.25 / 4) + (3 + .75 + 1.25) / 4)
    state = np.ones(8, dtype=complex) / math.sqrt(8)
    for gamma, beta in zip(parameters[:2], parameters[2:]):
        state *= np.exp(-1j * gamma * energies / scale)
        rotation = np.array([[math.cos(beta), -1j * math.sin(beta)],
                             [-1j * math.sin(beta), math.cos(beta)]])
        state = np.kron(np.kron(rotation, rotation), rotation) @ state
    assert engine.qaoa_probabilities(config, parameters) == pytest.approx(abs(state) ** 2, abs=1e-10)
    shifted = engine.QuboRequest(matrix=matrix, offset=-499, layers=2)
    assert engine.qaoa_probabilities(shifted, parameters) == pytest.approx(abs(state) ** 2, abs=1e-10)


def test_solver_battle_reports_actual_sample_minima_and_independent_exact_reference():
    engine = qubo_module()
    matrix = [[-3, 4], [0, -2]]
    result = engine.run_qubo({'matrix': matrix, 'offset': 1, 'iterations': 10, 'shots': 128, 'seed': 7})
    assert result['kind'] == 'qubo'
    assert result['exact_energy'] == -2
    assert result['exact_solutions'] == [[1, 0]]
    assert [row['energy'] for row in result['energy_table']] == [1, -1, -2, 0]
    assert {solver['key'] for solver in result['solvers']} == {'exact', 'greedy', 'local_search', 'annealing', 'qaoa'}
    for solver in result['solvers']:
        assert solver['energy'] == pytest.approx(reference_energy(matrix, 1, solver['solution']))
        assert solver['gap'] == pytest.approx(solver['energy'] + 2)
        assert solver['gap'] >= -1e-10
        assert solver['runtime_s'] >= 0
        assert solver['evaluations'] > 0
        assert solver['bitstring'] == ''.join(map(str, solver['solution']))
    qaoa = next(solver for solver in result['solvers'] if solver['key'] == 'qaoa')
    assert qaoa['evaluations'] == len(qaoa['trace']) <= 10
    assert qaoa['expected_energy'] == pytest.approx(np.dot(qaoa['probabilities'], [1, -1, -2, 0]))
    assert qaoa['expected_gap'] == pytest.approx(qaoa['expected_energy'] + 2)
    assert qaoa['energy'] == min(reference_energy(matrix, 1, list(map(int, bits)))
                                 for bits, count in qaoa['counts'].items() if count)
    for key in ('qaoa', 'annealing'):
        solver = next(row for row in result['solvers'] if row['key'] == key)
        assert sum(solver['counts'].values()) == 128
        assert math.isfinite(solver.get('initialization_s', float('nan')))
        assert solver['initialization_s'] >= 0
    assert sum(qaoa['probabilities']) == pytest.approx(1)
    json.dumps(result, allow_nan=False)


def test_qaoa_timing_separates_initialization_and_work_and_total_includes_metadata(monkeypatch):
    engine = qubo_module()
    elapsed = [0.0]
    # A controlled clock verifies phase boundaries without adding sleeps or
    # replacing real scientific calculations with mocked solver results.
    monkeypatch.setattr(engine, 'time', SimpleNamespace(perf_counter=lambda: elapsed[0]))
    original_circuit = engine._qaoa_circuit
    original_versions = engine.versions

    def construct(config):
        circuit, scale, depth = original_circuit(config)
        elapsed[0] += 5

        def evaluate(parameters):
            result = circuit(parameters)
            elapsed[0] += .25
            return result

        return evaluate, scale, depth

    def record_versions():
        result = original_versions()
        elapsed[0] += 2
        return result

    monkeypatch.setattr(engine, '_qaoa_circuit', construct)
    monkeypatch.setattr(engine, 'versions', record_versions)
    result = engine.run_qubo({'matrix': [[-3, 4], [0, -2]], 'iterations': 4, 'shots': 128})
    qaoa = next(row for row in result['solvers'] if row['key'] == 'qaoa')
    assert qaoa.get('initialization_s') == 5
    assert qaoa['runtime_s'] == .25 * qaoa['evaluations']
    assert result['runtime_s'] == 7 + qaoa['runtime_s']
    assert qaoa['evaluations'] == len(qaoa['trace']) <= 4
    assert sum(qaoa['counts'].values()) == 128


def test_greedy_does_not_silently_receive_the_exact_or_local_search_solution():
    engine = qubo_module()
    # Greedy takes x0 then cannot add x1: -1. Global minimum x1 alone is -3.
    result = engine.run_qubo({'matrix': [[-1, 5], [0, -3]], 'iterations': 4, 'shots': 128})
    greedy = next(row for row in result['solvers'] if row['key'] == 'greedy')
    assert greedy['solution'] == [1, 0]
    assert greedy['energy'] == -1
    assert greedy['gap'] == 2
    assert greedy['evaluations'] == 3


@pytest.mark.filterwarnings('error:All bqm biases are zero')
def test_flat_hamiltonian_preserves_degeneracy_and_finite_values():
    engine = qubo_module()
    result = engine.run_qubo({'matrix': [[0, 0], [0, 0]], 'offset': 3, 'iterations': 4, 'shots': 128})
    assert len(result['exact_solutions']) == 4
    qaoa = next(row for row in result['solvers'] if row['key'] == 'qaoa')
    assert qaoa['probabilities'] == pytest.approx([.25] * 4)
    assert qaoa['expected_energy'] == pytest.approx(3)
    assert all(row['energy'] == 3 and row['gap'] == 0 for row in result['solvers'])
    json.dumps(result, allow_nan=False)


def test_seed_reproduces_sampling_and_search_without_comparing_timings():
    engine = qubo_module()
    config = engine.QuboRequest(matrix=[[-1, 2, -1], [0, -2, 3], [0, 0, .5]],
                                iterations=8, shots=128, seed=19)
    first, second = engine.run_qubo(config), engine.run_qubo(config)
    for a, b in zip(first['solvers'], second['solvers']):
        assert a['solution'] == b['solution']
        assert a.get('counts') == b.get('counts')
        assert a.get('trace') == b.get('trace')
