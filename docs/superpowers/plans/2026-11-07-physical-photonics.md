# V3 Repository Audit and Immediate Implementation

## Existing project
- Standalone local directory `quantum-forge-lab`; no Git repository/history is present, so no branch or commit audit is available. Other projects are outside this change.
- React 19/TypeScript/Vite/Recharts UI, FastAPI/Pydantic backend, SQLite JSON experiment records, one spawned numerical worker with timeout/cancel/RSS watchdog.
- Working: Qiskit circuit builder, 8-qubit assembly computer/debugger, eleven quantum information/algorithm experiments, PennyLane QAOA, Max-Cut/knapsack, Ocean simulated annealing, OR-Tools and exhaustive baselines, guides/challenges, history and exports.
- Last delivered verification: 78 backend tests, 13 frontend checks; rerun baseline below. Dependencies are already installed and locked. No QuTiP, optical solver, or physical hardware integration is present.
- Limitations relevant to V3: no continuous-time open-system dynamics, no classical optical bench, no time-domain instrumentation. Existing noise is circuit gate/readout noise, not a physical device model.
- Preservation: retain current APIs/jobs/data and frontend tools. SQLite backup made at data/experiments-before-physical-photonics.sqlite3. Both full source prompts preserved in docs/requirements.

## Decisions
V3's immediate execution order is the binding next slice: Rabi two-level dynamics and classical Mach–Zehnder interferometry. Bell and QAOA acceptance tests already exist and remain regression checks. Additive modules reuse the current app; advanced Quantum AI, arbitrary optics, FDTD, bosonic optics and hardware remain explicitly planned.

Use existing NumPy/SciPy rather than adding mandatory dependencies: a constant 2×2 Hamiltonian and 4×4 Lindblad superoperator can be independently validated against analytic Rabi, relaxation and dephasing solutions. This is an equivalently verified solver, not an assertion of QuTiP use. Classical coherent-wave matrix optics models the MZI; no photon or hardware measurement claims.

## Implementation plan
- [x] Fresh baseline, dependencies and backup/audit.
- [x] Physics engine: MHz/us units, drive/detuning/pulse duration/phase, ground/excited/plus initial conditions, optional T1 and pure-dephasing Tphi, exact density evolution, ideal/noisy traces and finite-shot independent measurements with uncertainty. Scientific invariant and analytic reference tests.
- [x] Photonics engine: specified coherent source, two lossless splitters, lossy paths, wavelength/path phase, phase shifter and power meters, phase sweep, exact visibility, power conservation, seeded repeated electronic meter readings and uncertainty. Separate classical model labels and tests.
- [x] Integrate both job kinds, validation, history restoration and scientific CSV rows. Reuse process limits and cancel controls.
- [x] Add physical lab equipment diagram, oscilloscope-like population/pulse traces, density/Bloch inspection, reproducibility details. Add optical component library and validated preset assembly bench, optical properties, phase sweep and power readouts. Both support pinning a prior run for comparison.
- [x] Update research overview, curriculum/status, user docs and version, without marking later modules operational.
- [x] Run full tests/build, real browser workflows and responsive screenshots; independent scientific/integration review and fixes. Leave the app running locally.

## Review focus
T1/Tphi conventions and 2π unit conversions; sampling vs deterministic evolution; trace/PSD and tiny numerical residue; detector noise vs optical power; exact visibility for zero-signal ports; phase accounting and energy conservation; old history/export compatibility; no uncontrolled jobs or secrets.

## Completion evidence
- Added two independent engines with 91 analytic/invariant/model tests. Full backend suite: 173 passed, including all prior acceptance tests and API/history/CSV tests.
- Browser coverage exercises changing Rabi pulse amplitude, pinned comparisons, actual JSON/CSV/SVG downloads, complete optical bench assembly/validation, phase0/π port exchange, history restoration and mobile chart reflow. Full suite: 16 frontend checks.
- Production TypeScript/Vite build passed; pip check found no broken requirements; no dependencies added.
- Independent review verified scientific assumptions, uncertainty, endianness-independent physics/optical models and export provenance. Follow-up browser testing found pre-existing worker-exit result-loss races; both now have red-to-green regressions and corrected pipe-drain ordering.
- App running on loopback port 8777. The first restart approval review timed out; its permitted retry succeeded. No approval or execution blocker remains.
- Desktop/mobile screenshots are in docs/screenshots. Original prompt files are archived in docs/requirements; prior run database was backed up before implementation.
- Later V3 modules remain planned. Next coherent milestones: Ramsey/spin echo and separate single-photon/HOM quantum-optics models.
