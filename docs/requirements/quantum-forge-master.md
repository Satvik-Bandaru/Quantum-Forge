# QUANTUM FORGE — MASTER CODEX DEVELOPMENT PROMPT

## ROLE AND MISSION

You are the principal quantum software engineer, quantum computing researcher, AI systems architect, scientific simulation developer, and full-stack technical lead for my existing project:

**QUANTUM FORGE — Advanced Quantum Computing, Quantum AI, Optimization, Photonics & Scientific Research Platform**

Your objective is to transform Quantum Forge into a powerful, interactive, scientifically credible quantum computing laboratory suitable for:

- Learning quantum computing from beginner to advanced levels
- Building and simulating quantum circuits
- Researching quantum algorithms and quantum AI
- Comparing quantum and classical optimization
- Exploring quantum computing hardware and noise
- Studying quantum communication and networks
- Running quantum chemistry experiments
- Simulating quantum photonics
- Solving satellite and spacecraft optimization problems
- Experimenting with supply-chain and logistics optimization
- Developing reproducible scientific research projects
- Preparing for future integration with actual quantum hardware

This should eventually become a sophisticated research and engineering platform, not merely a quantum-themed interface.

**CRITICAL: WORK IN MY EXISTING PROJECT. DO NOT CREATE AN UNRELATED APPLICATION OR REBUILD THE PROJECT FROM SCRATCH.**

---

# PART 1 — REPOSITORY AUDIT AND ARCHITECTURE

Before implementing anything:

1. Examine the entire repository structure.
2. Identify the existing frontend, backend, simulation engines, frameworks, libraries, and tests.
3. Determine which quantum features are already functional.
4. Identify incomplete or misleading features.
5. Check whether circuit execution produces mathematically correct results.
6. Identify existing quantum AI, optimization, hardware, or visualization modules.
7. Check performance and computational requirements.
8. Review the current user interface.
9. Review API boundaries, dependencies, and security.
10. Create an implementation roadmap based on the actual state of the repository.

Preserve working features and avoid unnecessary framework migrations.

Reuse the current architecture unless there is a strong technical justification for changing it.

Do not assume any feature exists merely because a navigation tab or button exists.

Create a feature inventory with these statuses:

- Functional and tested
- Implemented but unverified
- Partially implemented
- UI-only
- Missing
- Blocked by external infrastructure

Then begin implementation rather than stopping after a planning report.

---

# PART 2 — QUANTUM CIRCUIT STUDIO

Build an interactive quantum circuit development environment.

## Core capabilities

Support:

- Quantum gate placement and editing
- Configurable numbers of qubits
- Single-qubit gates: X, Y, Z, H, S, T and rotations
- Controlled gates: CX, CY, CZ and controlled rotations where supported
- SWAP gates
- Multi-qubit operations where supported
- Measurement
- Circuit reset
- Parameterized gates
- Circuit depth calculation
- Gate counts
- Circuit validation
- Circuit import/export

Use a real quantum simulator.

Preferred libraries when compatible with the existing stack:

- Qiskit
- Qiskit Aer
- PennyLane
- Appropriate numerical Python libraries

## Interactive visualization

Add:

- Circuit diagram editor
- Bloch sphere visualizations
- Measurement probability charts
- Statevector viewer
- Density-matrix viewer
- Entanglement indicators with mathematically justified definitions
- Quantum state evolution visualization
- Step-by-step execution
- Optional phase and amplitude representations

Visualizations must reflect computed quantum states rather than fabricated values.

For mixed states, do not incorrectly describe the Bloch vector as a pure quantum state.

## Built-in experiments

Implement validated demonstrations of:

- Superposition
- Bell-state entanglement
- Quantum teleportation
- Superdense coding
- Deutsch-Jozsa algorithm
- Bernstein-Vazirani algorithm
- Grover search
- Quantum Fourier transform
- Small demonstrations of phase estimation
- Foundational variational circuits

Include descriptions, circuits, expected outcomes, and numerical validation.

Do not substitute a scripted animation for a genuinely computed experiment.

---

# PART 3 — QUANTUM ALGORITHM BATTLE ARENA

Build an interactive benchmarking center comparing quantum, quantum-inspired, and classical algorithms on the same well-defined problems.

## Algorithms

Support feasible implementations of:

### Quantum and hybrid

- QAOA
- VQE
- Variational quantum circuits
- Parameterized quantum optimization
- Small quantum search demonstrations

### Quantum-inspired

- Simulated annealing
- QUBO heuristic solvers
- Other validated heuristic methods where appropriate

### Classical

- Exhaustive search for sufficiently small problems
- Greedy optimization
- Local search
- Mixed-integer optimization
- OR-Tools CP-SAT
- Appropriate problem-specific algorithms

Use the same objective functions, constraints, and instances for valid comparisons.

Do not imply that simulated annealing is itself a quantum algorithm.

## Benchmark measurements

Measure:

- Objective value
- Solution feasibility
- Constraint violations
- Wall-clock runtime
- Solver initialization time, where relevant
- Number of evaluations
- Optimization iterations
- Memory usage where measurable
- Performance across random seeds
- Solution-quality gaps relative to known optima or defensible reference solutions

Where meaningful, distinguish simulator overhead, classical optimization overhead, sampling effort, and actual quantum execution time.

Never assume quantum methods are superior.

Explicitly report situations in which classical optimization wins.

---

# PART 4 — QUBO AND ISING MODELING LABORATORY

Create a visual optimization formulation tool.

Users should be able to:

1. Define decision variables.
2. Define an objective function.
3. Add constraints.
4. Convert suitable problems into QUBO representations.
5. Inspect QUBO coefficient matrices.
6. Visualize Ising couplings.
7. Adjust penalty parameters.
8. Solve a problem using different algorithms.
9. Compare results.
10. Export model definitions and solutions.

Support binary optimization initially.

Clearly explain transformations and identify when a constraint encoding is approximate or dependent on penalty selection.

Add small, verifiable examples such as:

- Max-Cut
- Knapsack
- Scheduling
- Assignment
- Portfolio-style allocation with explicit assumptions
- Traveling salesperson toy problems
- Resource allocation

---

# PART 5 — QUANTUM NOISE AND ERROR-CORRECTION LAB

Build a scientific workspace for exploring quantum noise and error mitigation.

## Noise simulation

Support:

- Depolarizing noise
- Amplitude damping
- Phase damping
- Readout errors
- Gate-error models
- Hardware-inspired connectivity restrictions
- Noisy state evolution

Where appropriate, use density-matrix or trajectory-based simulation rather than pure-state simulation.

## Error correction

Add educational and computational demonstrations of:

- Three-qubit bit-flip code
- Three-qubit phase-flip code
- Quantum error syndromes
- Logical versus physical qubits
- Basic stabilizer concepts
- Small surface-code demonstrations when feasible

## Error mitigation

Explore:

- Readout-error mitigation
- Zero-noise extrapolation where appropriate
- Measurement correction techniques
- Noise-aware compilation

Show how changes influence measurable output distributions.

Avoid claiming that a technique provides fault-tolerant quantum computing unless it actually satisfies the relevant requirements.

---

# PART 6 — QUANTUM AI AND MACHINE LEARNING LAB

Build a hybrid quantum-classical machine learning environment.

Support:

- Variational quantum classifiers
- Quantum feature maps
- Small quantum kernel demonstrations
- Hybrid neural-network experiments
- Trainable quantum circuits
- Gradient-based parameter optimization
- Quantum embedding experiments

Prefer PennyLane or another suitable maintained framework.

## Experiment interface

Allow users to choose:

- Dataset
- Quantum circuit
- Number of qubits
- Circuit depth
- Feature map
- Classical optimizer
- Learning rate
- Training iterations
- Noise settings
- Random seed

Display:

- Training and validation curves
- Evaluation metrics
- Confusion matrices where appropriate
- Parameter evolution
- Training time
- Generalization gaps
- Comparison against classical models

Always include meaningful classical baselines.

Use train/validation/test separation and explicitly guard against data leakage.

Clearly label toy datasets and small simulations.

Do not present quantum machine learning as generally outperforming classical machine learning.

---

# PART 7 — QUANTUM PHOTONICS STUDIO

Create a scientific photonics and optical quantum simulation module.

## Components

Support conceptual and mathematically grounded simulations of:

- Beam splitters
- Phase shifters
- Interferometers
- Optical modes
- Single-photon states
- Two-photon interference
- Hong-Ou-Mandel interference
- Photonic entanglement
- Photon detection
- Optical loss and detector inefficiency

Use appropriate libraries such as Strawberry Fields or a compatible optical simulation framework if practical.

Build visual diagrams showing optical paths and experimentally relevant probabilities.

Distinguish single-photon behavior from classical wave-optics approximations.

Allow users to adjust phase, transmissivity, reflectivity, and loss parameters.

All plots must be connected to mathematical computations.

Start with a validated Mach-Zehnder interferometer experiment before attempting complex multi-photon systems.

---

# PART 8 — QUANTUM NETWORKS AND COMMUNICATION

Build a network research module covering:

- Quantum teleportation
- Entanglement distribution
- Entanglement swapping
- Quantum repeaters at a simplified conceptual level
- Quantum key distribution demonstrations
- Noisy quantum channels
- Basic entanglement fidelity
- Quantum network topology
- Channel-loss effects

Create interactive network diagrams with configurable nodes and channels.

Allow users to test small network scenarios and compare theoretical and simulated outcomes.

Distinguish idealized protocols from deployable secure communication systems.

Do not claim that an educational QKD demonstration constitutes a production-secure cryptographic system.

---

# PART 9 — QUANTUM CHEMISTRY AND MATERIALS

Build an introductory computational quantum chemistry laboratory.

Support:

- Molecular Hamiltonians
- Small-molecule energy calculations
- VQE-based energy estimation
- Classical reference solutions where feasible
- Molecular orbital and basis-set explanations
- Parameterized ansatz selection
- Energy convergence charts

Begin with small, computationally manageable systems such as H2.

Compare results against exact diagonalization or another suitable reference when possible.

Document approximation choices and physical units.

Do not claim chemical accuracy without checking the relevant error threshold.

---

# PART 10 — SPACE TECHNOLOGY AND QUANTUM OPTIMIZATION

This module is strategically important because Quantum Forge may eventually support my spacecraft simulation and autonomy projects.

Develop a **Space Optimization Laboratory**.

## Applications

Explore:

- Satellite task scheduling
- Ground-station contact scheduling
- Spacecraft power-budget allocation
- Observation task selection
- Communication-window allocation
- Multi-satellite resource assignment
- Small mission-planning optimization problems
- Constellation scheduling
- Autonomous spacecraft resource planning

## Architecture

Allow an optimization problem to be defined using synthetic or validated mission data.

Use classical algorithms as the baseline.

Where mathematically justified, formulate quantum-compatible optimization versions.

Compare classical, quantum-inspired, and quantum algorithms.

Use realistic constraints such as:

- Available power
- Observation time windows
- Ground-station availability
- Priority values
- Storage capacity
- Resource conflicts
- Communication restrictions

Keep quantum optimization separate from spacecraft physics simulation.

Do not claim to simulate realistic orbital mechanics or spacecraft hardware unless appropriate validated models are implemented.

Build interfaces that could later exchange optimization tasks with my separate spacecraft autonomy platform through documented APIs.

---

# PART 11 — SUPPLY CHAIN AND LOGISTICS OPTIMIZATION

Build a Quantum Forge module that could eventually connect with ChainMind.

Applications:

- Supplier assignment
- Purchase-order allocation
- Warehouse task scheduling
- Inventory optimization
- Fleet assignment
- Delivery-route toy problems
- Production scheduling
- Shipment allocation
- Resource balancing

Convert suitable small problems into binary or constrained optimization formulations.

Compare classical optimization against quantum-compatible formulations.

Develop reusable APIs so ChainMind could submit optimization jobs and retrieve results.

Do not create direct dependencies on ChainMind unless the repository already includes them or authorized integration details are available.

Document all assumptions and constraints.

---

# PART 12 — VIRTUAL QUANTUM HARDWARE LAB

Create a simulated quantum hardware engineering environment.

Allow users to select conceptual or documented hardware profiles with:

- Qubit count
- Connectivity graph
- Supported native gates
- Gate durations
- Noise characteristics
- Readout fidelity
- Circuit transpilation constraints

Provide:

- Hardware topology visualization
- Circuit mapping
- Transpilation comparisons
- Gate-count comparisons
- Estimated circuit depth
- Noise-aware execution
- Basic hardware calibration concepts

When supporting actual quantum cloud providers, use their official supported SDKs.

Real hardware execution must be optional and require an explicit connection, credentials, permission, and clear information about potential charges.

Never fabricate hardware job IDs, real quantum measurements, or provider connections.

---

# PART 13 — AI QUANTUM RESEARCH ASSISTANT

Build an intelligent assistant inside Quantum Forge.

Its responsibilities:

- Explain quantum concepts
- Generate circuit examples
- Suggest experiments
- Explain algorithm limitations
- Help debug quantum code
- Analyze recorded experimental results
- Generate benchmark plans
- Explain quantum optimization models
- Suggest parameter sweeps
- Identify possible computational bottlenecks
- Help users learn quantum programming

Where supported, let the assistant request simulations through explicitly permitted, validated application tools.

All tool calls must be controlled by a trusted execution layer with appropriate authorization.

The assistant must distinguish:

- Theoretical predictions
- Simulated results
- Actual hardware measurements
- Hypotheses
- Unverified claims

Never invent experiments or claim to have performed calculations that were not executed.

Do not allow untrusted natural-language inputs to execute arbitrary code or operating-system commands without a controlled, explicitly authorized sandbox.

---

# PART 14 — QUANTUM ACADEMY AND PERSONAL LEARNING SYSTEM

Build an educational laboratory with progressive difficulty.

## Learning tracks

1. Linear algebra foundations
2. Complex numbers and probability amplitudes
3. Quantum mechanics fundamentals
4. Qubits and quantum gates
5. Quantum circuits
6. Entanglement and measurement
7. Quantum algorithms
8. Quantum noise
9. Error correction
10. Variational algorithms
11. Quantum machine learning
12. Quantum optimization
13. Quantum communication
14. Quantum photonics
15. Quantum hardware engineering
16. Quantum computing for spacecraft and logistics applications

Add interactive exercises that use actual simulations.

Include:

- Step-by-step explanations
- Coding exercises
- Practice questions
- Experiment assignments
- Progress tracking if persistence exists
- Difficulty levels
- Research challenges
- Optional project-based learning

Teach concepts accurately without making everything unnecessarily theoretical.

When possible, explain complex concepts using diagrams, calculations, and interactive demonstrations.

---

# PART 15 — RESEARCH EXPERIMENT CENTER

Build a central reproducible experiment management environment.

Users should be able to:

- Create and name experiments
- Save configurations
- Select algorithms
- Set random seeds
- Choose simulation backends
- Run parameter sweeps
- Compare multiple experiment runs
- View historical results
- Export results
- Reproduce earlier simulations
- Create research summaries

Every run should record available metadata including:

- Experiment ID
- Timestamp
- Algorithm
- Software versions
- Backend
- Dataset or problem-instance version
- Qubit count
- Circuit depth
- Noise model
- Random seed
- Solver settings
- Objective function
- Constraints
- Actual outputs
- Runtime
- Errors and warnings

Export standardized JSON and CSV.

Generate reports that clearly distinguish experimental observations from interpretations.

Do not fabricate references, statistical significance, or measured outcomes.

---

# PART 16 — ADVANCED SCIENTIFIC VISUALIZATION

Make Quantum Forge visually impressive without sacrificing accuracy.

Add visualizations such as:

- Bloch spheres
- Quantum circuit diagrams
- Complex-amplitude displays
- Probability histograms
- Density matrices
- Quantum hardware connectivity graphs
- Optimization convergence plots
- QUBO matrices
- Ising interaction graphs
- Quantum network diagrams
- Photonic circuit diagrams
- Parameter-landscape plots
- Benchmark comparisons
- Learning curves
- Noise sensitivity graphs

Support interactive controls, zooming, and data inspection where useful.

Every data visualization must show values derived from the actual mathematical model or executed experiment.

If a feature is conceptual rather than computed, label it clearly.

Avoid fake dashboards showing invented performance statistics.

---

# PART 17 — PERFORMANCE AND HARDWARE OPTIMIZATION

Quantum Forge should work efficiently on a modern Apple Silicon Mac, including a configuration with approximately 16 GB of unified memory.

Requirements:

- Optimize frontend rendering.
- Use small experiments by default.
- Prevent runaway simulation jobs.
- Implement configurable job limits.
- Estimate simulation resource requirements.
- Show progress and cancellation controls for long-running tasks.
- Cache valid repeated calculations where appropriate.
- Avoid blocking the UI.
- Release unused simulation resources.
- Support CPU execution.
- Use hardware acceleration only when it is compatible and beneficial.

Remember that exact statevector simulation grows exponentially with qubit count.

Do not advertise support for large ideal quantum systems simply because the interface allows a large qubit-count input.

Use clear resource warnings and graceful fallback behavior.

Advanced simulations may be offered through optional remote compute, but local operation should remain useful without paid infrastructure.

---

# PART 18 — SOFTWARE ARCHITECTURE

Preserve the existing stack when possible.

Preferred scientific components where compatible:

- Python for computational backends
- NumPy and SciPy
- Qiskit and Qiskit Aer
- PennyLane
- D-Wave Ocean
- OR-Tools
- Suitable quantum chemistry libraries
- Suitable photonic simulation libraries

Use existing frontend technologies rather than forcing a migration.

Keep separate modules for:

- Circuit execution
- Quantum algorithms
- Quantum AI
- Optimization
- Noise and error correction
- Quantum communication
- Photonics
- Chemistry
- Space applications
- Supply-chain applications
- Visualization
- Experiment management
- Reporting
- AI assistance

Provide versioned, documented APIs for modules that need to interact.

Make heavyweight dependencies optional when possible.

Do not require users to install every scientific library just to run a basic Bell-state simulation.

Use explicit dependency versions or compatible ranges, test them, and document environment setup.

---

# PART 19 — TESTING AND SCIENTIFIC VALIDATION

Build a real automated testing suite.

Required validation areas:

## Quantum circuits

- Normalization of quantum states
- Correct gate matrices
- Correct measurement probabilities
- Valid physical density matrices
- Bell-state correlations
- Correct teleportation behavior under specified conditions

## Optimization

- Objective evaluation
- Constraint enforcement
- Correct mapping of decision variables
- QUBO objective equivalence
- Small-problem agreement with exhaustive search
- Reproducible random-seed behavior

## Noise

- Valid noise-channel behavior
- Correct probability normalization
- Physical state validity
- Expected behavior of known test cases

## Quantum AI

- Correct dataset splitting
- Reproducible training configurations
- Valid loss calculation
- Baseline comparisons

## Chemistry and photonics

- Known analytical or high-confidence reference cases
- Physical conservation laws where applicable
- Appropriate numerical tolerances

## Engineering

- API validation
- Error handling
- Export consistency
- Performance boundaries
- Dependency availability
- Basic security checks

Use unit tests, integration tests, and benchmark tests.

If a test fails, report the failure instead of adjusting expected results to make the project appear correct.

---

# PART 20 — SCIENTIFIC INTEGRITY

These rules apply across the entire platform.

1. Never fabricate quantum measurements.
2. Never fabricate hardware execution.
3. Never invent performance benchmarks.
4. Never claim quantum advantage without appropriate evidence.
5. Never equate quantum-inspired optimization with demonstrated quantum speedup.
6. Never confuse simulation with experimental hardware measurements.
7. Never claim a system is scientifically validated without testing.
8. Never display fake experimental histories.
9. Always distinguish proposed functionality from implemented functionality.
10. Always report limitations and computational assumptions.
11. Clearly identify toy demonstrations.
12. Provide reproducibility instructions for experimental claims.

Scientific credibility is more important than visual complexity.

---

# PART 21 — FUTURE INTEGRATIONS

Design modular interfaces for potential future integration with:

- Spacecraft autonomy and mission simulation systems
- ChainMind supply-chain optimization
- NexusLab AI reliability testing
- External quantum hardware services
- Scientific notebooks
- GitHub-based research workflows
- Cloud computing infrastructure
- Unity-based educational visualizations

Do not create fictional connections.

Implement shared APIs only where justified by working use cases.

Use authenticated, versioned interfaces and explicit authorization for external actions.

---

# PART 22 — IMPLEMENTATION ROADMAP

Do not attempt to build every feature simultaneously.

Use the following implementation order, adjusting for functionality already present.

## PHASE 1 — Scientific foundation

- Audit the current project
- Fix broken or misleading features
- Implement a validated circuit simulator
- Add measurement visualization
- Build the Bell-state demonstration
- Add basic automated tests

## PHASE 2 — Quantum optimization

- Implement QUBO builder
- Implement classical baselines
- Add QAOA
- Build the Algorithm Battle Arena
- Compare actual solver outputs

## PHASE 3 — Research workflows

- Experiment history
- Reproducible configuration
- Parameter sweeps
- Benchmark exports
- Research reporting

## PHASE 4 — Advanced quantum computing

- Noise simulation
- Error-correction demonstrations
- Hardware constraints
- Transpilation analysis

## PHASE 5 — Quantum AI

- Variational quantum classifiers
- Hybrid models
- Training visualizations
- Classical baselines

## PHASE 6 — Quantum science

- Quantum communication
- Quantum networks
- Photonics
- Small quantum chemistry experiments

## PHASE 7 — Applied research

- Spacecraft scheduling
- Satellite resource optimization
- Supply-chain optimization
- Cross-platform APIs

## PHASE 8 — Educational and product maturity

- Quantum Academy
- Research assistant
- Improved UX
- Performance optimization
- Documentation
- Deployment readiness

---

# PART 23 — IMMEDIATE EXECUTION INSTRUCTIONS

Begin working in the existing repository now.

Do not respond with only a development plan.

First:

1. Inspect the existing codebase.
2. Summarize what is already functional.
3. Identify the most important technical weaknesses.
4. Preserve existing working components.
5. Select the smallest valuable end-to-end improvement.
6. Implement actual code changes.
7. Add and run automated tests.
8. Verify that the feature produces real computational results.
9. Fix errors discovered during testing.
10. Update the documentation.

Start with Phase 1 unless the repository already contains a tested scientific foundation. If Phase 1 is complete, advance to Phase 2.

Do not add dozens of placeholder features merely to make the interface look more advanced.

Work iteratively. Complete one useful, scientifically defensible vertical slice before proceeding to the next.

When a phase is complete, report:

- Files created or modified
- Features implemented
- Algorithms used
- Tests executed
- Test results
- Performance limitations
- Remaining issues
- Recommended next implementation phase

If repository access, dependencies, or external services prevent a feature from being implemented, state the blocker accurately and continue with the best available local improvement.

---

# FINAL OBJECTIVE

Build Quantum Forge into a genuine quantum computing and scientific engineering platform where users can:

**LEARN → DESIGN → SIMULATE → OPTIMIZE → BENCHMARK → ANALYZE → REPRODUCE → RESEARCH**

Quantum Forge should combine a professional interactive interface with correct scientific computation.

Its long-term purpose is to support advanced quantum computing research, quantum-classical optimization, AI, spacecraft autonomy, photonics, and future commercial applications.

The final product must be technically credible, modular, reproducible, and expandable.

**Start by inspecting and upgrading the existing project. Prioritize functioning scientific technology over appearances.**