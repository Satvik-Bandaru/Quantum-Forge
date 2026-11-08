# Quantum Forge — Quantum Computing Laboratory

A working personal scientific laboratory for a Mac laptop. React/TypeScript frontend, FastAPI service, local CPU simulation, and SQLite experiment history. **Version 0.4 adds an editable QUBO and Ising laboratory with five executed solvers and a refreshed Quantum Forge command center.** The programmable virtual quantum computer, circuit studio, general experiments, driven two-level Rabi model, and classical Mach–Zehnder bench remain available. The source folder remains `quantum-forge-lab`. Advanced quantum optics, quantum ML, error correction, and domain-specific space/supply-chain modules remain planned.

## Open the app

Double-click **`start.command`** in this folder. It starts the local service and opens **http://127.0.0.1:8777**. Leave its Terminal window running; Ctrl+C stops the service and terminates an active worker. If the lab is already running, the launcher opens that instance.

Dependencies and the production frontend are already installed/built on this Mac. The application itself needs no Internet connection, GPU, account, cloud service, or API key. No fonts or scripts are fetched from a CDN.

For a clean installation (Python 3.12 and Node 22+ recommended):

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm --prefix frontend ci
npm --prefix frontend run build
.venv/bin/python launch.py
```

`requirements.lock.txt` records the exact tested Python environment on macOS ARM64; `frontend/package-lock.json` records the frontend dependencies. For an identical Mac environment, install `requirements.lock.txt` instead of `requirements.txt`.

## Things that work

- **QUBO & Ising Lab:** edit a canonical upper-triangular binary model with 2–8 variables, a constant offset, and bounded solver settings. Inspect the derived Ising fields/couplings, start with negative Max-Cut or an adjustable one-hot penalty, import/export model JSON, and compare exhaustive enumeration, greedy assignment, multistart local search, Ocean classical annealing, and PennyLane QAOA. View actual energies, absolute gaps, CPU timings, optimizer traces, finite-shot counts, and complete saved provenance. Constraints exist only through supplied coefficients; no general symbolic constraint parser or separate feasibility checker is claimed.

- **Physical Quantum Lab:** a schematic workbench for one driven two-level system. Set pulse amplitude, detuning, duration and phase, initial state, T₁ relaxation and Tφ pure dephasing. A virtual oscilloscope compares ideal coherent evolution, Lindblad density-matrix evolution, and independent finite-shot measurements. Inspect pulse and Bloch channels, purity, fidelity, T₂ and the final density matrix. SciPy evaluates the constant generator's matrix exponential; this is an effective square-pulse rotating-frame model with a zero-temperature Markovian bath, not a calibrated hardware simulator.
- **Photonics Lab:** explore the supplied studio photo with equipment hotspots, enlarged details, plain-language explanations, and direct jumps to each model control. Switch between **Photo lab** and **Schematic** while keeping the same component selection. The image is a visual reference; its embedded chart values are illustrative. In the working MZI model, place a coherent source, two splitters, two mirrors, a phase shifter and two power meters into predefined Mach–Zehnder slots. Adjust optical power, wavelength, optical path difference, splitter ratios, arm transmissions and electronic meter noise. Inspect complex fields, phase-sweep power fringes, exact visibility, loss and power balance. Repeated meter readings include independent Gaussian electronic noise and uncertainty. This is fixed-topology, fully coherent **classical wave optics**; it does not model arbitrary optical circuits, FDTD or quantum photons.
- **Scientific run comparisons and exports:** pin a completed physical or optical run, change settings and execute again. Matching time/phase grids support trace overlays; final/selected-phase metrics remain comparable when grids differ. Restore executed settings and results from History. Export full run JSON, time/phase-series CSV, and the main plot as SVG. JSON includes the complete series and raw meter readings returned by the models; CSV is the plotted numerical series with configuration and provenance.
- **Virtual Quantum Computer:** a programmable 1–8-qubit machine, with quantum assembly and a bounded OpenQASM 2 subset. Compile and execute up to 96 instructions, inspect the ideal state after each instruction, step forward/back, rewind or play the trace. Qubit registers show probabilities, Bloch vectors, purity and single-qubit entanglement entropy. Export programs and actual QASM, import them, replay saved runs, and move compatible circuits to the visual builder. This is a classical simulation of a gate-based quantum computer, not physical QPU hardware.
- **General Quantum Experiments:** 11 executable experiments: Bell and GHZ entanglement, interference, Grover search, QFT/inverse QFT, phase estimation, Deutsch–Jozsa, superdense coding, coherent deferred-measurement teleportation, VQE, and CHSH correlations. Editable parameters, independent analytic/exact checks, complex amplitudes and phase displays, circuit inspection, noise-aware sampled readout, and saved history. Compatible decomposed circuits can be opened directly on the virtual computer.

- **Circuit Builder:** drag gates onto qubit wires, or use the keyboard-accessible gate palette and sequence editor. X, Y, Z, H, S/SDG, T/TDG, P, RX/RY/RZ, CNOT, CZ, CP, SWAP, CCX, and terminal measurement. Up to 12 qubits, reproducible shots, ideal statevectors and reduced Bloch vectors. Qiskit Aer simulates configured gate depolarization and readout errors in the measurement histogram. Download SVG diagrams; save, restore, import, and export circuit configurations.
- **Optimization Lab:** editable weighted Max-Cut and integer knapsack instances. PennyLane QAOA, D-Wave Ocean's **classical** simulated annealing, and OR-Tools CP-SAT. Separate exhaustive verification, feasibility checks, observed objective/quality, timing, measurement distributions, and QAOA convergence traces. Repeat stochastic methods with successive seeds.
- **Control center and history:** statistics derived from the latest 200 actual run records, with that window identified; persistent input/output records, including cancelled, timed-out, and failed attempts. Load a run to inspect or replay it. JSON exports preserve the full record; optimization CSV contains solver metadata; circuit CSV contains per-state ideal probabilities, amplitudes, and measured counts.
- **Experience modes:** Beginner includes learning notes and hides math behind expandable sections. Experiment emphasizes configuration and outputs. Research adds detailed QUBO/configuration records, amplitudes, versions, and parameters.
- **Learning:** stepwise explanations of QAOA, annealing, classical baselines, and Bell states. Three replayable challenges score saved scientific results, not button clicks. The local learning guide uses **curated reference explanations** and actual current-run evidence; it is not a generative AI model.
- **Execution controls:** one isolated spawned process at a time, live stages, cancellation, hard timeout, RSS memory watchdog, input validation, and helpful errors. Only loopback hostnames and local browser mutation origins are accepted. Received request bodies are capped at 256 KB before JSON parsing, including chunked or underdeclared bodies.

## Start with a binary optimization model

1. Open **QUBO Lab**, choose **Triangle Max-Cut**, and click **Run QUBO benchmark**. The independently enumerated minimum is −2 (negative maximum cut). All five rows come from executed solvers on that matrix.
2. Change `Q 0 0` from −2 to −3. The existing result stays tied to its saved run and is marked stale; the live coupling graph explicitly reflects the current setup. Run again: the exact minimum is now −3.
3. Choose **One-hot assignment**. The encoded objective is `A(Σxᵢ−1)²−3x₀−2x₁−x₂`. With A=4 the minimum selects only the highest reward. Lower penalties can favor violating assignments; the generic solver reports encoded energy, not separately verified constraint feasibility.
4. Click a graph node or edge to inspect a field or coupling. Spin convention is `x=(1−z)/2`; all offsets are retained in JSON.
5. Export **Run JSON** or **Run CSV**, then reopen the run from **History**. Model-only JSON is separate from full run records. Importing a matrix without an offset uses zero, while omitted solver settings retain the current settings.

See [QUBO equations, algorithms and limits](docs/qubo-model.md) and the [current feature inventory](docs/feature-inventory.md).

## Start with physical and optical models

1. Open **Physical Quantum Lab**, choose **Rabi preset**, and click **Run Rabi experiment**. Compare the ideal, Lindblad and sampled population traces.
2. Click **Pin run for comparison**, change detuning or Tφ, and run again. Expand **Pulse and Bloch-vector channels** to inspect the drive envelope and noisy ensemble state. Each time point is a freshly prepared experiment with its own shots; it is not continuous destructive measurement of one qubit.
3. Open **Photonics Lab** and load the **MZI preset**. The balanced, lossless model at zero phase has a dark D0 port and bright D1 port. Change phase to π to exchange them; change arm transmission to study loss and visibility.
4. Read the calculated optical powers separately from the virtual meters' sample means and standard errors. Meter readings represent electronic noise, not photon counts. Negative noisy readings near a dark port do not imply negative optical power.
5. Restore either run through **History**, then use **Export JSON**, **CSV**, or **Plot SVG** to keep the executed evidence. Changing controls leaves the saved result visible and marked stale until another run completes.

See the [Rabi model and measurement conventions](docs/rabi-model.md), [classical MZI model](docs/mzi-model.md), and [V3 repository audit and implementation plan](docs/superpowers/plans/2026-11-07-physical-photonics.md) for equations, validation and scope.

## Start with the virtual computer

1. Open **Virtual Computer**, choose **Bell pair**, and click **Execute program**.
2. Step forward once: q0 has 50% probability of one, but is still pure. Step again: both local qubits have purity 0.5 and entropy 1 bit because they form an entangled pair.
3. Open **Amplitudes** or **Bloch sphere** in the inspector. The debugger shows the selected ideal snapshot; the final readout chart is always the final executed state.
4. In **Experiments**, run **Grover search** on three qubits with marked state 101 and two iterations. Ideal success is 94.53125%, versus the uniform 12.5% baseline. This is a known phase-oracle demonstration, not a claim of practical speedup.
5. Run **Quantum phase estimation** with three counting qubits and phase 0.375. The counting register should be 011. The last qubit is the eigenstate target.
6. Click **Open on virtual computer** to inspect the decomposed circuit instruction by instruction. Large circuits may exceed the debugger limit and remain runnable in Experiments instead.

See [the virtual computer manual](docs/virtual-computer.md) for the assembly grammar, state inspection, and scientific conventions.

## More experiments

1. Circuit Builder → **Bell state** → **Run circuit**. Ideal outcomes are 00 and 11 at 50% each. Either reduced Bloch vector lies at the center because that qubit alone is mixed.
2. Change readout error to 0.12 and run again. Ideal probabilities remain unchanged; noisy sampled measurements now include 01 and 10.
3. Challenges → **Cut the triangle**. Compare QAOA's best observed cut with the exhaustive optimum of 2.
4. Optimization Lab → **Knapsack**. Edit weights, values, and capacity; inspect feasible sample fraction and the capacity penalty in Research mode.
5. Open History, restore a completed run, and export its JSON. It contains the precise configuration and package versions needed to replay it.

## Mathematical conventions

**Bit ordering:** throughout the interface and exported data, the leftmost bit is q0. Qiskit's internal little-endian states and count strings are reversed at the application boundary. Item decisions precede slack qubits for knapsack. Rotation angles are radians.

**Max-Cut:** maximize `Σ w_ij (x_i + x_j - 2 x_i x_j)` for binary x. QUBO energy is the negative cut, minimized by QAOA and annealing. The classical baseline uses direct XOR constraints. Duplicate edges and self-loops are rejected. Weights are positive integers.

**Knapsack:** maximize `Σ v_i x_i` subject to `Σ w_i x_i ≤ C`. Quantum/annealing energy is:

```
E(x,s) = -Σ v_i x_i + A(Σ w_i x_i + Σ 2^k s_k - C)^2
A = Σ v_i + 1
k = 0, ..., floor(log2(C))
```

Any feasible item set can encode its unused capacity in slack. Integer inputs ensure an equality violation of at least one costs more than all possible item rewards. A sampled assignment is validated against the **original item capacity constraint**; feasible item choices are retained even if their sampled slack is not canonical. Best-sample selection uses only observed candidates and never substitutes the exact answer.

**Problem-specific QAOA (Max-Cut/knapsack):** start in uniform superposition, alternate `exp(-i γ C / scale)` with `RX(2β)` on each wire. `scale = max(max|E(x)|, 1)`. SciPy COBYLA minimizes the exact expectation with 2p parameters. Configuration requires at least `2p+2` evaluations so SciPy cannot silently raise the budget. The best evaluated parameters are sampled with a seeded multinomial draw. This is a real gate-based statevector simulation with analytical training expectations, not hardware execution. Reported depth `1+2p` treats dense diagonal cost evolution as one logical operation; **it is not native decomposed hardware depth**. Dense diagonal simulation is intentionally limited to tiny instances.

**Gate-based noise:** the circuit builder, virtual computer and general experiments display the **ideal pre-measurement** amplitudes and state diagnostics; sampled readouts use the selected noise. Histograms are Aer samples with the selected noise. Gate depolarization is the channel `ρ → (1-λ)ρ + λ I/d` on the affected gate's qubits. Readout error independently flips a detected bit. M gates mark terminal readout; the backend measures every qubit at the end, including circuits without explicit M. Mid-circuit measurements and feedback are not implemented.

**Physical and optical noise:** the Physical Quantum Lab's Bloch vectors and density matrix describe its **noisy Lindblad ensemble**, with a separate ideal reference. Its readouts use binomial shots independently at each time. The Photonics Lab evolves classical coherent fields and adds independent Gaussian electronic noise only to repeated meter readings; those readings do not change optical propagation. Neither model uses the circuit builder's gate/readout noise settings. Frequencies are MHz (cycles/µs), times are µs, optical powers are mW, wavelengths are nm, optical path differences are µm, and phases are radians.

**Problem-specific comparisons:** quality is best observed feasible objective / independently enumerated optimum. CP-SAT gets one CPU worker and up to five seconds. Annealing uses 200 sweeps and at most 1024 reads; QAOA uses its configured measurement shots and objective-call budget. These operations have different costs. Repetitions rerun QAOA and annealing with `(seed + repetition_index) % 2**31`; the deterministic classical reference is solved once. Timings measure the actual solver/simulator work, excluding worker startup and library import time. No simulated timing is a prediction of QPU execution time. One tiny experiment does not establish quantum advantage.

**Generic QUBO QAOA:** uses the equivalent Ising model with RZ, IsingZZ and RX gates; its normalization excludes the constant offset. Its logical depth is the critical path of those gates. All solvers minimize the same submitted energy, and the gap is energy minus exact minimum. An energy ratio is not meaningful for arbitrary negative/zero optima. QAOA/Ocean initialization is recorded separately from optimization/sampling work, and retained in JSON/CSV and the run record. See [the separate model conventions](docs/qubo-model.md); the two workspaces have different documented cost encodings and depth definitions.

## Resource configuration

Set environment variables before launching:

| Variable | Default | Enforced range |
| --- | --- | --- |
| `QF_MAX_QUBITS` | 12 | 2–12 |
| `QF_MAX_SHOTS` | 8192 | 128–65536 |
| `QF_TIMEOUT_SECONDS` | 45 | 1–120 |
| `QF_MEMORY_MB` | 1024 | 128–2048 MiB worker RSS |

The watchdog checks worker RSS and wall time every 50 ms. RSS limits are reactive, not an OS address-space reservation; a brief allocation may exceed the threshold before termination. State-space caps prevent large circuit allocations. Aer is additionally capped at 256 MiB and one thread. Numerical workers request one BLAS/OpenMP thread. Concurrency is intentionally fixed at one to protect the laptop. The UI uses conservative default parameter ranges; customized lower backend limits produce validation feedback.

SQLite is in `data/experiments.sqlite3`. The history list shows the latest 200 experiments; older records remain in SQLite and can be retrieved by known ID. Saved circuit list shows the latest 100 entries. Schema and inputs are validated before execution. The app is designed for one trusted local user and one server process; do not expose it through a public reverse proxy.

## Development and checks

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
npm --prefix frontend run build
```

For frontend hot reload, start the backend on port 8777 and run `npm --prefix frontend run dev`; Vite runs on port 5178 and proxies `/api`.

Browser checks (against the running production app):

```sh
npm --prefix frontend run test:ui
```

The checked-in Playwright config uses the installed Google Chrome app on macOS. On another platform, remove `launchOptions.executablePath` and install Playwright Chromium. Tests execute real simulations and create actual local experiment records. Coverage includes Bell-state execution/save, Max-Cut comparison/export, knapsack/history, comma editing, terminal-measurement validation, and desktop/mobile rendering. The v0.3 checks add physical-lab execution/comparison/export, optical phase and meter workflows, incomplete-bench validation and responsive workbenches. The v0.4 checks add real QUBO benchmarking, matrix edits, CSV download, history restoration, JSON validation, Ising inspection and responsive layout. Current verification is recorded in the [Quantum Forge implementation plan](docs/superpowers/plans/2026-11-07-quantum-forge-qubo.md). The current FastAPI/Starlette test client emits a deprecation warning about its httpx adapter.

## Later phases

The next master-roadmap milestone is **reproducible parameter sweeps and multi-run benchmark reports** (Phase 3). Single-photon/Hong–Ou–Mandel interference and Ramsey pulse sequences remain planned scientific extensions; neither is implemented in v0.4. Arbitrary optical networks, quantum photonics, FDTD, multilevel device/cavity models, quantum ML, train/validation/test comparisons, quantum error correction, dynamic measurement/feed-forward, satellite scheduling, routing, supplier selection, and a generative research assistant also remain planned. Grover, QFT, phase estimation, VQE, the virtual computer, two-level Rabi evolution and classical MZI optics are implemented. Hardware access is not connected. All future quantum-provider execution must be explicit, opt-in, and separately configured. No existing Orbital Forge or ChainMind project is modified.

See [compatibility and primary references](docs/compatibility.md), the preserved [current master request](docs/requirements/quantum-forge-master.md), [feature inventory](docs/feature-inventory.md), and [delivery plan](docs/superpowers/plans/2026-11-07-quantum-forge-qubo.md). Earlier [V3 requirements](docs/requirements/platform-v3.md) are retained for context.
