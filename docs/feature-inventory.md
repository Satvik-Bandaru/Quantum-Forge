# Quantum Forge feature inventory

Audit date: 2026-11-07. This describes source code and executed checks, not the capabilities suggested by visual references. The existing React/Vite frontend, FastAPI API, isolated CPU worker and SQLite store are preserved. No framework migration, external connection, or data migration is required.

Status refers to the delivered subset where a broad family is only partial. **Functional and tested** means actual computation is covered by automated checks; it does not assert validation of every possible scientific application.

| Family | Status | Working evidence and remaining scope |
| --- | --- | --- |
| Circuit studio | Partially implemented; delivered subset functional and tested | `backend/quantum.py`, `tests/test_science.py`: real Qiskit/Aer gates, validation, counts, ideal amplitudes, reduced states and QASM. Generic CY/controlled rotations, reset operation and a general density-matrix viewer remain missing. |
| General algorithms | Partially implemented; delivered subset functional and tested | `backend/experiments.py`, `tests/test_general_lab.py`: 11 computed demonstrations including QFT, QPE, Grover, coherent teleportation, superdense coding, toy VQE and CHSH. Bernstein–Vazirani and mid-circuit feedback remain missing. |
| Virtual quantum computer | Functional and tested within stated scope | `backend/machine.py`, `VirtualComputer.tsx`: bounded 1–8-qubit assembly/QASM, up to 96 instructions, computed ideal snapshots and final noisy samples. No physical QPU or general-purpose Python execution. |
| Algorithm battle arena | Partially implemented; delivered subset functional and tested | `science.py` and `qubo.py`: common-instance comparisons, exact references, QAOA, Ocean classical annealing, CP-SAT for Max-Cut/knapsack, and new generic greedy/local-search baselines. Memory/init breakdowns and statistical multi-seed reports remain missing. |
| QUBO and Ising modeling | Functional and tested initial binary slice | New `qubo.py`, `QuboLab.tsx`, `tests/test_qubo.py`: editable upper-triangular matrix and offset, full Ising mapping, five executed solvers, encoded one-hot penalty example, actual counts/traces, model/run exports. General symbolic constraints, scheduling/TSP templates and automatic constraint verification remain missing. |
| Physical quantum laboratory | Functional and tested bounded model | `physics.py`, `tests/test_physics.py`: two-level square-pulse Lindblad propagation, relaxation/dephasing, independent finite-shot readout, physical density checks. No calibrated device simulation, Ramsey/echo or multilevel models. |
| Noise and error correction | Partially implemented | Tested circuit depolarization/readout and single-system T1/Tφ dynamics. Error-correcting codes, mitigation, connectivity routing and hardware calibration profiles are missing. |
| Quantum AI / machine learning | Missing | Roadmap only. No classifier, kernel, train/test experiment or claimed quantum AI result. |
| Photonics | Partially implemented; classical MZI functional and tested | `photonics.py`, `tests/test_photonics.py`: coherent two-mode fields, losses, phase sweeps, power conservation and electronic meter noise. Single photons, HOM, entanglement and arbitrary optical networks remain missing. |
| Networks and communication | Partially implemented | Executable ideal protocols exist in the experiment library. Network topology, lossy channels, repeaters, QKD and remote communication are missing. |
| Chemistry and materials | Missing | Existing VQE minimizes a toy two-spin Hamiltonian, not a molecular Hamiltonian. No H₂/basis-set/chemical-accuracy claim. |
| Space applications | Missing | Roadmap only. No orbit simulation, mission data or spacecraft control connection. |
| Supply-chain applications | Missing | Roadmap only. No ChainMind dependency or fictional business benchmark. |
| Hardware engineering | Partially implemented | Bounded all-to-all simulated register and logical depth. Profiles, native compilation/mapping comparisons and calibration are missing. Actual QPU execution is blocked by external infrastructure: no configured provider/account/credentials. |
| Research assistant | UI-only relative to generative AI requirement | Working curated local learning guide is explicitly labeled as such and can explain saved results. No generative model or natural-language execution layer. |
| Academy | Partially implemented | Four guides, experience modes and three challenges scored from saved scientific outcomes. Full course tracks, exercise persistence and coding assessments remain missing. |
| Research experiment center | Partially implemented; persistence functional and tested | `jobs.py`, `store.py`, `app.py`: seeds/config/versions/results/errors, history replay and JSON/CSV; physical/optical run pinning. Parameter sweeps, experiment naming, project management and multi-run reports remain missing. |
| Scientific visualization | Partially implemented; delivered plots computed | Circuit, Bloch, amplitudes, probability, convergence, Rabi density, optical powers; new coefficient-derived Ising graph and actual QUBO solver evidence. Decorative command-center wave art has no data axes and conveys no scientific measurement. Network/hardware/landscape visualizations remain missing. |
| Performance controls | Functional and tested bounded foundation | One spawned worker, hard timeout, cancellation, RSS monitor, finite input limits, ≤12 circuit qubits and ≤8 generic QUBO variables. No cache or remote compute. |
| Architecture | Partially implemented | Separate local scientific engines and shared job/persistence boundary. Existing API routes are local `/api` endpoints; versioned authenticated external integration APIs remain missing. All scientific dependencies are currently installed together. |
| Scientific validation | Functional and tested delivered foundation | Analytical reference states, independent Fourier/Ising/QAOA calculations, exhaustive optimization, density physicality, power conservation, API/worker boundaries, history/exports and real browser workflows. No validation is claimed for missing modules. |
| Integrity and integrations | Integrity applied to delivered scope; integrations missing | CPU simulation, classical optics and ideal/noisy distinctions are explicit. Roadmap features do not masquerade as working providers, AI systems or experimental hardware. |

## Boundary fixes found during this audit

- Valid maximum seeds with repeated optimization runs previously exceeded Ocean's seed range. Derived seeds now wrap modulo `2**31`, with effective seeds retained per solver and regression checks for both boundary and ordinary cases.
- Request sizing previously trusted `Content-Length`, and malformed values could raise a server error. A bounded ASGI body reader now checks actual bytes before JSON parsing, rejects malformed lengths, and supports chunked input without bypassing the cap.
- New solver records use absolute gaps rather than the legacy optimization quality ratio. History tolerates both schemas; QUBO CSV preserves energies, gaps, settings and versions.

## Next implementation order

1. Phase 3: bounded parameter sweeps, multiple recorded seeds, and exported benchmark reports with explicit comparison assumptions.
2. Advanced-computing demonstrations: readout mitigation and small error-correction circuits with independently checked noise behavior.
3. Quantum ML with classical baselines and rigorous data splits; then quantum photons/HOM and molecular models.
4. Domain-specific space/logistics problems and optional external services only after the local models and documented interfaces exist.

The [current delivery plan](superpowers/plans/2026-11-07-quantum-forge-qubo.md) records verification results. The complete user master request remains in [requirements](requirements/quantum-forge-master.md).
