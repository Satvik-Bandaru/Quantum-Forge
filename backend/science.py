"""Small-instance, exact statevector experiments. Display order is always q0 first."""
import importlib.metadata
import time
import numpy as np
from .models import CircuitRequest, OptimizationRequest

PACKAGES = ['pennylane','qiskit','qiskit-aer','dwave-samplers','ortools','numpy','scipy']

def versions():
    return {name:importlib.metadata.version(name) for name in PACKAGES}


def run_circuit(config: CircuitRequest):
    from .quantum import circuit_from_config,execute_circuit
    return execute_circuit(circuit_from_config(config),config.shots,config.seed,config.readout_error,config.gate_error)


def build_problem(config: OptimizationRequest):
    if config.problem == 'maxcut':
        n = config.nodes
        Q = {}
        for i,j,w in config.edges:
            Q[(i,i)] = Q.get((i,i),0)-w
            Q[(j,j)] = Q.get((j,j),0)-w
            Q[(min(i,j),max(i,j))] = 2*w
        offset = 0
        decision_n=n
        penalty=None
        slack=[]
    else:
        decision_n=len(config.weights)
        slack=[2**i for i in range(config.capacity.bit_length())]
        coefficients=config.weights+slack
        n=len(coefficients)
        penalty=sum(config.values)+1
        Q={}
        for i,a in enumerate(coefficients):
            Q[(i,i)] = penalty*(a*a-2*config.capacity*a) - (config.values[i] if i<decision_n else 0)
            for j in range(i+1,n):
                Q[(i,j)]=2*penalty*a*coefficients[j]
        offset=penalty*config.capacity**2
    states=((np.arange(2**n)[:,None] >> np.arange(n-1,-1,-1)) & 1).astype(int)
    energy=np.full(2**n,float(offset))
    for (i,j),coefficient in Q.items():
        energy+=coefficient*states[:,i]*states[:,j]
    if config.problem=='maxcut':
        objective=-energy
        feasible=np.ones(2**n,dtype=bool)
    else:
        objective=states[:,:decision_n]@np.asarray(config.values)
        feasible=(states[:,:decision_n]@np.asarray(config.weights))<=config.capacity
    return {'n':n,'decision_n':decision_n,'Q':Q,'offset':offset,'states':states,'energy':energy,
            'objective':objective,'feasible':feasible,'penalty':penalty,'slack_weights':slack}


def classical_baseline(config,problem):
    from ortools.sat.python import cp_model
    start=time.perf_counter()
    model=cp_model.CpModel()
    n=problem['decision_n']
    variables=[model.new_bool_var(f'x{i}') for i in range(n)]
    if config.problem=='maxcut':
        terms=[]
        for k,(i,j,w) in enumerate(config.edges):
            diff=model.new_bool_var(f'cut{k}')
            model.add_allowed_assignments([variables[i],variables[j],diff],[(0,0,0),(0,1,1),(1,0,1),(1,1,0)])
            terms.append(w*diff)
        model.maximize(sum(terms))
    else:
        model.add(sum(w*x for w,x in zip(config.weights,variables))<=config.capacity)
        model.maximize(sum(v*x for v,x in zip(config.values,variables)))
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=5
    solver.parameters.num_search_workers=1
    solver.parameters.random_seed=config.seed
    status=solver.solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        raise RuntimeError('Classical solver did not return a feasible solution within its budget.')
    return {'algorithm':'OR-Tools CP-SAT','version':importlib.metadata.version('ortools'),
            'backend':'classical CPU','objective':float(solver.objective_value),
            'solution':[solver.value(x) for x in variables],'feasible':True,'violations':0,
            'runtime_s':time.perf_counter()-start,'status':solver.status_name(status),
            'qubits':None,'depth':None,'shots':None,'evaluations':int(solver.num_branches)}


def summarize_samples(config,problem,counts,algorithm,runtime,**details):
    n=problem['n']
    # Select the best observed feasible item solution; NEVER replace it with the exact answer.
    candidates=[int(key,2) for key,count in counts.items() if count>0]
    feasible=[i for i in candidates if problem['feasible'][i]]
    best=max(feasible,key=lambda i:problem['objective'][i]) if feasible else None
    feasible_reads=sum(count for key,count in counts.items() if problem['feasible'][int(key,2)])
    return {'algorithm':algorithm,'runtime_s':runtime,'counts':counts,
            'objective':float(problem['objective'][best]) if best is not None else None,
            'solution':problem['states'][best,:problem['decision_n']].tolist() if best is not None else None,
            'full_bitstring':format(best,f'0{n}b') if best is not None else None,
            'energy':float(problem['energy'][best]) if best is not None else None,
            'feasible':best is not None,'violations':0 if best is not None else None,
            'feasible_fraction':feasible_reads/sum(counts.values()),
            'status':'SAMPLED_FEASIBLE' if best is not None else 'NO_FEASIBLE_SAMPLE',**details}


def run_qaoa(config,problem,seed):
    import pennylane as qml
    from scipy.optimize import minimize
    start=time.perf_counter()
    n=problem['n']
    energy=problem['energy']
    scale=max(float(np.max(np.abs(energy))),1)
    device=qml.device('default.qubit',wires=n)
    @qml.qnode(device,interface=None,diff_method=None)
    def circuit(parameters):
        for wire in range(n): qml.Hadamard(wires=wire)
        for layer in range(config.layers):
            qml.DiagonalQubitUnitary(np.exp(-1j*parameters[layer]*energy/scale),wires=range(n))
            for wire in range(n): qml.RX(2*parameters[config.layers+layer],wires=wire)
        return qml.probs(wires=range(n))
    trace=[]
    best_parameters=None
    best_energy=float('inf')
    def objective(parameters):
        nonlocal best_parameters,best_energy
        expectation=float(np.dot(np.asarray(circuit(parameters)),energy))
        if expectation<best_energy:
            best_energy=expectation
            best_parameters=np.array(parameters)
        trace.append({'evaluation':len(trace)+1,'expected_energy':expectation,'best_energy':best_energy})
        return expectation/scale
    rng=np.random.default_rng(seed)
    initial=rng.uniform(0,np.pi,2*config.layers)
    fitted=minimize(objective,initial,method='COBYLA',options={'maxiter':config.iterations,'rhobeg':0.6,'tol':1e-4})
    probabilities=np.maximum(np.asarray(circuit(best_parameters)),0)
    probabilities=probabilities/probabilities.sum()
    sampled=rng.multinomial(config.shots,probabilities)
    counts={format(i,f'0{n}b'):int(c) for i,c in enumerate(sampled) if c}
    # Dense diagonal unitary remains a high-level operation; report depth honestly.
    return summarize_samples(config,problem,counts,'QAOA',time.perf_counter()-start,
        backend='PennyLane default.qubit / local CPU statevector',version=importlib.metadata.version('pennylane'),
        qubits=n,depth=1+2*config.layers,depth_convention='Logical depth: parallel H, then one dense diagonal cost operation and parallel RX per layer. Not native gate depth.',
        shots=config.shots,evaluations=len(trace),trace=trace,parameters=best_parameters.tolist(),
        probabilities=probabilities.tolist(),expected_energy=best_energy,optimizer_status=str(fitted.message),
        seed=seed,layers=config.layers)


def run_annealing(config,problem,seed):
    import dimod
    from dwave.samplers import SimulatedAnnealingSampler
    start=time.perf_counter()
    bqm=dimod.BinaryQuadraticModel.from_qubo(problem['Q'],offset=problem['offset'])
    for i in range(problem['n']):
        if i not in bqm.variables: bqm.add_variable(i,0)
    samples=SimulatedAnnealingSampler().sample(bqm,num_reads=min(config.shots,1024),num_sweeps=200,seed=seed)
    counts={}
    for record in samples.data(['sample','num_occurrences']):
        bits=''.join(str(int(record.sample[i])) for i in range(problem['n']))
        counts[bits]=counts.get(bits,0)+int(record.num_occurrences)
    return summarize_samples(config,problem,counts,'Simulated annealing',time.perf_counter()-start,
        backend='D-Wave Ocean / classical CPU (no QPU)',version=importlib.metadata.version('dwave-samplers'),
        qubits=None,depth=None,shots=sum(counts.values()),evaluations=sum(counts.values())*200,seed=seed,sweeps=200)


def run_optimization(config: OptimizationRequest):
    start=time.perf_counter()
    problem=build_problem(config)
    baseline=classical_baseline(config,problem)
    exact=float(np.max(problem['objective'][problem['feasible']]))
    baseline['quality']=baseline['objective']/exact if exact else 1
    solvers=[baseline]
    for repetition in range(config.repetitions):
        # Ocean accepts signed-31-bit seeds; retain ordinary successive seeds
        # and record the effective wrapped seed on each stochastic result.
        seed=(config.seed+repetition) % (2**31)
        for result in (run_qaoa(config,problem,seed),run_annealing(config,problem,seed)):
            result['quality']=result['objective']/exact if result['objective'] is not None and exact else (1 if result['objective']==0 else None)
            result['repetition']=repetition+1
            solvers.append(result)
    return {'kind':'optimization','problem':config.problem,'qubits':problem['n'],'baseline':baseline,
        'exact_optimum':exact,'solvers':solvers,'runtime_s':time.perf_counter()-start,
        'versions':versions(),'seed':config.seed,'penalty':problem['penalty'],'slack_weights':problem['slack_weights'],
        'qubo':{'terms':[[i,j,float(c)] for (i,j),c in problem['Q'].items()],'offset':problem['offset']},
        'limitations':['All methods run on a local CPU. Simulating a quantum circuit is not quantum hardware execution.',
                      'QAOA optimizes an exact expectation, then samples finite shots. Training uses no shot noise.',
                      'Dense diagonal cost evolution is used for small problems; logical depth is not a native hardware gate count.',
                      'QAOA and annealing report the best observed feasible item solution, including feasible knapsack items whose sampled slack is not canonical.',
                      'The exact optimum is enumerated separately for these bounded instances. Simulator timings cannot establish quantum advantage.',
                      'Repetition r (starting at zero) uses (configured seed + r) modulo 2^31. Each stochastic solver records its effective seed.',
                      'Annealing reads are capped at 1024 with 200 sweeps; QAOA shots and objective evaluations have different computational costs.']}
