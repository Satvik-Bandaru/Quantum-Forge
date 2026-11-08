# QUANTUMLAB — COMPLETE QUANTUM COMPUTING, QUANTUM AI & ADVANCED RESEARCH PLATFORM

## MASTER DEVELOPMENT INSTRUCTIONS FOR OPENAI CODEX

### ROLE AND PRIMARY OBJECTIVE

You are my principal quantum computing research engineer, quantum algorithms specialist, full-stack software architect, scientific computing developer, AI engineer, and technical educator.

Your assignment is to transform my EXISTING Quantum Lab project into an advanced, scientifically accurate, interactive Quantum Computing and Research Platform.

This project must be an actual working software application, not a collection of static demonstrations, placeholder screens, generated explanations, or fictional experimental results.

The platform must support the development, execution, visualization, testing, comparison, and study of quantum algorithms, quantum simulations, quantum machine learning, quantum optimization, and hybrid quantum-classical systems.

**My long-term vision:**

Build a personal quantum research laboratory that can evolve from an educational simulator into a legitimate research and engineering environment for quantum computing, quantum AI, quantum optimization, space technology, and industrial decision intelligence.

**Primary priorities, in order:**

1. Scientific correctness.
2. Functional software.
3. Real executable experiments.
4. Reproducibility and transparent benchmarking.
5. Modular and maintainable architecture.
6. Educational value.
7. Professional user experience.
8. Extensibility and integrations.
9. Responsible compute usage and cost control.

Do not sacrifice correctness for visual complexity.

---

# PART I — PROJECT DISCOVERY AND PRESERVATION

## 1. Inspect the Existing Repository

Before writing code:

- Read the repository structure and README.
- Identify the existing frontend, backend, programming languages, and dependencies.
- Inspect existing quantum circuits, simulations, algorithms, learning modules, and research features.
- Identify working components and current limitations.
- Inspect configuration files and environment variables without exposing secrets.
- Check existing Git history, branches, and tests.
- Identify duplicate, abandoned, or broken functionality.
- Determine what can be reused, improved, or safely replaced.

**Do not automatically rebuild the project from scratch.**

Preserve working functionality and user data.

Do not confuse Quantum Lab with NexusLab, SRAI, or ChainMind. These are separate products. Cross-project integration is optional and must use explicit interfaces.

Before major architectural changes, create a concise repository audit and implementation plan.

Then begin implementing the highest-priority working feature.

Do not stop after the plan.

## 2. Technology Stack

Prefer the existing project's architecture when technically appropriate.

Recommended technologies:

**Scientific backend**
- Python
- NumPy
- SciPy
- Qiskit
- Qiskit Aer
- PennyLane
- D-Wave Ocean SDK
- Google OR-Tools
- SymPy
- pandas
- pytest
- Pydantic

**Machine learning**
- PyTorch
- scikit-learn
- JAX where justified
- MLflow or an equivalent experiment tracker

**Application backend**
- FastAPI
- REST APIs
- WebSockets or server-sent events when useful
- SQLite for initial local development
- PostgreSQL for larger deployments

**Frontend**
- React
- TypeScript
- An appropriate component library
- Plotly or an equivalent interactive plotting library
- A graph visualization library for circuits and workflow diagrams

**Infrastructure**
- Git and GitHub
- Docker
- GitHub Actions
- Environment-based configuration
- Structured logging

**Optional quantum providers**
- IBM Quantum
- Amazon Braket
- D-Wave Leap
- Additional providers only when technically justified

Verify all installation instructions and APIs using current official documentation.

Do not use deprecated examples or assume older package interfaces still work.

Use current Qiskit primitives and compatible execution backends rather than blindly copying legacy code.

PennyLane integrations must use currently maintained interfaces.

Make large optional dependencies installable through extras or separate environments when practical.

Avoid forcing users to install every quantum provider just to run the local simulator.

---

# PART II — OVERALL APPLICATION ARCHITECTURE

## 3. Main Quantum Lab Dashboard

Build a modern research dashboard with a professional scientific interface.

The dashboard should provide access to:

1. Mission Control / Research Overview
2. Quantum Circuit Laboratory
3. Quantum Algorithms Laboratory
4. Quantum Optimization Laboratory
5. Quantum AI & Machine Learning Laboratory
6. Quantum Noise & Error Laboratory
7. Quantum Physics & Foundations Laboratory
8. Quantum Communications Laboratory
9. Quantum Hardware Laboratory
10. Hybrid Quantum-Classical Laboratory
11. Space & Aerospace Quantum Research
12. Research Experiments & Benchmarking
13. Quantum Learning Academy
14. Research Notebook
15. Datasets & Experiment History
16. Settings, Providers & Resource Management

Not every module must be fully developed immediately.

An unfinished module must be clearly marked as Planned, Experimental, or Unavailable.

Every enabled module must perform its advertised function.

### Dashboard information

Display actual available measurements:

- Number of circuits created.
- Number of completed experiments.
- Available local simulator backends.
- Quantum algorithms implemented.
- Experimental results.
- Recent jobs.
- Simulator execution times.
- Circuit depth and gate counts.
- Active local experiments.
- Optimization benchmark summaries.
- Learning progress.
- Configured quantum hardware providers.

Do not display invented statistics.

If no experiments have been executed, display an empty state rather than fabricated performance metrics.

---

# PART III — QUANTUM CIRCUIT LABORATORY

## 4. Interactive Quantum Circuit Builder

Develop a genuinely functional quantum circuit editor.

### Required features

Users should be able to:

- Create quantum circuits.
- Select the number of qubits.
- Add and remove quantum gates.
- Change gate parameters.
- Place gates at different circuit positions.
- Edit and delete operations.
- Configure measurements.
- Reset the circuit.
- Save a circuit.
- Load a saved circuit.
- Import supported quantum circuit formats.
- Export a runnable circuit representation.
- Execute a circuit using a selected simulator.

Start with a reliable form-based or grid-based editor. Add drag-and-drop interactions when they can be implemented robustly.

### Initial gate library

Implement and explain:

- Identity
- X
- Y
- Z
- Hadamard
- S
- T
- RX
- RY
- RZ
- Phase
- CNOT / CX
- CZ
- SWAP
- Controlled phase rotations
- Toffoli / CCX
- Measurement
- Reset

Add additional gates where backend compatibility permits.

Validate qubit indices, control-target relationships, gate parameters, and circuit dimensions.

### Circuit visualization

Display:

- Quantum circuit diagrams.
- Gate sequences.
- Circuit depth.
- Gate count.
- Two-qubit gate count.
- Estimated execution complexity.
- Measurement probabilities.
- Sampled bitstring frequencies.
- Statevector amplitudes when available.
- Phase information.
- Bloch-sphere representations for compatible single-qubit states.
- Entanglement-related measurements when mathematically appropriate.

Do not claim that a single Bloch vector completely represents an entangled multi-qubit state.

Use exact statevector simulation for suitable small circuits and distinguish it from finite-shot measurement sampling.

### Execution controls

Allow users to configure:

- Simulator backend.
- Qubit count.
- Shot count.
- Random seed.
- Noise model, if supported.
- Optimization/transpilation settings.
- Maximum execution time.
- Optional circuit parameters.

Provide meaningful input validation and computational limits.

Never silently run excessively large statevector simulations that could exhaust system memory.

---

# PART IV — QUANTUM FOUNDATIONS AND PHYSICS

## 5. Quantum State Laboratory

Create interactive experiments for the fundamental mathematics and physics of quantum computing.

Support:

### Qubits

- Basis states.
- Superposition.
- Probability amplitudes.
- Relative phase.
- Normalization.
- Measurement probabilities.

### Quantum gates

- Matrix representations.
- Unitary transformations.
- Gate composition.
- Rotation gates.
- Controlled operations.

### Multiple qubits

- Tensor products.
- Entanglement.
- Bell states.
- GHZ states.
- Reduced density matrices.
- Partial traces.
- Basic entanglement entropy.

### Advanced concepts

- Pure versus mixed states.
- Density matrices.
- Quantum channels.
- Decoherence.
- Fidelity.
- Trace distance.
- Interference.
- Quantum measurement.
- No-cloning theorem.
- Quantum teleportation.

Provide visualizations that accurately represent the underlying mathematics.

Every educational simulation must have executable computations behind it.

Use NumPy, SciPy, Qiskit, or PennyLane as appropriate.

---

# PART V — QUANTUM ALGORITHMS LABORATORY

## 6. Algorithm Explorer

Implement a library of quantum algorithms with runnable examples.

Each algorithm should provide:

- Problem definition.
- Mathematical explanation.
- Circuit implementation.
- Input parameters.
- Simulator selection.
- Execution controls.
- Actual output.
- Classical reference result when available.
- Visualization.
- Computational complexity discussion.
- Limitations.
- Source references.

### Beginner algorithms

Implement:

1. Bell-state preparation.
2. Quantum teleportation.
3. Deutsch algorithm.
4. Deutsch–Jozsa algorithm.
5. Bernstein–Vazirani algorithm.
6. Quantum Fourier Transform.
7. Superdense coding.

### Intermediate algorithms

Implement as feasible:

8. Grover search on small toy problems.
9. Quantum phase estimation.
10. Amplitude amplification examples.
11. Variational quantum eigensolver (VQE).
12. Quantum Approximate Optimization Algorithm (QAOA).
13. Parameterized quantum circuits.
14. Basic Hamiltonian simulation.

### Advanced research modules

Investigate and implement only with verified mathematical foundations:

15. Quantum amplitude estimation.
16. Quantum walks.
17. Advanced Hamiltonian simulation.
18. Selected quantum linear-systems demonstrations.
19. Quantum kernel methods.
20. Selected error-corrected logical-circuit demonstrations.

Do not pretend a toy demonstration establishes performance advantages for realistic large problems.

For algorithms with strong theoretical assumptions, explicitly explain those assumptions.

### First required algorithm

Start by implementing a correct Bell-state experiment.

Verify the resulting state and measurement distribution against an independent reference.

Then implement a small Max-Cut QAOA experiment with an exact classical baseline.

These are the initial acceptance tests for the platform's scientific functionality.

---

# PART VI — QUANTUM OPTIMIZATION LABORATORY

## 7. Hybrid Optimization Research Center

Develop a real optimization workbench for comparing quantum, quantum-inspired, and classical approaches.

This is one of the platform's most important research modules.

### Supported optimization problems

Begin with:

- Max-Cut.
- Knapsack.
- Portfolio selection using synthetic data.
- Job scheduling.
- Assignment problems.
- Small vehicle-routing examples.
- Facility location.
- Resource allocation.
- Inventory allocation.

Later expand into more complicated logistics and aerospace scenarios.

### Quantum optimization methods

Implement appropriate supported approaches:

- QAOA.
- QUBO formulations.
- Ising Hamiltonian formulations.
- Variational circuits.
- Quantum annealing through supported providers.
- Hybrid quantum-classical optimization.

### Classical baselines

Implement:

- Brute force for small cases.
- SciPy optimization where appropriate.
- Google OR-Tools CP-SAT.
- Simulated annealing.
- Greedy heuristics.
- Local search.
- Other suitable exact or approximate algorithms.

Use fair comparisons.

### Benchmark design

Compare methods on equivalent mathematical problems.

Record:

- Objective value.
- Constraint satisfaction.
- Optimality gap when a proven optimum or valid bound is available.
- Approximation ratio where mathematically appropriate.
- Feasibility.
- Execution time.
- Preprocessing time.
- Optimization iterations.
- Shots and circuit evaluations.
- Qubit count.
- Circuit depth.
- Memory use where measurable.
- Number of repeated runs.
- Distribution of outcomes.
- Estimated or actual monetary cost, clearly distinguished.

Use consistent units and problem instances.

Report statistics across several seeds.

When the exact optimum is unknown, do not label the best observed solution as the proven optimum.

Never claim quantum advantage without a well-defined workload and convincing comparative evidence.

### Interactive optimization interface

Users should be able to:

1. Select an optimization problem.
2. Load or generate a small problem instance.
3. Choose algorithms.
4. Configure parameters.
5. Run comparisons.
6. Inspect solution feasibility.
7. View convergence plots.
8. See classical versus quantum results.
9. Export results.
10. Reproduce the experiment.

### ChainMind-ready optimization

Develop reusable problem schemas for:

- Supplier selection.
- Shipment allocation.
- Warehouse scheduling.
- Route assignments.
- Procurement optimization.
- Inventory replenishment.

These should use synthetic sample data by default.

Do not directly modify ChainMind or connect to its production database.

Provide an optional documented adapter for future integration.

---

# PART VII — QUANTUM AI LABORATORY

## 8. Quantum Machine Learning Research

Create an interactive Quantum AI research environment using PennyLane and appropriate compatible machine learning libraries.

### Core capabilities

Implement:

- Variational quantum circuits.
- Parameterized quantum layers.
- Hybrid quantum-classical models.
- Quantum feature maps.
- Quantum kernel experiments.
- Small classification experiments.
- Quantum neural network demonstrations.
- Gradient computation and visualization.
- Model training history.
- Optimizer comparison.

### Training interface

Provide controls for:

- Dataset selection.
- Quantum model architecture.
- Number of qubits.
- Circuit layers.
- Data encoding.
- Learning rate.
- Optimizer.
- Training epochs.
- Batch size.
- Random seed.
- Noise settings.
- Classical baseline.

Show:

- Training loss.
- Validation loss.
- Accuracy when meaningful.
- Confusion matrix for classification.
- Prediction distributions.
- Model size.
- Circuit evaluations.
- Execution time.
- Evidence of overfitting or instability where detectable.

### Dataset requirements

Use small public or synthetic datasets with appropriate licensing.

Implement proper train/validation/test separation.

Do not allow information from the test set to leak into model selection.

Use comparable preprocessing and data access for classical and quantum baselines.

### Classical AI comparisons

Compare quantum models with suitable classical approaches:

- Logistic regression.
- Small neural networks.
- Support vector machines.
- Random forests when applicable.
- Other appropriately sized baselines.

Compare generalization, training cost, inference cost, and accuracy.

Do not present a quantum classifier as superior merely because it achieved a higher score on one tiny example.

### Future research topics

Build extensible foundations for studying:

- Quantum-enhanced representation learning.
- Quantum kernels.
- Quantum generative models.
- Variational circuit expressibility.
- Barren plateaus.
- Noise-aware training.
- Quantum model robustness.
- Hybrid learning systems.

All advanced features must be clearly identified as implemented, experimental, or planned.

---

# PART VIII — QUANTUM NOISE, RELIABILITY AND ERROR CORRECTION

## 9. Noise Simulation Laboratory

Build an environment for studying how realistic imperfections affect quantum computations.

Support appropriate models for:

- Bit-flip noise.
- Phase-flip noise.
- Depolarizing noise.
- Amplitude damping.
- Phase damping.
- Readout errors.
- Gate errors.
- Decoherence.

Use supported simulator noise models.

Compare ideal and noisy execution on the same circuit.

Display:

- Measurement distributions.
- Circuit fidelity measures.
- Observable errors.
- Error rates.
- Sensitivity to gate depth.
- Sensitivity to shot count.
- Effects of configurable noise strength.

Never confuse ideal mathematical outputs with physical-hardware outcomes.

## 10. Error Mitigation Research

Add experiments for:

- Readout-error mitigation.
- Zero-noise extrapolation where supported.
- Other documented error mitigation techniques.

Compare mitigation methods against unmitigated results.

Report variance and additional sampling costs.

Explain that error mitigation does not provide full fault-tolerant quantum computation.

## 11. Quantum Error Correction

Create educational and experimental demonstrations of:

- Three-qubit bit-flip code.
- Three-qubit phase-flip code.
- Syndrome measurement.
- Logical versus physical qubits.
- Stabilizer concepts.
- Small repetition-code experiments.
- Selected surface-code concepts when supportable.

Show detection and correction results using actual simulator output.

Distinguish toy error-correcting codes from scalable fault tolerance.

---

# PART IX — QUANTUM ANNEALING LABORATORY

## 12. D-Wave Ocean Integration

Build a QUBO and Ising optimization laboratory.

Support local modeling and classical samplers first.

### Required features

- Binary quadratic models.
- QUBO generation.
- Ising transformations.
- Objective visualization.
- Constraint penalties.
- Solution sampling.
- Energy distributions.
- Solution feasibility checks.
- Exact and heuristic local baselines.

Use Ocean components such as dimod and appropriate samplers.

### Optional D-Wave cloud integration

When configured and explicitly authorized:

- Connect to available D-Wave solvers.
- Inspect solver capabilities.
- Submit compatible problems.
- Record execution metadata.
- Retrieve returned samples.
- Inspect timing and reported costs where provided.

Never assume all D-Wave solvers are interchangeable.

Do not confuse classical simulated annealing, hybrid solvers, and physical quantum annealers.

Cloud jobs must be disabled by default.

---

# PART X — QUANTUM HARDWARE LABORATORY

## 13. Hardware Provider Management

Create a dedicated quantum hardware workspace.

### IBM Quantum

Support appropriate current IBM Quantum execution interfaces.

Allow:

- Provider configuration.
- Backend discovery.
- Backend metadata inspection.
- Circuit transpilation.
- Simulator execution.
- Authorized quantum hardware submission.
- Job status.
- Returned measurement results.
- Execution metadata.

### Amazon Braket

Support:

- Local simulator execution.
- Backend capability information.
- Optional managed simulation.
- Optional hardware jobs.
- Job histories.
- Cost visibility.

### D-Wave

Support:

- Local Ocean optimization.
- Optional cloud solver integration.
- Returned optimization samples.

### Strict hardware safety requirements

- Hardware execution is OFF by default.
- Never automatically buy or submit paid quantum jobs.
- Require explicit user approval before a paid execution.
- Display estimated cost or explain when an estimate is unavailable.
- Configure budget limits and job quotas.
- Protect API keys and credentials.
- Store secrets outside the frontend.
- Do not log private credentials.
- Handle unavailable providers gracefully.
- Do not invent hardware execution results.
- Record provider, device, backend type, execution time, and job identifier when available.

Show a visible execution badge:

LOCAL SIMULATION

NOISY SIMULATION

CLOUD SIMULATION

HYBRID SOLVER

REAL QUANTUM HARDWARE

These execution modes must never be mislabeled.

---

# PART XI — SPACE AND AEROSPACE QUANTUM RESEARCH

## 14. Space-Oriented Quantum Laboratory

Create a research module exploring potential quantum-computing applications relevant to aerospace and satellite systems.

This module is educational and experimental, not flight-certified.

### Research scenarios

Investigate:

- Satellite task scheduling.
- Ground-station communication windows.
- Spacecraft resource allocation.
- Satellite constellation scheduling.
- Mission planning optimization.
- Multi-satellite task assignment.
- Small orbital maneuver scheduling abstractions.
- Spacecraft power-budget scheduling.
- Sensor observation scheduling.
- Autonomous mission decision-support problems.

### Optimization methods

Compare:

- Classical integer optimization.
- Constraint programming.
- QUBO-based optimization.
- QAOA.
- Annealing-based methods.

Use synthetic mission data.

For scenarios involving orbital mechanics, rely on verified orbital models or established simulation packages rather than inventing physics equations.

### Quantum sensing and communication

Add research explanations and small simulations for:

- Quantum sensing principles.
- Atomic clocks.
- Quantum measurement sensitivity.
- Quantum communication basics.
- Quantum key distribution protocols.
- Entanglement distribution.
- Quantum repeaters as conceptual models.

Do not imply that a software demonstration constitutes a working quantum sensor or secure quantum communication device.

### SRAI integration

Design an optional API allowing SRAI to send optimization problems to Quantum Lab.

The adapter should:

- Accept validated problem data.
- Return candidate solutions.
- Return feasibility information.
- Include execution provenance.
- Identify the algorithm and backend.
- Include relevant limitations.

Do not directly alter SRAI without authorization.

---

# PART XII — QUANTUM COMMUNICATION LABORATORY

## 15. Quantum Networking and Cryptography

Build educational simulations for:

- Quantum teleportation.
- Superdense coding.
- BB84.
- Entanglement-based key distribution.
- Basis selection.
- Measurement disturbance.
- Noise effects.
- Simplified eavesdropping demonstrations.

Clearly distinguish simulated security properties from real cryptographic guarantees.

Do not describe educational BB84 demonstrations as secure production communication systems.

Add an interactive communication diagram showing Alice, Bob, quantum channels, and classical channels.

Provide actual simulated measurement outcomes.

---

# PART XIII — QUANTUM-INSPIRED ALGORITHMS

## 16. Quantum-Inspired Computing

Create a separate module for methods inspired by quantum computing that run on conventional hardware.

Include selected methods such as:

- Simulated annealing.
- Simulated quantum annealing.
- Tensor-network approaches when appropriate.
- Quantum-inspired optimization heuristics.
- Classical sampling methods.
- Ising-model optimization.

The interface must distinguish quantum-inspired classical algorithms from quantum algorithms executed on simulators or physical quantum hardware.

Do not classify a method as quantum hardware computation simply because it uses a QUBO formulation.

---

# PART XIV — HYBRID QUANTUM-CLASSICAL WORKFLOWS

## 17. Hybrid Workflow Builder

Build a modular environment for combining classical computation with quantum circuit evaluation.

A typical workflow:

1. Construct a classical optimization problem.
2. Map it into a supported quantum representation.
3. Generate a parameterized circuit.
4. Execute the circuit.
5. Measure outputs.
6. Update parameters classically.
7. Evaluate convergence.
8. Compare against a classical baseline.
9. Save the full experiment.

Support configurable parameter sweeps and optimizers.

Allow researchers to inspect intermediate results rather than only final scores.

Provide execution logs and meaningful error messages.

Implement job cancellation and computational limits where feasible.

---

# PART XV — ADVANCED VISUALIZATION

## 18. Visualization Engine

Create accurate, interactive visualization tools.

### Quantum visualizations

- Circuit diagrams.
- Bloch spheres.
- Probability histograms.
- Amplitude plots.
- Phase plots.
- Density matrices.
- Measurement results.
- Gate-depth charts.
- Noise comparison plots.

### Optimization visualizations

- Optimization convergence.
- Objective-function distributions.
- Solution feasibility.
- Graph coloring for Max-Cut solutions.
- Algorithm comparison charts.
- Runtime and cost comparison.
- Parameter sensitivity.

### Machine learning visualizations

- Training curves.
- Validation curves.
- Confusion matrices.
- Decision boundaries for suitable low-dimensional examples.
- Parameter gradients.
- Model comparison.

### Experiment visualizations

- Repeated-trial distributions.
- Error bars.
- Confidence intervals when appropriate.
- Baseline comparisons.
- Run timelines.
- Experiment metadata.

Every graph must be computed from real data, reproducible simulations, or explicitly labeled illustrative examples.

Never use static images that pretend to be live results.

---

# PART XVI — QUANTUM LEARNING ACADEMY

## 19. Personal Quantum Computing Course

Build an interactive learning experience integrated directly into the actual Quantum Lab.

I want to understand the technology while building and operating it.

Teach from beginner to research-level concepts.

### Level 1 — Foundations

- Bits and classical logic.
- Complex numbers.
- Vectors.
- Matrices.
- Basic probability.
- Qubits.
- Quantum gates.
- Superposition.
- Measurement.

### Level 2 — Quantum Circuits

- Multiple qubits.
- Entanglement.
- Controlled gates.
- Circuit composition.
- Measurement results.
- Circuit depth.
- Simulators.

### Level 3 — Quantum Algorithms

- Deutsch–Jozsa.
- Bernstein–Vazirani.
- Grover search.
- QFT.
- Phase estimation.
- VQE.
- QAOA.

### Level 4 — Quantum Programming

- Python quantum programming.
- Qiskit.
- PennyLane.
- Simulator backends.
- Circuit debugging.
- Testing.
- Reproducibility.

### Level 5 — Quantum Optimization

- Optimization models.
- QUBO.
- Ising models.
- Constraint programming.
- QAOA.
- Quantum annealing.
- Classical baselines.

### Level 6 — Quantum AI

- Parameterized quantum circuits.
- Quantum feature maps.
- Variational classifiers.
- Hybrid neural networks.
- Quantum kernels.
- Training instability.
- Generalization.

### Level 7 — Advanced Quantum Research

- Noise.
- Error mitigation.
- Error correction.
- Hardware constraints.
- Experimental benchmarking.
- Scientific methodology.
- Research papers.

### Level 8 — Applied Research

- Aerospace optimization.
- Supply-chain optimization.
- Quantum communication.
- Quantum-inspired algorithms.
- Hybrid systems.
- Independent research projects.

### Teaching style

Explain concepts in clear language.

Introduce the mathematical notation, then explain what each symbol means.

Do not skip algebraic steps when they are essential to understanding.

Include visual explanations, interactive examples, and exercises.

Allow users to:

- Learn a concept.
- Run an experiment demonstrating the concept.
- Modify parameters.
- Predict the result.
- Compare predicted and observed results.
- Complete practice problems.
- Receive explanations.
- Track progress.

### Learning features

- Interactive lessons.
- Short quizzes.
- Coding exercises.
- Experiment-based assignments.
- Formula reference sheets.
- Glossary.
- Project challenges.
- Saved progress.
- Beginner and advanced explanation modes.

Learning exercises must connect directly to functioning platform capabilities.

Avoid making the learning system depend entirely on free-form AI-generated answers.

Use deterministic checks for objectively verifiable exercises when practical.

---

# PART XVII — AI RESEARCH ASSISTANT

## 20. Quantum Research Copilot

Implement an optional AI assistant to help users understand and work with Quantum Lab.

The assistant should be capable of:

- Explaining quantum concepts.
- Explaining mathematical equations.
- Helping debug circuits.
- Suggesting experiments.
- Explaining solver results.
- Interpreting convergence plots.
- Comparing algorithms.
- Reviewing code.
- Generating runnable experiment configurations.
- Explaining hardware limitations.
- Identifying unsupported research claims.

### Important limitations

The assistant must distinguish:

- Mathematical derivations.
- Simulated results.
- Measured hardware results.
- Hypotheses.
- Unverified claims.

Never allow the assistant to invent scientific citations.

Never let the assistant silently change experimental results.

Model-generated interpretations should be separate from raw experiment data.

If AI model integration is unavailable, leave the copilot optional rather than providing fake AI responses.

Any external model API must be explicitly configured.

---

# PART XVIII — RESEARCH ENGINEERING AND EXPERIMENTS

## 21. Research Experiment Manager

Implement structured research workflows.

Each experiment must have:

- Unique experiment ID.
- Experiment title.
- Scientific objective.
- Algorithm.
- Backend.
- Input data reference.
- Algorithm parameters.
- Random seed.
- Shots.
- Qubit count.
- Circuit depth where applicable.
- Software package versions.
- Start and completion timestamps.
- Execution status.
- Raw results.
- Processed results.
- Error logs.
- Baseline comparison.
- Reproducibility metadata.

Support saving, reopening, comparing, and exporting experiments.

### Experiment statuses

Use:

- Draft.
- Queued.
- Running.
- Completed.
- Failed.
- Cancelled.
- Not Executed.

Never mark a job Completed merely because a test configuration was generated.

### Reproducibility

Support:

- Fixed seeds.
- Stored configurations.
- Versioned experiment schemas.
- Software environment snapshots.
- Repeated trials.
- Experiment cloning.
- JSON/CSV exports.
- Machine-readable result artifacts.

Ensure experimental results can be recreated as closely as backend capabilities permit.

Clearly document unavoidable nondeterminism, especially with real quantum hardware.

---

## 22. Benchmarking Framework

Build a reliable framework that compares algorithms fairly.

### Benchmark principles

- Use the same problem instance.
- Apply identical constraints.
- Record resource budgets.
- Specify termination criteria.
- Separate setup time from optimization time.
- Report both best and distributional performance.
- Include classical baselines.
- Track sampling costs.
- Distinguish exact and heuristic solvers.
- Avoid cherry-picking successful seeds.

For stochastic methods, run multiple repetitions where feasible.

When comparing real hardware with simulators, account for the different execution environments and report the limitations of direct runtime comparisons.

Do not claim a computational speedup based only on simulator performance.

### Scientific statistics

Support:

- Means.
- Medians.
- Standard deviations.
- Quantiles.
- Confidence intervals when justified.
- Error rates.
- Approximation gaps.
- Sample sizes.
- Repeated-run plots.

Distinguish statistical uncertainty from systematic measurement error.

---

# PART XIX — RESEARCH NOTEBOOK AND DOCUMENTATION

## 23. Quantum Research Notebook

Create an experiment-linked notebook or research log.

Researchers should be able to record:

- Hypotheses.
- Experiment objectives.
- Parameter choices.
- Observations.
- Results.
- Interpretation.
- Limitations.
- Next questions.

Support Markdown notes.

Allow experiment references and result snapshots.

Export research summaries in Markdown or another supported format.

Do not automatically invent conclusions.

### Documentation requirements

Maintain:

- README.
- Installation guide.
- Architecture documentation.
- Algorithm documentation.
- API reference.
- Supported backends.
- Known limitations.
- Testing instructions.
- Reproducibility guide.
- Cloud-provider setup instructions.
- Troubleshooting guide.

Explain how to run the application locally.

---

# PART XX — SOFTWARE ARCHITECTURE AND APIS

## 24. Modular Architecture

Separate concerns cleanly.

Suggested modules:

- quantum/core
- quantum/circuits
- quantum/algorithms
- quantum/simulators
- quantum/noise
- quantum/optimization
- quantum/annealing
- quantum/ml
- quantum/hardware
- quantum/communications
- quantum/aerospace
- quantum/benchmarks
- quantum/experiments
- quantum/education

Use the actual repository conventions if they differ.

### Backend services

Provide reusable functions or services for:

- Circuit validation.
- Circuit execution.
- Optimization.
- Benchmarking.
- Experiment persistence.
- Job execution.
- Results retrieval.
- Hardware-provider management.

### API capabilities

Design endpoints or equivalent service interfaces for:

- Simulator discovery.
- Circuit execution.
- Algorithm discovery.
- Algorithm execution.
- Optimization jobs.
- Experiment creation.
- Experiment status.
- Result retrieval.
- Benchmark comparisons.
- Experiment export.

Use validated request and response schemas.

Separate HTTP request handling from scientific computation.

Do not execute arbitrary uploaded Python code in the main application process.

---

# PART XXI — PERFORMANCE AND COMPUTE MANAGEMENT

## 25. Resource Controls

Quantum simulation becomes expensive quickly as qubit counts increase.

Implement sensible default limits for:

- Qubit count.
- Shot count.
- Circuit depth.
- Execution time.
- Concurrent jobs.
- Memory usage.
- Optimization iterations.
- Experiment batch size.

These limits must be configurable according to machine capabilities.

Show an estimated compute warning before launching expensive simulations.

Allow a user to cancel supported jobs.

Do not run multiple resource-intensive jobs automatically without limits.

Use background job execution only when the application has actual job-worker infrastructure.

Avoid blocking the entire UI during scientific computation.

### Performance improvements

Use profiling before optimizing.

Potential improvements:

- Caching repeated deterministic results.
- Vectorized numerical operations.
- Efficient job queues.
- Parallel execution for independent experiments.
- Sparse mathematical representations.
- Optional accelerated simulation.

Do not claim GPU acceleration unless a supported backend is actually using the GPU.

---

# PART XXII — TESTING AND SCIENTIFIC VALIDATION

## 26. Automated Testing

Create an automated test suite covering:

### Quantum correctness

- State normalization.
- Gate unitarity.
- Expected Bell-state amplitudes.
- Measurement probabilities.
- Circuit equivalence.
- Basic quantum algorithm outputs.
- Noisy versus ideal behavior.

### Optimization correctness

- Valid objective calculations.
- Constraint satisfaction.
- QUBO energy consistency.
- Ising transformation correctness.
- Classical optimum verification for small problems.
- QAOA output interpretation.

### Quantum machine learning

- Parameter dimensions.
- Gradient validity where supported.
- Train/test separation.
- Reproducible seeding.
- Prediction output shape.
- Consistent metric calculations.

### Backend

- Schema validation.
- API request validation.
- Experiment storage.
- Job state transitions.
- Cancellation behavior.
- Failure handling.
- Export consistency.

### Frontend

- Navigation.
- Input handling.
- Form validation.
- Loading states.
- Error reporting.
- Empty states.
- Experiment result rendering.
- Saving and restoring work.

### Provider safety

- No hardware jobs without explicit authorization.
- No credentials included in exported results.
- No fabricated backend availability.
- No unsupported provider calls.

Use pytest for backend tests and the existing frontend testing framework where possible.

Run relevant tests after modifications.

Report failures rather than hiding them.

---

# PART XXIII — USER EXPERIENCE

## 27. Professional Quantum Research Interface

Build a modern technical dashboard inspired by professional scientific software, without copying proprietary designs.

### Visual style

- Dark navy or charcoal research theme.
- Optional light theme.
- Electric blue, teal, and violet accents.
- Clear scientific typography.
- Responsive layouts.
- High-contrast plots.
- Accessible interface elements.
- Expandable technical panels.

### Interaction design

Every major laboratory should have three stages:

**Configure → Execute → Analyze**

Users should always know:

- What they are running.
- Which backend is being used.
- Whether the computation is simulated or physical.
- What parameters are configured.
- Whether the run has started.
- Whether it completed.
- Where results are stored.
- Whether the result has been verified.

### Important usability requirements

- No fake dashboard statistics.
- No nonfunctional buttons.
- No unrelated stock graphics replacing real visualizations.
- No extremely narrow input fields.
- No enormous empty panels.
- No misleading progress indicators.
- No accidental loss of configured experiments.
- No mixing prior experiment outputs with new runs.

Display honest error messages.

---

# PART XXIV — RESEARCH ROADMAP

## 28. Stage 1: Foundation and First Verified Experiment

Start here.

1. Audit existing repository.
2. Fix broken dependencies and tests.
3. Establish reliable local quantum simulation.
4. Implement the Bell-state experiment.
5. Calculate expected theoretical results.
6. Execute the circuit.
7. Display measured or simulated output.
8. Validate numerical results.
9. Save execution metadata.
10. Add automated tests.
11. Display the result in the UI.

Do not proceed to large advanced features before this works.

## 29. Stage 2: Quantum Circuit Studio

Implement:

- Circuit creation.
- Core gates.
- Circuit visualization.
- Parameter editing.
- Simulator selection.
- Measurement charts.
- Save/load.
- Export.

## 30. Stage 3: Quantum Optimization

Implement:

- Max-Cut problem generator.
- Exact classical solver.
- QAOA implementation.
- Multiple random seeds.
- Objective comparison.
- Runtime measurement.
- Convergence visualization.
- Reproducible result export.

## 31. Stage 4: Quantum AI

Implement:

- Small quantum classifier.
- Classical classifier baseline.
- Parameterized circuits.
- Training and validation.
- Accuracy comparison.
- Learning curves.
- Honest assessment of generalization.

## 32. Stage 5: Noise and Error Correction

Implement:

- Noise models.
- Ideal/noisy comparison.
- Small error-correction experiment.
- Error mitigation study.
- Hardware readiness indicators.

## 33. Stage 6: Quantum Annealing

Implement:

- QUBO builder.
- Local Ocean solvers.
- Classical annealing comparisons.
- Optional D-Wave cloud adapter.

## 34. Stage 7: Aerospace and Industrial Optimization

Implement synthetic:

- Satellite scheduling.
- Spacecraft resource allocation.
- Warehouse assignment.
- Shipment allocation.
- Supplier optimization.

Compare classical and quantum methods.

## 35. Stage 8: Research Platform

Implement:

- Experiment manager.
- Repeated trials.
- Benchmark suites.
- Research notebook.
- Exportable reports.
- Reproducibility tools.

## 36. Stage 9: Optional Real Hardware

After local validation:

- IBM Quantum integration.
- Amazon Braket integration.
- D-Wave integration.
- Cost controls.
- Job tracking.
- Hardware-versus-simulator comparisons.

Do not automatically start paid cloud executions.

## 37. Stage 10: Advanced Research Extensions

Explore selectively:

- Quantum kernels.
- Advanced variational algorithms.
- Noise-aware learning.
- Quantum communication.
- Quantum sensing models.
- Selected quantum error-correction research.
- Advanced hybrid optimization.
- Higher-fidelity aerospace applications.

Prioritize scientific usefulness rather than feature count.

---

# PART XXV — RESEARCH INTEGRITY

## 38. Non-Negotiable Scientific Rules

Always distinguish:

1. Mathematical theory.
2. Exact classical computation.
3. Quantum circuit simulation.
4. Noisy quantum simulation.
5. Quantum-inspired classical computation.
6. Hybrid quantum-classical computation.
7. Physical quantum hardware execution.

Never present one as another.

Never invent experiment outcomes.

Never fabricate citations.

Never claim quantum advantage without credible supporting evidence.

Never assume quantum computing improves every optimization problem.

Never claim hardware-level accuracy from ideal simulation.

Never present proposed research experiments as completed findings.

Never make unsupported claims about fault tolerance, cryptographic security, or scalable quantum AI.

Use current documentation and verify unfamiliar algorithms before implementing them.

If an experiment produces unexpected results, investigate and report them instead of adjusting the display to match expectations.

---

# PART XXVI — FINAL DELIVERY REQUIREMENTS

## 39. Required Deliverables

The implemented project should ultimately include:

1. Working Quantum Lab application.
2. Local circuit simulator.
3. Interactive circuit visualization.
4. Executable quantum algorithms.
5. Correct quantum optimization experiments.
6. Classical benchmarks.
7. Quantum AI experiments.
8. Noise simulation.
9. Research experiment tracking.
10. Learning modules.
11. Quantum hardware adapters, when configured.
12. Synthetic aerospace and logistics examples.
13. Reproducibility metadata.
14. Automated testing.
15. Technical documentation.
16. Clear implementation status for every major module.

Do not promise all deliverables are complete after one coding session.

Build iteratively and maintain a clear status report.

## 40. Initial Execution Instructions

Immediately perform the following:

1. Inspect my actual repository.
2. Identify the existing architecture and implemented features.
3. Verify the scientific dependencies and current library APIs.
4. Preserve working components.
5. Identify the smallest complete scientific experiment that can be built with the existing architecture.
6. Implement or repair a Bell-state circuit using local simulation.
7. Add independent mathematical verification.
8. Display real results in the existing interface.
9. Save reproducibility metadata.
10. Write and run automated tests.
11. Fix any failures introduced by the implementation.
12. Document what changed.

Then identify the next concrete milestone: an executable Max-Cut QAOA-versus-classical benchmark.

**Do not spend the entire response writing a roadmap.**

Start making code changes after the necessary audit.

### Definition of Done for the first milestone

The first milestone is only complete when:

- The circuit is created programmatically.
- The simulator actually executes it.
- The result matches theoretical expectations within stated numerical or sampling tolerance.
- The frontend displays the result.
- The experiment can be rerun.
- The execution backend is identified.
- Relevant automated tests pass.
- The README explains how to reproduce the experiment.

### Final Reporting Format

After implementation, report:

**Repository assessment:** What already existed.

**Implemented:** Exact files and functionality changed.

**Scientific validation:** How correctness was checked.

**Tests:** Commands executed and pass/fail results.

**Limitations:** What is still unsupported.

**Next milestone:** The next useful working implementation.

**IMPORTANT FINAL DIRECTIVE**

Build Quantum Lab as a scientific computing and quantum research platform, not as a decorative AI-generated interface.

Make every module evidence-driven, mathematically defensible, reproducible, and useful for real learning and experimentation.

Prioritize reliable working software over ambitious feature claims.

BEGIN BY INSPECTING THE EXISTING CODEBASE AND IMPLEMENTING THE FIRST VERIFIED END-TO-END QUANTUM EXPERIMENT.