"""Hand-derived fixtures catch endianness, signs, penalty and feasibility bugs."""
import numpy as np
import pytest
from pydantic import ValidationError
from backend.models import CircuitRequest, OptimizationRequest
from backend.science import run_circuit, run_optimization, build_problem


def test_bell_state_has_only_correlated_outcomes():
    result = run_circuit(CircuitRequest(qubits=2, shots=1024, seed=7, gates=[{'name':'H','target':0}, {'name':'CNOT','target':1,'control':0}]))
    assert result['probabilities'] == pytest.approx([0.5, 0, 0, 0.5])
    assert set(result['counts']) == {'00', '11'}
    assert sum(result['counts'].values()) == 1024
    assert result['bloch'][0] == pytest.approx([0, 0, 0], abs=1e-8)
    assert result['depth'] == 2


def test_display_order_is_q0_first_and_rotations_are_radians():
    result = run_circuit(CircuitRequest(qubits=2, gates=[{'name':'X','target':0}]))
    assert result['probabilities'] == pytest.approx([0, 0, 1, 0])
    result = run_circuit(CircuitRequest(qubits=1, gates=[{'name':'RY','target':0,'angle':np.pi/2}]))
    assert result['bloch'][0] == pytest.approx([1, 0, 0], abs=1e-8)


def test_readout_noise_changes_samples_but_not_ideal_state():
    result = run_circuit(CircuitRequest(qubits=1, shots=4096, readout_error=0.2, seed=3))
    assert result['probabilities'] == [1, 0]
    assert 0.15 < result['counts'].get('1',0)/4096 < 0.25


@pytest.mark.parametrize('payload', [
    {'qubits':13}, {'shots':1000000}, {'qubits':2,'gates':[{'name':'CNOT','target':0,'control':0}]},
    {'qubits':1,'gates':[{'name':'H','target':1}]}, {'gates':[{'name':'BAD','target':0}]},
    {'gates':[{'name':'M','target':0},{'name':'X','target':0}]}, {'gate_error':float('nan')},
])
def test_invalid_circuits_rejected_before_allocating(payload):
    with pytest.raises(ValidationError):
        CircuitRequest(**payload)


def test_triangle_maxcut_exact_and_qaoa_evidence():
    config = OptimizationRequest(problem='maxcut', nodes=3, edges=[[0,1,1],[1,2,1],[0,2,1]], shots=512, iterations=12, seed=12)
    result = run_optimization(config)
    assert result['baseline']['objective'] == 2
    assert result['baseline']['status'] == 'OPTIMAL'
    assert result['exact_optimum'] == 2
    for solver in result['solvers']:
        assert solver['feasible']
        assert solver['objective'] <= 2
        assert 0 <= solver['quality'] <= 1
        assert solver['runtime_s'] >= 0
    quantum = next(s for s in result['solvers'] if s['algorithm'] == 'QAOA')
    assert quantum['qubits'] == 3
    assert sum(quantum['counts'].values()) == 512
    assert abs(sum(quantum['probabilities']) - 1) < 1e-8
    assert quantum['evaluations'] > 0


def test_knapsack_slack_penalty_matches_hand_derived_values():
    config = OptimizationRequest(problem='knapsack', weights=[2,3,4], values=[3,4,5], capacity=5, shots=256, iterations=8)
    problem = build_problem(config)
    # q0,q1,q2 are item decisions; remaining bits are slack, q0 displayed first.
    # 110 + zero slack has value 7, exact weight 5, zero violation.
    assert problem['energy'][int('110000',2)] == -7
    # 111 + zero slack violates by 4: -(3+4+5) + 13*16 = 196.
    assert problem['energy'][int('111000',2)] == 196
    result = run_optimization(config)
    assert result['baseline']['objective'] == 7
    assert result['exact_optimum'] == 7
    assert result['qubits'] == 6
    for solver in result['solvers']:
        if solver['solution'] is not None:
            assert sum(w*x for w,x in zip(config.weights, solver['solution'])) <= 5
            assert solver['feasible']
            assert solver['objective'] <= 7


def test_seed_reproduces_simulated_sampling():
    config = CircuitRequest(qubits=2, shots=400, seed=8, gates=[{'name':'H','target':0}])
    assert run_circuit(config)['counts'] == run_circuit(config)['counts']


@pytest.mark.parametrize('payload', [
    {'problem':'maxcut','nodes':3,'edges':[[0,0,1]]},
    {'problem':'maxcut','nodes':3,'edges':[[0,1,1],[1,0,2]]},
    {'problem':'maxcut','nodes':3,'edges':[[0,4,1]]},
    {'problem':'knapsack','weights':[1,2],'values':[1],'capacity':3},
    {'problem':'knapsack','weights':[1]*8,'values':[1]*8,'capacity':31},
    {'problem':'knapsack','weights':[0],'values':[1],'capacity':3},
])
def test_invalid_optimization_instances_rejected(payload):
    with pytest.raises(ValidationError):
        OptimizationRequest(**payload)


def test_optimizer_budget_must_cover_initial_simplex():
    with pytest.raises(ValidationError):
        OptimizationRequest(layers=4,iterations=5)


def test_qaoa_stays_inside_declared_evaluation_budget():
    config=OptimizationRequest(nodes=3,edges=[[0,1,1],[1,2,1],[0,2,1]],layers=2,iterations=8,shots=128)
    result=run_optimization(config)
    quantum=next(s for s in result['solvers'] if s['algorithm']=='QAOA')
    assert quantum['evaluations']<=8


@pytest.mark.parametrize('gates,expected',[
    ([{'name':'RX','target':0,'angle':np.pi}], [0,0,-1]),
    ([{'name':'H','target':0},{'name':'RZ','target':0,'angle':np.pi/2}], [0,1,0]),
    ([{'name':'H','target':0},{'name':'Z','target':0}], [-1,0,0]),
    ([{'name':'Y','target':0}], [0,0,-1]),
])
def test_gate_rotations_and_phases_on_bloch_sphere(gates,expected):
    result=run_circuit(CircuitRequest(qubits=1,gates=gates))
    assert result['bloch'][0]==pytest.approx(expected,abs=1e-8)


def test_swap_and_controlled_phase_preserve_q0_first_convention():
    swapped=run_circuit(CircuitRequest(qubits=2,gates=[{'name':'X','target':0},{'name':'SWAP','target':1,'control':0}]))
    assert swapped['probabilities']==pytest.approx([0,1,0,0])
    phased=run_circuit(CircuitRequest(qubits=2,gates=[{'name':'H','target':0},{'name':'H','target':1},{'name':'CZ','target':1,'control':0}]))
    np.testing.assert_allclose(phased['amplitudes'],[[.5,0],[.5,0],[.5,0],[-.5,0]],atol=1e-8)


def test_gate_depolarization_affects_histogram():
    result=run_circuit(CircuitRequest(qubits=1,shots=4096,seed=2,gate_error=.15,gates=[{'name':'X','target':0}]))
    assert .04<result['counts'].get('0',0)/4096<.11
    assert result['probabilities']==pytest.approx([0,1])


def test_qaoa_and_annealing_reproduce_counts_for_same_seed():
    config=OptimizationRequest(nodes=3,edges=[[0,1,1],[1,2,1],[0,2,1]],iterations=8,shots=128)
    first=run_optimization(config)
    second=run_optimization(config)
    for a,b in zip(first['solvers'][1:],second['solvers'][1:]):
        assert a['counts']==b['counts']
        assert a['solution']==b['solution']


@pytest.mark.parametrize('seed,expected_seeds',[
    (42,[42,42,43,43,44,44]),
    (2147483647,[2147483647,2147483647,0,0,1,1]),
])
def test_repeated_solvers_keep_valid_reproducible_effective_seeds(seed,expected_seeds):
    config=OptimizationRequest(nodes=2,edges=[[0,1,1]],layers=1,iterations=5,
                               shots=128,repetitions=3,seed=seed)
    first=run_optimization(config)
    second=run_optimization(config)
    assert [solver['seed'] for solver in first['solvers'][1:]]==expected_seeds
    for a,b in zip(first['solvers'][1:],second['solvers'][1:]):
        assert sum(a['counts'].values())==128
        assert a['counts']==b['counts']
        assert a['solution']==b['solution']
