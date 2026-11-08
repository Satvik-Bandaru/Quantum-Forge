# Compatibility and API verification

Originally checked November 4, 2026; extended for QuantumLab Research Command Center v0.3 on November 7, 2026 using the same Mac, Python 3.12.8, Node 24.21.0 and ARM64 CPU. The source folder remains `quantum-forge-lab`.

| Package | Tested version | Used APIs |
|---|---|---|
| PennyLane | 0.45.1 | `device('default.qubit')`, `qnode`, `Hadamard`, `DiagonalQubitUnitary`, `RX`, `probs` |
| Qiskit | 2.6.1 | `QuantumCircuit`, `Statevector`, `partial_trace`, `Pauli`, `transpile` |
| Qiskit Aer | 0.18.2 | `AerSimulator`, `NoiseModel`, `ReadoutError`, `depolarizing_error` |
| D-Wave samplers | 1.8.0 | `dwave.samplers.SimulatedAnnealingSampler` |
| dimod | 0.12.23 | `BinaryQuadraticModel.from_qubo` |
| OR-Tools | 9.15.6755 | snake_case CP-SAT model, Boolean constraints, single-worker solve |
| NumPy | 2.5.4 | arrays, exact basis enumeration, seeded RNG, multinomial/binomial/Gaussian sampling, complex optical transfer matrices, density-matrix diagnostics |
| SciPy | 1.18.1 | COBYLA minimization, explicit minimum evaluation-budget validation, `scipy.linalg.expm` for constant Hamiltonian/Lindblad evolution |
| FastAPI | 0.162.0 | lifespan, Pydantic validation, JSON/CSV endpoints, static frontend |

All packages were resolved together in a fresh virtual environment; `pip check` reported no broken requirements. Exact transitive pins are recorded in `requirements.lock.txt`. Both compiled quantum simulators installed from macOS ARM64 wheels. No GPU packages, IBM Runtime, D-Wave cloud clients, or provider credentials are required.

Primary sources consulted before implementation:

- [PennyLane default.qubit CPU/macOS device](https://pennylane.ai/devices/default-qubit)
- [PennyLane QAOA Max-Cut implementation tutorial](https://pennylane.ai/demos/tutorial_qaoa_maxcut)
- [Qiskit Aer maintained installation and simulator documentation](https://qiskit.github.io/qiskit-aer/getting_started.html)
- [D-Wave maintained sampler APIs](https://docs.dwavequantum.com/en/latest/ocean/api_ref_samplers/api_ref.html) — use `dwave.samplers`; older `neal` namespace is not used.
- [OR-Tools Python installation/platform guidance](https://developers.google.com/optimization/install/python)

Documentation establishes supported APIs; the application's scientific and integration tests verify their combined use in this exact environment. No claim is made that every future package release remains compatible.

## General lab extension — November 7, 2026

The same installed versions support the virtual computer and eleven general experiments. Added APIs: Qiskit state evolution, partial trace, entropy/purity, controlled phase and multi-controlled phase, QASM 2 export, and NumPy exact eigensolvers. No dependency installation or cloud connection was added. New programs are interpreted by a bounded AST/assembly parser, not evaluated as Python.

Primary references for the extension:

- [IBM Statevector API](https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.quantum_info.Statevector)
- [IBM quantum Fourier transform](https://quantum.cloud.ibm.com/learning/en/modules/computer-science/qft)
- [IBM superdense coding](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/entanglement-in-action/superdense-coding)
- [IBM quantum teleportation](https://quantum.cloud.ibm.com/learning/en/modules/computer-science/quantum-teleportation)
- [IBM variational eigensolver](https://quantum.cloud.ibm.com/learning/en/modules/computer-science/vqe)

## Physical and classical photonics labs — v0.3, November 7, 2026

Both additions use the already installed NumPy/SciPy environment. No new dependency, cloud service or hardware connection was added. The Rabi engine is an independently verified constant-generator solver built with SciPy matrix exponentials; it does not call QuTiP or claim a QuTiP integration. The MZI engine uses NumPy complex field transfer matrices and seeded repeated power-meter readings; it does not use a quantum optics solver.

The Physical Quantum Lab delivers a single two-level rotating-frame square pulse with detuning, phase, duration, ground/excited/plus initial states, optional T₁ relaxation and Tφ pure dephasing, ideal/noisy population traces, Bloch/density inspection and independently sampled binomial readout at each time. Its bath is zero-temperature and Markovian. Independent tests cover resonant/detuned analytic formulas, relaxation, T₂ coherence, rotation signs, purity/fidelity, trace/Hermiticity/positivity, finite JSON and bounded requests. See the [Rabi model](rabi-model.md).

The Photonics Lab delivers a fixed-topology, fully coherent classical Mach–Zehnder interferometer: one source, two lossless beam splitters, lossy mirror arms, a phase shifter and two power meters. Tests cover phase limits, complex field signs, wavelength/path units, asymmetric loss, exact visibility, blocked arms, power conservation, electronic meter uncertainty and request validation. The component palette populates predefined MZI slots; it does not create arbitrary optical networks. It performs neither FDTD nor single-photon/quantum-state propagation. See the [MZI model](mzi-model.md).

Both use the existing isolated job worker, input validation, cancellation, timeout/RSS limits, SQLite history and restoration. New CSV exports contain time/phase series and run metadata; full JSON preserves the complete executed result and configuration. The frontend supplies workbench schematics, controls, scopes, run pinning/comparison and main-plot SVG export. Measurement records remain distinct: physics shots are independent repeated qubit preparations at each time, while photonics readings are classical power plus Gaussian electronic noise.

The current FastAPI/Starlette test client produces its existing httpx adapter deprecation warning. Browser workflow and responsive verification are tracked in the [V3 audit and implementation plan](superpowers/plans/2026-11-07-physical-photonics.md). Single-photon/Hong–Ou–Mandel and Ramsey experiments are the next planned milestones. Advanced photonics/device/AI modules remain planned.

Additional primary references:

- [SciPy matrix exponential API and numerical method](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html)
- [Qiskit Dynamics driven-qubit and Lindblad tutorial](https://qiskit-community.github.io/qiskit-dynamics/stable/tutorials/Rabi_oscillations.html) — conceptual reference; the implemented solver is SciPy and its Tφ convention is documented explicitly.
- [NumPy binomial sampling](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.binomial.html)
- [NumPy Gaussian sampling](https://numpy.org/doc/stable/reference/random/generated/numpy.random.Generator.normal.html)
