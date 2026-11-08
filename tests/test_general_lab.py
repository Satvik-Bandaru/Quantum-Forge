import math
import numpy as np
import pytest
from pydantic import ValidationError
from backend.machine import MachineRequest, compile_program, run_machine
from backend.experiments import ExperimentRequest, run_experiment


def test_virtual_machine_bell_snapshots_and_entropy():
    result=run_machine(MachineRequest(qubits=2,program='H q0\nCX q0, q1\nMEASURE ALL',shots=256))
    frames=result['snapshots']
    assert frames[0]['probabilities']==[1,0,0,0]
    assert frames[1]['probabilities']==pytest.approx([.5,0,.5,0])
    assert frames[2]['probabilities']==pytest.approx([.5,0,0,.5])
    assert frames[1]['registers'][0]['entropy']==pytest.approx(0,abs=1e-9)
    assert frames[2]['registers'][0]['entropy']==pytest.approx(1)
    assert sum(result['counts'].values())==256
    assert result['statevector_bytes']==64
    assert 'OPENQASM 2.0' in result['qasm']


def test_assembly_understands_pi_and_qasm_subset():
    program='OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\nh q[0];\ncp(pi/2) q[0],q[1];\nmeasure q -> c;'
    config,_=compile_program(program,2)
    assert config.gates[1].name=='CP'
    assert config.gates[1].angle==pytest.approx(math.pi/2)
    result=run_machine(MachineRequest(qubits=2,program='X q0\nSWAP q0,q1'))
    assert result['probabilities']==pytest.approx([0,1,0,0])


@pytest.mark.parametrize('program',[
    'RX __import__("os") q0','RX 2**100000 q0','H q9','CX q0,q0','QREG 12\nH q0',
    'MEASURE ALL\nH q0','H q0\n'*97,'include "secret.inc";', 'RY pi/0 q0', 'qreg q[8];\nh q[0];',
])
def test_machine_rejects_unsafe_or_invalid_programs(program):
    with pytest.raises((ValidationError,ValueError)):
        run_machine(MachineRequest(qubits=2,program=program))


@pytest.mark.parametrize('message',['00','01','10','11'])
def test_superdense_decodes_both_classical_bits(message):
    result=run_experiment(ExperimentRequest(algorithm='superdense',message=message,shots=128))
    assert result['probabilities'][int(message,2)]==pytest.approx(1)
    assert result['metrics']['decoded_message']==message


def test_grover_matches_analytic_success_probability():
    result=run_experiment(ExperimentRequest(algorithm='grover',qubits=3,marked_state='101',iterations=2,shots=256))
    expected=math.sin(5*math.asin(1/math.sqrt(8)))**2
    assert result['probabilities'][5]==pytest.approx(expected)
    assert result['metrics']['success_probability']==pytest.approx(expected)


def test_qft_includes_correct_complex_phases():
    result=run_experiment(ExperimentRequest(algorithm='qft',qubits=3,basis_state=3))
    amps=np.array([complex(*a) for a in result['amplitudes']])
    np.testing.assert_allclose(amps,np.exp(2j*np.pi*3*np.arange(8)/8)/np.sqrt(8),atol=1e-8)
    assert result['metrics']['reference_fidelity']==pytest.approx(1)


def test_qpe_exact_three_bit_phase():
    result=run_experiment(ExperimentRequest(algorithm='qpe',qubits=3,phase=.375))
    assert result['metrics']['estimated_phase']==pytest.approx(.375)
    assert result['probabilities'][int('0111',2)]==pytest.approx(1)


@pytest.mark.parametrize('oracle,expected',[('constant','000'),('balanced','101')])
def test_deutsch_jozsa_detects_oracle_promise(oracle,expected):
    result=run_experiment(ExperimentRequest(algorithm='deutsch_jozsa',qubits=3,oracle=oracle,mask='101'))
    assert result['metrics']['input_register']==expected
    assert result['metrics']['classification']==oracle


def test_teleportation_preserves_arbitrary_qubit_fidelity():
    result=run_experiment(ExperimentRequest(algorithm='teleportation',theta=1.13,phi=-.77))
    assert result['metrics']['receiver_fidelity']==pytest.approx(1)
    assert result['bloch'][2]==pytest.approx([math.sin(1.13)*math.cos(-.77),math.sin(1.13)*math.sin(-.77),math.cos(1.13)])


def test_chsh_exact_correlation_is_tsirelson_bound():
    result=run_experiment(ExperimentRequest(algorithm='chsh',shots=2048))
    assert result['metrics']['ideal_chsh']==pytest.approx(2*math.sqrt(2))
    assert 2.4<result['metrics']['sampled_chsh']<3.1


def test_vqe_energy_respects_independent_exact_ground_energy():
    result=run_experiment(ExperimentRequest(algorithm='vqe',coupling=.7,iterations=80))
    ground=-math.sqrt(4+.7**2)
    assert result['metrics']['exact_ground_energy']==pytest.approx(ground)
    assert ground-1e-8<=result['metrics']['variational_energy']<ground+.1
    assert result['metrics']['evaluations']<=80


def test_interference_and_ghz_are_real_circuits():
    interference=run_experiment(ExperimentRequest(algorithm='interference',phi=math.pi))
    assert interference['probabilities']==pytest.approx([0,1],abs=1e-8)
    ghz=run_experiment(ExperimentRequest(algorithm='ghz',qubits=4))
    assert ghz['probabilities'][0]==pytest.approx(.5)
    assert ghz['probabilities'][15]==pytest.approx(.5)


@pytest.mark.parametrize('payload',[{'algorithm':'grover','qubits':3,'marked_state':'11'}, {'algorithm':'qft','qubits':3,'basis_state':8}, {'algorithm':'qpe','phase':float('nan')}, {'algorithm':'deutsch_jozsa','qubits':3,'oracle':'balanced','mask':'000'}])
def test_experiment_input_bounds(payload):
    with pytest.raises(ValidationError): ExperimentRequest(**payload)


@pytest.mark.parametrize('algorithm',['bell','grover','qft','qpe','deutsch_jozsa','superdense','teleportation','vqe','chsh'])
def test_exported_small_experiment_runs_on_virtual_machine(algorithm):
    from qiskit.quantum_info import state_fidelity,Statevector
    config=ExperimentRequest(algorithm=algorithm,iterations=20 if algorithm=='vqe' else 2,shots=128)
    result=run_experiment(config)
    assert result['machine_program'] is not None
    replay=run_machine(MachineRequest(qubits=result['qubits'],program=result['machine_program'],shots=128))
    a=np.array([complex(*v) for v in result['amplitudes']])
    b=np.array([complex(*v) for v in replay['amplitudes']])
    assert abs(np.vdot(a,b))**2==pytest.approx(1)
