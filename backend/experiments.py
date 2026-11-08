"""Small, functional experiments across quantum information and computation."""
import math
import time
import numpy as np
from pydantic import Field,model_validator
from typing import Literal
from .models import StrictModel,MAX_QUBITS,MAX_SHOTS

Algorithm=Literal['bell','ghz','interference','grover','qft','qpe','deutsch_jozsa','superdense','teleportation','vqe','chsh']

class ExperimentRequest(StrictModel):
    algorithm:Algorithm='grover'
    qubits:int=Field(default=3,ge=2,le=min(6,MAX_QUBITS))
    shots:int=Field(default=1024,ge=128,le=MAX_SHOTS)
    seed:int=Field(default=42,ge=0,le=2**31-1)
    iterations:int=Field(default=2,ge=1,le=150)
    marked_state:str=Field(default='101',max_length=6)
    basis_state:int=Field(default=1,ge=0,le=63)
    inverse:bool=False
    phase:float=Field(default=.375,ge=0,lt=1)
    oracle:Literal['constant','balanced']='balanced'
    mask:str=Field(default='101',max_length=6)
    constant:int=Field(default=0,ge=0,le=1)
    message:str=Field(default='10',pattern=r'^[01]{2}$')
    theta:float=Field(default=math.pi/3,ge=-2*math.pi,le=2*math.pi)
    phi:float=Field(default=math.pi/4,ge=-2*math.pi,le=2*math.pi)
    coupling:float=Field(default=.7,ge=-2,le=2)
    gate_error:float=Field(default=0,ge=0,le=.15)
    readout_error:float=Field(default=0,ge=0,le=.3)

    @model_validator(mode='after')
    def check_algorithm(self):
        if self.algorithm=='grover':
            if len(self.marked_state)!=self.qubits or any(c not in '01' for c in self.marked_state):
                raise ValueError('Marked bitstring must contain one 0 or 1 per search qubit.')
            if self.iterations>8: raise ValueError('Grover is limited to 8 amplification iterations.')
        if self.algorithm=='qft' and self.basis_state>=2**self.qubits:
            raise ValueError('Basis state must fit inside the register.')
        if self.algorithm in ('qpe','deutsch_jozsa') and self.qubits+1>MAX_QUBITS:
            raise ValueError('Counting/input qubits plus the target exceed the configured qubit cap.')
        if self.algorithm=='deutsch_jozsa' and self.oracle=='balanced':
            if len(self.mask)!=self.qubits or any(c not in '01' for c in self.mask) or '1' not in self.mask:
                raise ValueError('Balanced parity mask must fit the input register and contain at least one 1.')
        fixed={'bell':2,'interference':1,'superdense':2,'teleportation':3,'vqe':2,'chsh':2}
        if self.algorithm in fixed and fixed[self.algorithm]>MAX_QUBITS:
            raise ValueError('This experiment exceeds the configured qubit cap.')
        if self.algorithm=='vqe' and self.iterations<6:
            raise ValueError('The four-parameter VQE ansatz requires at least 6 evaluations.')
        return self


def fourier(n):
    """Positive-exponent QFT with q0 interpreted as the most significant bit."""
    from qiskit import QuantumCircuit
    qc=QuantumCircuit(n)
    for j in range(n):
        qc.h(j)
        for k in range(j+1,n): qc.cp(math.pi/2**(k-j),k,j)
    for j in range(n//2): qc.swap(j,n-1-j)
    return qc


def vqe(config):
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import Statevector
    from scipy.optimize import minimize
    z=np.diag([1,-1]);x=np.array([[0,1],[1,0]]);identity=np.eye(2)
    hamiltonian=-np.kron(z,identity)-np.kron(identity,z)+config.coupling*np.kron(x,x)
    def ansatz(parameters):
        qc=QuantumCircuit(2);qc.ry(parameters[0],0);qc.ry(parameters[1],1)
        qc.cx(0,1);qc.ry(parameters[2],0);qc.ry(parameters[3],1)
        return qc
    trace=[];best_energy=float('inf');best=None
    def objective(parameters):
        nonlocal best,best_energy
        state=Statevector.from_instruction(ansatz(parameters)).data
        energy=float(np.real(np.vdot(state,hamiltonian@state)))
        if energy<best_energy: best_energy=energy;best=np.array(parameters)
        trace.append({'evaluation':len(trace)+1,'expected_energy':energy,'best_energy':best_energy})
        return energy
    rng=np.random.default_rng(config.seed)
    fit=minimize(objective,rng.normal(0,.4,4),method='COBYLA',options={'maxiter':config.iterations,'rhobeg':.5,'tol':1e-6})
    ground=float(np.linalg.eigvalsh(hamiltonian)[0])
    return ansatz(best),{'variational_energy':best_energy,'exact_ground_energy':ground,
                         'energy_error':best_energy-ground,'evaluations':len(trace),'optimizer_status':str(fit.message)},trace


def run_experiment(config:ExperimentRequest):
    from qiskit import QuantumCircuit,transpile
    from qiskit.quantum_info import Statevector,partial_trace,state_fidelity
    from .quantum import execute_circuit,BASIS
    start=time.perf_counter();a=config.algorithm;n=config.qubits;metrics={};trace=[]
    notes=[]
    if a in ('bell','ghz','chsh'):
        qc=QuantumCircuit(n if a=='ghz' else 2);qc.h(0)
        for q in range(1,qc.num_qubits): qc.cx(0,q)
        if a=='chsh':
            correlations=[]
            for index,(left,right) in enumerate(((0,math.pi/4),(0,-math.pi/4),(math.pi/2,math.pi/4),(math.pi/2,-math.pi/4))):
                setting=qc.copy();setting.ry(-left,0);setting.ry(-right,1)
                output=execute_circuit(setting,config.shots,config.seed+index,config.readout_error,config.gate_error)
                exact=sum((1 if bits.count('1')%2==0 else -1)*p for bits,p in ((format(i,'02b'),p) for i,p in enumerate(output['probabilities'])))
                sampled=sum((1 if bits.count('1')%2==0 else -1)*count for bits,count in output['counts'].items())/config.shots
                correlations.append({'setting':f'A{index//2} B{index%2}','ideal':exact,'sampled':sampled,'counts':output['counts']})
            signs=[1,1,1,-1]
            metrics.update(ideal_chsh=sum(s*d['ideal'] for s,d in zip(signs,correlations)),
                           sampled_chsh=sum(s*d['sampled'] for s,d in zip(signs,correlations)),classical_bound=2,
                           setting_shots=config.shots)
            notes.append('CHSH uses four separate basis-setting circuits. The histogram below is the prepared Bell circuit; the correlation table contains the four actual measurement runs. This is an educational simulation, not a loophole-free physical Bell test.')
    elif a=='interference':
        qc=QuantumCircuit(1);qc.h(0);qc.rz(config.phi,0);qc.h(0)
        metrics['reference_p0']=math.cos(config.phi/2)**2
    elif a=='grover':
        qc=QuantumCircuit(n)
        for q in range(n): qc.h(q)
        for _ in range(config.iterations):
            for q,bit in enumerate(config.marked_state):
                if bit=='0': qc.x(q)
            qc.mcp(math.pi,list(range(n-1)),n-1)
            for q,bit in enumerate(config.marked_state):
                if bit=='0': qc.x(q)
            for q in range(n): qc.h(q);qc.x(q)
            qc.mcp(math.pi,list(range(n-1)),n-1)
            for q in range(n): qc.x(q);qc.h(q)
        metrics.update(marked_state=config.marked_state,uniform_probability=1/2**n,
                       reference_success=math.sin((2*config.iterations+1)*math.asin(1/math.sqrt(2**n)))**2,
                       oracle_queries=config.iterations)
        notes.append('The phase oracle is constructed from the supplied marked bitstring. This illustrates amplitude amplification; it is not a search over hidden external data. Too many iterations can reduce success.')
    elif a=='qft':
        qc=QuantumCircuit(n)
        for q,bit in enumerate(format(config.basis_state,f'0{n}b')):
            if bit=='1': qc.x(q)
        qc.compose(fourier(n).inverse() if config.inverse else fourier(n),inplace=True)
    elif a=='qpe':
        qc=QuantumCircuit(n+1);qc.x(n)
        for q in range(n):
            qc.h(q);qc.cp(2*math.pi*config.phase*2**(n-1-q),q,n)
        qc.compose(fourier(n).inverse(),qubits=list(range(n)),inplace=True)
        notes.append('U = diag(1, exp(2πiθ)); the target is prepared in eigenstate |1⟩. Counting qubits are q0…q[n−1], followed by the target. A finite register approximates phases not representable in n bits.')
    elif a=='deutsch_jozsa':
        qc=QuantumCircuit(n+1);qc.x(n)
        for q in range(n+1): qc.h(q)
        if config.constant: qc.x(n)
        if config.oracle=='balanced':
            for q,bit in enumerate(config.mask):
                if bit=='1': qc.cx(q,n)
        for q in range(n): qc.h(q)
        metrics['oracle_queries']=1
        notes.append('The selectable oracle family is f(x) = mask·x XOR constant for a nonzero parity mask, or a constant function. This is the promised Deutsch–Jozsa problem, not arbitrary function classification.')
    elif a=='superdense':
        qc=QuantumCircuit(2);qc.h(0);qc.cx(0,1)
        if config.message[0]=='1': qc.z(0)
        if config.message[1]=='1': qc.x(0)
        qc.cx(0,1);qc.h(0)
        notes.append('Alice and Bob first share one Bell pair. Alice encodes two classical bits and then sends her qubit to Bob; shared entanglement and one transmitted qubit are required.')
    elif a=='teleportation':
        qc=QuantumCircuit(3);qc.ry(config.theta,0);qc.rz(config.phi,0)
        qc.h(1);qc.cx(1,2);qc.cx(0,1);qc.h(0);qc.cx(1,2);qc.cz(0,2)
        target=QuantumCircuit(1);target.ry(config.theta,0);target.rz(config.phi,0)
        receiver=partial_trace(Statevector.from_instruction(qc),[0,1])
        metrics['receiver_fidelity']=float(state_fidelity(receiver,Statevector.from_instruction(target)))
        notes.append('This circuit uses the deferred-measurement equivalent of teleportation: coherent CX and CZ corrections replace intermediate measurements and classical feed-forward. It demonstrates receiver-state recovery, not actual remote communication or a dynamic measurement computer.')
    else:
        qc,metrics,trace=vqe(config)
        notes.append('H = −Z₀ − Z₁ + g X₀X₁. A four-angle RY/CNOT ansatz is optimized with COBYLA using exact expectation values. The independent 4×4 eigensolver supplies the ground-energy reference; training is noiseless and sampled readout is separate.')
    result=execute_circuit(qc,config.shots,config.seed,config.readout_error,config.gate_error)
    probabilities=np.asarray(result['probabilities'])
    if a in ('bell','ghz','chsh'):
        metrics['ideal_correlated_probability']=float(probabilities[0]+probabilities[-1])
    if a=='grover':
        metrics['success_probability']=float(probabilities[int(config.marked_state,2)])
        metrics['sampled_success']=result['counts'].get(config.marked_state,0)/config.shots
    if a=='qft':
        size=2**n;sign=-1 if config.inverse else 1
        reference=np.exp(sign*2j*np.pi*config.basis_state*np.arange(size)/size)/np.sqrt(size)
        amplitudes=np.asarray([complex(*z) for z in result['amplitudes']])
        metrics['reference_fidelity']=float(abs(np.vdot(reference,amplitudes))**2)
    if a in ('qpe','deutsch_jozsa'):
        marginal=probabilities.reshape(2**n,2).sum(axis=1)
        peak=int(np.argmax(marginal));bits=format(peak,f'0{n}b')
        metrics['input_register' if a=='deutsch_jozsa' else 'counting_register']=bits
        if a=='qpe':
            estimate=peak/2**n;difference=abs(estimate-config.phase)
            metrics.update(estimated_phase=estimate,circular_error=min(difference,1-difference),peak_probability=float(marginal[peak]))
        else: metrics['classification']='constant' if peak==0 else 'balanced'
    if a=='superdense':
        metrics.update(decoded_message=format(int(np.argmax(probabilities)),'02b'),success_probability=float(probabilities[int(config.message,2)]))
    native=transpile(qc,basis_gates=BASIS,optimization_level=0)
    result.update(kind='experiment',algorithm=a,metrics=metrics,trace=trace,
                  native_depth=native.depth(),native_gate_count=native.size(),
                  machine_program=result['qasm'] if native.size()+qc.num_qubits<=96 and qc.num_qubits<=8 else None,
                  correlations=correlations if a=='chsh' else [],runtime_s=time.perf_counter()-start,
                  limitations=notes+result['limitations'])
    return result
