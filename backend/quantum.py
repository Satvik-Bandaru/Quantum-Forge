"""Shared Qiskit execution and q0-first state inspection."""
import time
import numpy as np
from .models import CircuitRequest


def circuit_from_config(config: CircuitRequest):
    from qiskit import QuantumCircuit
    qc=QuantumCircuit(config.qubits)
    for gate in config.gates:
        if gate.name=='M': continue
        if gate.name in ('CNOT','CZ','SWAP'):
            getattr(qc,{'CNOT':'cx','CZ':'cz','SWAP':'swap'}[gate.name])(gate.control,gate.target)
        elif gate.name=='CP': qc.cp(gate.angle,gate.control,gate.target)
        elif gate.name=='CCX': qc.ccx(gate.control,gate.control2,gate.target)
        elif gate.name in ('RX','RY','RZ','P'):
            getattr(qc,gate.name.lower())(gate.angle,gate.target)
        else: getattr(qc,gate.name.lower())(gate.target)
    return qc


def inspect_state(state):
    from qiskit.quantum_info import partial_trace,Pauli,entropy,purity
    n=state.num_qubits
    amplitudes=np.asarray(state.reverse_qargs().data)
    registers=[]
    for q in range(n):
        rho=partial_trace(state,[i for i in range(n) if i!=q])
        bloch=[float(np.real(rho.expectation_value(Pauli(axis)))) for axis in ('X','Y','Z')]
        registers.append({'qubit':q,'p1':float(np.real(rho.data[1,1])),
                          'bloch':bloch,'purity':float(np.real(purity(rho))),
                          'entropy':max(0,float(entropy(rho,base=2)))})
    return {'probabilities':(np.abs(amplitudes)**2).tolist(),
            'amplitudes':[[float(a.real),float(a.imag)] for a in amplitudes],
            'bloch':[r['bloch'] for r in registers],'registers':registers,
            'norm':float(np.sum(np.abs(amplitudes)**2))}


BASIS=['h','x','y','z','s','sdg','t','tdg','rx','ry','rz','p','cx','cz','cp','swap','ccx']

def export_qasm(qc):
    from qiskit import transpile,qasm2
    native=transpile(qc,basis_gates=BASIS,optimization_level=0)
    measured=native.copy();measured.measure_all()
    # Canonical register name c makes this export readable by the bounded machine compiler.
    return qasm2.dumps(measured).replace('meas[','c[').replace('-> meas','-> c').replace('barrier '+','.join(f'q[{i}]' for i in range(qc.num_qubits))+';','')


def execute_circuit(qc,shots=1024,seed=42,readout_error=0,gate_error=0):
    from qiskit import transpile
    from qiskit.quantum_info import Statevector
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel,ReadoutError,depolarizing_error
    from .science import versions
    start=time.perf_counter()
    state=Statevector.from_instruction(qc)
    details=inspect_state(state)
    noise=NoiseModel()
    if readout_error:
        noise.add_all_qubit_readout_error(ReadoutError([[1-readout_error,readout_error],[readout_error,1-readout_error]]))
    if gate_error:
        for arity,names in ((1,['h','x','y','z','s','sdg','t','tdg','rx','ry','rz','p']),(2,['cx','cz','cp','swap']),(3,['ccx'])):
            noise.add_all_qubit_quantum_error(depolarizing_error(gate_error,arity),names)
    backend=AerSimulator(method='statevector',noise_model=noise,max_parallel_threads=1,max_memory_mb=256)
    measured=qc.copy();measured.measure_all()
    compiled=transpile(measured,basis_gates=BASIS,optimization_level=0)
    raw=backend.run(compiled,shots=shots,seed_simulator=seed).result().get_counts()
    counts={k.replace(' ','')[::-1]:int(v) for k,v in raw.items()}
    return {'kind':'circuit','backend':'Qiskit Aer / local CPU simulation','versions':versions(),**details,
            'qubits':qc.num_qubits,'depth':qc.depth(),'gate_count':qc.size(),'shots':shots,'seed':seed,
            'runtime_s':time.perf_counter()-start,'counts':counts,'qasm':export_qasm(qc),
            'circuit_text':str(qc.draw(output='text',fold=100)),
            'limitations':['Snapshots, statevectors, reduced states and exact metrics describe the ideal pre-measurement circuit. Only final sampled histograms include configured noise.',
                           'All qubits are read out at the end. Snapshot stepping does not simulate intermediate measurement collapse.',
                           'This is a virtual quantum computer simulated on a classical CPU, not a physical QPU. Simulator runtime cannot establish quantum advantage.']}
