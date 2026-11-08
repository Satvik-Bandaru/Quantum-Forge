"""Bounded generic QUBOs, independent classical baselines and simulated QAOA.

Every energy is minimized; q0 is the most significant displayed bit. Constraints
exist only when the submitted coefficients already encode their penalties.
"""
import importlib.metadata
import time
from typing import Annotated

import numpy as np
from pydantic import Field, model_validator

from .models import MAX_QUBITS, StrictModel
from .science import versions

MAX_VARIABLES = min(8, MAX_QUBITS)
Coefficient = Annotated[float, Field(strict=True, ge=-100, le=100)]
Row = Annotated[list[Coefficient], Field(min_length=2, max_length=MAX_VARIABLES)]


class QuboRequest(StrictModel):
    matrix: list[Row] = Field(min_length=2, max_length=MAX_VARIABLES)
    offset: float = Field(default=0, strict=True, ge=-1000, le=1000)
    layers: int = Field(default=1, strict=True, ge=1, le=3)
    iterations: int = Field(default=35, strict=True, ge=4, le=80)
    shots: int = Field(default=512, strict=True, ge=128, le=4096)
    seed: int = Field(default=42, strict=True, ge=0, le=2**31 - 1)

    @model_validator(mode='after')
    def canonical_matrix_and_budget(self):
        n = len(self.matrix)
        if any(len(row) != n for row in self.matrix):
            raise ValueError('QUBO matrix must be square.')
        if any(self.matrix[i][j] != 0 for i in range(n) for j in range(i)):
            raise ValueError('Use canonical upper-triangular coefficients: entries below the diagonal must be zero.')
        if self.iterations < 2 * self.layers + 2:
            raise ValueError('COBYLA iterations must be at least 2*layers+2 to initialize all variational parameters.')
        return self


def qubo_to_ising(matrix, offset=0):
    """Expand xi=(1-zi)/2, retaining the complete constant and every field."""
    q = np.asarray(matrix, dtype=float)
    n = len(q)
    h = -np.diag(q) / 2
    coupling = np.zeros((n, n), dtype=float)
    constant = float(offset + np.trace(q) / 2)
    for i in range(n):
        for j in range(i + 1, n):
            coupling[i, j] = q[i, j] / 4
            h[i] -= q[i, j] / 4
            h[j] -= q[i, j] / 4
            constant += q[i, j] / 4
    return {'h': h.tolist(), 'J': coupling.tolist(), 'offset': constant}


def build_qubo(config: QuboRequest):
    """Enumerate all bounded bitstrings for the explicitly identified oracle."""
    n = len(config.matrix)
    states = ((np.arange(2**n)[:, None] >> np.arange(n - 1, -1, -1)) & 1).astype(int)
    q = np.asarray(config.matrix, dtype=float)
    energy = np.full(2**n, config.offset, dtype=float)
    for i in range(n):
        energy += q[i, i] * states[:, i]
        for j in range(i + 1, n):
            energy += q[i, j] * states[:, i] * states[:, j]
    return {'n': n, 'matrix': q, 'offset': config.offset, 'states': states, 'energy': energy}


def _energy(problem, state):
    # Greedy/local search evaluate submitted coefficients, never the oracle's
    # optimum or its ranked state table.
    bits = np.asarray(state, dtype=int)
    return float(problem['offset'] + bits @ problem['matrix'] @ bits)


def _result(key, algorithm, family, energy, solution, runtime, evaluations, **details):
    bits = [int(bit) for bit in solution]
    return {'key': key, 'algorithm': algorithm, 'family': family, 'energy': float(energy),
            'solution': bits, 'bitstring': ''.join(map(str, bits)), 'runtime_s': runtime,
            'evaluations': int(evaluations), **details}


def _greedy(problem):
    start = time.perf_counter()
    state = np.zeros(problem['n'], dtype=int)
    energy = _energy(problem, state)
    trace = [{'evaluation': 1, 'energy': energy, 'best_energy': energy}]
    for i in range(problem['n']):
        candidate = state.copy()
        candidate[i] ^= 1
        trial = _energy(problem, candidate)
        if trial < energy:
            state, energy = candidate, trial
        trace.append({'evaluation': len(trace) + 1, 'energy': trial, 'best_energy': energy})
    return _result('greedy', 'Greedy one pass', 'classical heuristic', energy, state,
                   time.perf_counter() - start, len(trace), trace=trace,
                   evaluation_unit='QUBO energy evaluations',
                   backend='NumPy / classical CPU',
                   policy='Start at all zeros; visit q0 through q(n-1) once, accepting strictly improving flips.')


def _local_search(problem, seed):
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    restarts = min(16, 2 * problem['n'])
    best_energy = float('inf')
    best_state = None
    trace = []

    def evaluate(state):
        nonlocal best_energy, best_state
        energy = _energy(problem, state)
        if energy < best_energy:
            best_energy, best_state = energy, state.copy()
        trace.append({'evaluation': len(trace) + 1, 'energy': energy, 'best_energy': best_energy})
        return energy

    for _ in range(restarts):
        state = rng.integers(0, 2, size=problem['n'])
        energy = evaluate(state)
        while True:
            next_state, next_energy = state, energy
            for i in range(problem['n']):
                candidate = state.copy()
                candidate[i] ^= 1
                trial = evaluate(candidate)
                if trial < next_energy:
                    next_state, next_energy = candidate, trial
            if next_energy >= energy:
                break
            state, energy = next_state, next_energy
    return _result('local_search', 'Multistart 1-bit local search', 'classical heuristic',
                   best_energy, best_state, time.perf_counter() - start, len(trace), trace=trace,
                   evaluation_unit='QUBO energy evaluations', backend='NumPy / classical CPU',
                   restarts=restarts, seed=seed,
                   policy='Seeded random starts; steepest strictly improving one-bit flips until a local minimum.')


def _best_observed(problem, counts):
    candidates = [(float(_energy(problem, [int(bit) for bit in bits])), bits)
                  for bits, count in counts.items() if count > 0]
    energy, bits = min(candidates)
    return energy, [int(bit) for bit in bits]


def _annealing(config, problem):
    initialization_start = time.perf_counter()
    import dimod
    from dwave.samplers import SimulatedAnnealingSampler

    n = problem['n']
    terms = {(i, j): float(problem['matrix'][i, j]) for i in range(n) for j in range(i, n)}
    bqm = dimod.BinaryQuadraticModel.from_qubo(terms, offset=config.offset)
    # A constant cost is a valid editable model. Its temperature is immaterial;
    # explicitly supply a schedule rather than trigger Ocean's bias-heuristic
    # warning. Seeded uniform initial states retain uniform marginal samples.
    options = {'beta_range': (.1, 1.0)} if not np.any(problem['matrix']) else {}
    sampler = SimulatedAnnealingSampler()
    initialization_s = time.perf_counter() - initialization_start
    start = time.perf_counter()
    samples = sampler.sample(
        bqm, num_reads=config.shots, num_sweeps=200, seed=config.seed, **options)
    counts = {}
    for record in samples.data(['sample', 'num_occurrences']):
        bits = ''.join(str(int(record.sample[i])) for i in range(n))
        counts[bits] = counts.get(bits, 0) + int(record.num_occurrences)
    energy, state = _best_observed(problem, counts)
    return _result('annealing', 'Simulated annealing', 'classical stochastic', energy, state,
                   time.perf_counter() - start, config.shots, counts=counts,
                   initialization_s=initialization_s,
                   evaluation_unit='Reported sample energies; internal annealing work is not an objective-evaluation count',
                   backend='D-Wave Ocean / classical CPU (no QPU)', shots=config.shots,
                   sweeps=200, spin_update_budget=config.shots * 200 * n, seed=config.seed,
                   trace=[], status='BEST_OBSERVED_SAMPLE')


def _qaoa_circuit(config):
    import pennylane as qml

    n = len(config.matrix)
    mapped = qubo_to_ising(config.matrix, config.offset)
    fields, couplings = mapped['h'], mapped['J']
    # A uniform constant contributes only global phase. Keep angles and search
    # unchanged when users shift the objective by a constant.
    scale = max(1.0, sum(abs(value) for value in fields)
                + sum(abs(couplings[i][j]) for i in range(n) for j in range(i + 1, n)))
    device = qml.device('default.qubit', wires=n, shots=None)

    @qml.qnode(device, interface=None, diff_method=None)
    def circuit(parameters):
        for i in range(n):
            qml.Hadamard(wires=i)
        for layer in range(config.layers):
            gamma, beta = parameters[layer], parameters[config.layers + layer]
            for i, field in enumerate(fields):
                if field != 0:
                    qml.RZ(2 * gamma * field / scale, wires=i)
            for i in range(n):
                for j in range(i + 1, n):
                    if couplings[i][j] != 0:
                        qml.IsingZZ(2 * gamma * couplings[i][j] / scale, wires=[i, j])
            for i in range(n):
                qml.RX(2 * beta, wires=i)
        return qml.probs(wires=range(n))

    # Critical-path depth for precisely the logical gate sequence above. RZ,
    # IsingZZ and RX each count as one operation; no native decomposition.
    depth = [1] * n
    for _ in range(config.layers):
        for i, field in enumerate(fields):
            depth[i] += int(field != 0)
        for i in range(n):
            for j in range(i + 1, n):
                if couplings[i][j] != 0:
                    depth[i] = depth[j] = max(depth[i], depth[j]) + 1
        depth = [value + 1 for value in depth]
    return circuit, scale, max(depth)


def qaoa_probabilities(config: QuboRequest, parameters):
    """Evaluate fixed angles for reproducible scientific reference checks.

    Parameter order is all p gamma angles followed by all p beta angles.
    """
    angles = np.asarray(parameters, dtype=float)
    if angles.shape != (2 * config.layers,) or not np.all(np.isfinite(angles)):
        raise ValueError('QAOA needs exactly 2*layers finite angles.')
    circuit, _, _ = _qaoa_circuit(config)
    return np.asarray(circuit(angles), dtype=float).tolist()


def _qaoa(config, problem):
    initialization_start = time.perf_counter()
    from scipy.optimize import minimize

    circuit, scale, depth = _qaoa_circuit(config)
    trace = []
    best_energy, best_parameters = float('inf'), None
    best_probabilities = None

    def objective(parameters):
        nonlocal best_energy, best_parameters, best_probabilities
        probabilities = np.asarray(circuit(parameters), dtype=float)
        expected = float(probabilities @ problem['energy'])
        if expected < best_energy:
            best_energy = expected
            best_parameters = np.asarray(parameters).copy()
            best_probabilities = probabilities.copy()
        trace.append({'evaluation': len(trace) + 1, 'expected_energy': expected, 'best_energy': best_energy})
        return (expected - qubo_constant) / scale

    qubo_constant = qubo_to_ising(config.matrix, config.offset)['offset']
    rng = np.random.default_rng(config.seed)
    initial = rng.uniform(0, np.pi, 2 * config.layers)
    initialization_s = time.perf_counter() - initialization_start
    start = time.perf_counter()
    fitted = minimize(objective, initial, method='COBYLA',
                      options={'maxiter': config.iterations, 'rhobeg': .6, 'tol': 1e-4})
    probabilities = np.maximum(best_probabilities, 0)
    probabilities /= probabilities.sum()
    sampled = rng.multinomial(config.shots, probabilities)
    counts = {format(i, f'0{problem["n"]}b'): int(count) for i, count in enumerate(sampled) if count}
    energy, state = _best_observed(problem, counts)
    return _result('qaoa', 'QAOA', 'quantum circuit simulation', energy, state,
                   time.perf_counter() - start, len(trace), trace=trace, counts=counts,
                   initialization_s=initialization_s,
                   probabilities=probabilities.tolist(), expected_energy=float(probabilities @ problem['energy']),
                   parameters=best_parameters.tolist(), initial_parameters=initial.tolist(),
                   parameter_order='gamma[0:p], beta[0:p]', cost_scale=scale,
                   p=config.layers, layers=config.layers, depth=depth, logical_depth=depth,
                   depth_convention='Critical-path depth in H, RZ, IsingZZ and RX logical operations; not native hardware gate depth.',
                   qubits=problem['n'], shots=config.shots, seed=config.seed,
                   backend='PennyLane default.qubit / local CPU statevector',
                   evaluation_unit='Exact statevector expectation evaluations during COBYLA training',
                   optimizer='COBYLA', optimizer_status=str(fitted.message),
                   status='BEST_OBSERVED_SAMPLE')


def run_qubo(config: QuboRequest | dict):
    """Validated, worker-friendly bounded QUBO solver battle."""
    if not isinstance(config, QuboRequest):
        config = QuboRequest(**config)
    start = time.perf_counter()
    exact_start = time.perf_counter()
    problem = build_qubo(config)
    exact_index = int(np.argmin(problem['energy']))
    exact_energy = float(problem['energy'][exact_index])
    exact_solutions = problem['states'][problem['energy'] == exact_energy].tolist()
    exact = _result('exact', 'Exhaustive enumeration', 'classical exact', exact_energy,
                    problem['states'][exact_index], time.perf_counter() - exact_start, 2**problem['n'],
                    evaluation_unit='Enumerated bitstring energies', backend='NumPy / classical CPU',
                    status='EXACT_OPTIMUM', trace=[])
    solvers = [exact, _greedy(problem), _local_search(problem, config.seed),
               _annealing(config, problem), _qaoa(config, problem)]
    for solver in solvers:
        solver['gap'] = solver['energy'] - exact_energy
        if 'expected_energy' in solver:
            solver['expected_gap'] = solver['expected_energy'] - exact_energy
    result = {'kind': 'qubo', 'qubits': problem['n'], 'matrix': config.matrix, 'offset': config.offset,
            'exact_energy': exact_energy, 'exact_solutions': exact_solutions,
            'energy_table': [{'bitstring': format(i, f'0{problem["n"]}b'), 'solution': state.tolist(),
                              'energy': float(problem['energy'][i])} for i, state in enumerate(problem['states'])],
            'ising': qubo_to_ising(config.matrix, config.offset), 'solvers': solvers,
            'seed': config.seed, 'shots': config.shots,
            'versions': versions() | {'dimod': importlib.metadata.version('dimod')},
            'energy_units': 'arbitrary units', 'bit_order': 'q0 first (most significant bit)',
            'limits': {'min_variables': 2, 'max_variables': MAX_VARIABLES, 'coefficient_abs_max': 100,
                       'offset_abs_max': 1000, 'max_layers': 3, 'max_iterations': 80,
                       'max_shots': 4096, 'annealing_sweeps': 200},
            'limitations': [
                'All solvers execute on a local classical CPU. QAOA is a quantum circuit simulation; Ocean simulated annealing uses no QPU.',
                'Energies are minimized in arbitrary units. Gaps are energy minus the separately enumerated exact minimum; ratios are not used.',
                'Only the submitted QUBO is solved. Constraints are not interpreted or checked; they must already be encoded as coefficient penalties.',
                'QAOA trains with exact statevector expectations and COBYLA, then samples finite shots. Training has no shot noise or hardware noise.',
                'QAOA reports the best observed sample and its energy separately from the optimized expectation. The exact solution is never substituted.',
                'QAOA logical depth counts H, RZ, IsingZZ and RX operations, without native hardware decomposition or connectivity routing.',
                'Classical wall times and different solver evaluation units are not hardware performance comparisons and cannot establish quantum advantage.',
                'One seeded run is not a statistical benchmark. Annealing uses the requested reads and 200 sweeps; local search uses up to 16 restarts.',
            ]}
    result['runtime_s'] = time.perf_counter() - start
    return result
