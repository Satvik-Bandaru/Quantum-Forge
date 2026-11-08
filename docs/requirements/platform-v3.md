# QUANTUMLAB — MASTER CODEX BUILD PROMPT V3
## Advanced Quantum Computing, Virtual Physical Quantum Laboratory, Photonics, Quantum Optics, Quantum AI & Scientific Research Platform

# 0. ROLE AND MISSION

You are my principal quantum computing research engineer, experimental quantum physicist, photonics engineer, quantum optics specialist, scientific software architect, full-stack developer, simulation engineer, AI researcher, and technical educator.

Your task is to transform my EXISTING Quantum Lab project into a powerful, interactive, scientifically grounded research and learning platform.

I want Quantum Lab to combine:

1. A complete quantum computing laboratory.
2. A virtual experimental quantum physics laboratory.
3. A virtual photonics and quantum optics laboratory.
4. A quantum hardware and device simulation environment.
5. A quantum algorithms development environment.
6. A quantum optimization research platform.
7. A quantum AI and machine learning laboratory.
8. A quantum communications laboratory.
9. A quantum noise, control, and error-correction laboratory.
10. An advanced scientific research and benchmarking platform.
11. A virtual equipment and laboratory instrumentation system.
12. A structured quantum computing and experimental physics learning academy.
13. A scientific AI research assistant.
14. Optional future research integrations with my independent SRAI, ChainMind, and NexusLab projects.

This is intended to become an actual working scientific software system, not a static interface, AI chatbot wrapper, or visual demonstration with fictional results.

The platform must let me design experiments, configure simulated equipment, execute physics models, inspect results, change parameters, compare outcomes, learn the underlying mathematics, and develop original research projects.

**The ultimate objective is to create a software-based virtual quantum research institute that I can use to study both theoretical quantum computing and experimental quantum technologies.**

Never exaggerate scientific capabilities.

Never describe classical simulations as physical experiments performed on real hardware.

Never claim quantum advantage without reliable comparative evidence.

Always distinguish implemented features from experimental prototypes and future research ideas.

---

# PART 1 — INSPECT AND PRESERVE MY CURRENT PROJECT

Before making changes:

- Inspect the complete existing repository.
- Identify all working features, pages, modules, and dependencies.
- Inspect the current frontend and backend.
- Review existing Python quantum code and scientific models.
- Examine tests, documentation, and application configuration.
- Identify outdated libraries and compatibility problems.
- Identify existing mathematical or scientific mistakes.
- Check Git status and preserve uncommitted work.
- Preserve user data, existing experiments, and working code.

Do not rebuild everything from scratch.

Do not replace functional code just because a different architecture looks more attractive.

Maintain backward compatibility when reasonable.

Create a concise repository audit and implementation plan, then begin implementation.

Do not stop after generating the plan.

Do not modify my other projects unless I explicitly authorize it.

Quantum Lab must remain an independent project with optional integration interfaces.

---

# PART 2 — TECHNICAL ARCHITECTURE

## 2.1 Scientific Backend

Use Python for scientific computations.

Evaluate these libraries based on current compatibility and official documentation:

- NumPy
- SciPy
- SymPy
- Qiskit
- Qiskit Aer
- QuTiP
- PennyLane
- Perceval
- Meep
- gdsfactory
- D-Wave Ocean SDK
- Google OR-Tools
- PyTorch
- scikit-learn
- pandas
- Pydantic
- pytest

Consider Strawberry Fields for compatible continuous-variable quantum photonics experiments, but verify Python requirements and maintenance status before choosing it.

Do not use deprecated Qiskit Dynamics as the default dynamics engine. Prefer maintained QuTiP functionality for supported Hamiltonian and master-equation simulations.

Use optional dependencies for specialized computational modules rather than requiring every user to install the entire stack.

## 2.2 Frontend

Preserve the existing frontend where practical.

Otherwise favor:

- React
- TypeScript
- A professional accessible component library
- Plotly or equivalent scientific plots
- SVG-based optical and circuit diagrams
- Three.js where useful for 3D visualization

The frontend must interact with actual simulation and calculation engines.

## 2.3 Backend Services

Use the existing backend when appropriate or introduce FastAPI.

Create separated services for:

- Circuit execution
- Quantum physics
- Photonics
- Quantum optics
- Quantum hardware abstractions
- Optimization
- Quantum machine learning
- Experiment tracking
- Scientific visualization
- Learning and assessments
- AI research assistance

## 2.4 Data and Infrastructure

Use SQLite initially unless an existing database should be preserved.

Consider PostgreSQL for larger installations.

Provide:

- Git-based version control
- Automated tests
- Experiment persistence
- Docker or reproducible environment configurations
- Structured logging
- Dependency version tracking
- Cost and resource controls
- API documentation

Design the project for local execution first.

Optional cloud services must never be required to access the basic educational laboratories.

---

# PART 3 — MAIN APPLICATION

## 3.1 Research Dashboard

Create a professional scientific dashboard called:

**QuantumLab Research Command Center**

Main navigation:

1. Research Overview
2. Quantum Circuit Laboratory
3. Virtual Physical Quantum Lab
4. Virtual Photonics Lab
5. Quantum Optics Lab
6. Quantum Hardware & Device Lab
7. Quantum Algorithms
8. Quantum Optimization
9. Quantum AI & Machine Learning
10. Quantum Noise & Control
11. Quantum Error Correction
12. Quantum Communication
13. Aerospace Quantum Research
14. Experiment Benchmarking
15. Quantum Learning Academy
16. Research Notebook
17. Hardware Providers
18. Research AI Assistant
19. Settings

Only enable navigation items with useful implementation.

Mark incomplete modules as Planned or Experimental.

## 3.2 Dashboard Metrics

Show actual available data:

- Saved circuits
- Completed experiments
- Current simulator jobs
- Failed experiments
- Algorithm availability
- Recent simulation results
- Quantum hardware connection status
- Qubit and optical-mode counts
- Experimental fidelity measurements
- Optimization results
- Compute usage
- Learning progress

Never invent measurement values.

---

# PART 4 — VIRTUAL PHYSICAL QUANTUM LABORATORY

## 4.1 Primary Goal

Create an interactive virtual laboratory that models how quantum physics experiments are performed.

I want to go beyond abstract quantum circuit diagrams.

I should be able to select simulated quantum devices, configure equipment, change experimental parameters, apply controls, collect virtual measurements, observe noise, analyze results, and compare different quantum platforms.

The laboratory must feel like a real experimental research environment while remaining explicit that it is a computational simulation.

## 4.2 Laboratory Interface

Create an interactive workspace with three main regions.

**Left: Equipment Library**

Show configurable simulated equipment and physical systems.

**Center: Laboratory Workbench**

Display the experimental arrangement, device connections, and relevant physical components.

**Right: Controls and Measurements**

Display configurable inputs, instrument readings, run controls, and experiment results.

Support responsive layouts.

Add a 2D workbench first.

Introduce 3D visualization when it improves understanding rather than merely adding decoration.

## 4.3 Virtual Equipment Library

Develop simulation abstractions for:

### Quantum systems

- Single qubit
- Two-qubit system
- Qubit register
- Quantum harmonic oscillator
- Two-level atom
- Three-level atom
- Spin-1/2 system
- Coupled spins
- Optical cavity
- Superconducting qubit
- Trapped ion
- Neutral atom
- Quantum dot
- Nitrogen-vacancy center
- Photonic qubit
- Oscillator and cavity modes

### Control equipment

- Pulse generator
- Microwave signal generator
- Radio-frequency control
- Frequency and phase controls
- Pulse sequencer
- Amplitude controller
- Detuning controller
- Magnetic-field control parameter
- Idealized optical control source
- Timing and synchronization controls

### Measurement equipment

- Oscilloscope
- Spectrum analyzer
- Signal analyzer
- Frequency counter
- Qubit-state readout
- Probability histogram
- Photon counter
- Coincidence counter
- Tomography analyzer
- Noise analyzer
- Virtual data-acquisition system

These are software instruments that operate on simulated signals.

Do not fake instrument readings.

Each simulated instrument must have an explicit input signal, measurement model, and output calculation.

## 4.4 Equipment Connections

Users should be able to configure meaningful links between compatible devices.

Example:

Control Pulse Generator → Qubit Model → Measurement Model → Virtual Oscilloscope

Another example:

Microwave Drive → Superconducting Qubit → Noisy Readout → Measurement Histogram

Provide clear validation for incompatible configurations.

Represent signal paths and physical coupling accurately.

Do not imply that every component can be connected arbitrarily.

## 4.5 Experiment Configuration

Allow users to set:

- System type
- Hamiltonian parameters
- Coupling strengths
- Frequencies
- Detuning
- Temperature where relevant
- Noise rates
- Pulse durations
- Pulse shapes
- Initial quantum state
- Measurement basis
- Number of experimental repetitions
- Simulation time
- Numerical solver tolerance
- Random seed

Use appropriate units.

Apply physically meaningful parameter validation.

Provide warnings about unrealistic assumptions and numerical instability.

## 4.6 Quantum Dynamics Engine

Use QuTiP or an equivalently verified numerical framework to implement actual quantum evolution.

Support:

- Time-independent Hamiltonians
- Time-dependent Hamiltonians
- Schrödinger evolution
- Density-matrix evolution
- Lindblad master-equation evolution
- Monte Carlo quantum trajectories
- Coupled quantum systems
- Open-system dynamics

Use correct solvers and documented conventions.

Show relevant observables as functions of time.

Compute numerical convergence checks where practical.

Make solver choice explicit.

## 4.7 Virtual Quantum Physics Experiments

Implement the following experiments progressively.

### Experiment A — Qubit Superposition

Prepare a qubit in a known initial state.

Apply a Hadamard or equivalent rotation.

Simulate measurements and visualize their distributions.

Verify probabilities against the expected mathematical model.

### Experiment B — Rabi Oscillations

Configure a driven two-level system.

Allow control over:

- Drive amplitude
- Detuning
- Pulse duration
- Noise
- Initial state

Plot population oscillations and corresponding observables.

Use the simulated dynamics to explain resonance and coherent control.

### Experiment C — Ramsey Interferometry

Simulate a Ramsey pulse sequence.

Allow users to configure free-evolution time and detuning.

Display interference fringes.

Introduce dephasing and study contrast loss.

### Experiment D — Spin Echo

Implement an appropriate echo pulse sequence.

Compare evolution with and without echo pulses under specified noise assumptions.

Explain what forms of dephasing the sequence can and cannot mitigate.

### Experiment E — Qubit Relaxation

Model energy relaxation using appropriate open-system dynamics.

Estimate relaxation time from simulated signals.

Allow users to investigate sensitivity to noise and measurement sampling.

### Experiment F — Qubit Dephasing

Simulate coherence loss.

Compare pure dephasing with relaxation effects.

Show both populations and coherence-dependent observables where appropriate.

### Experiment G — Bell-State Preparation

Prepare an entangled two-qubit state.

Measure in suitable bases.

Calculate state fidelity from the modeled state when available.

### Experiment H — Quantum State Tomography

Perform simulated measurements in multiple bases.

Reconstruct a density matrix using a suitable estimator.

Validate normalization, Hermiticity, and positive semidefiniteness.

Display reconstruction uncertainty and limitations.

### Experiment I — Quantum Process Characterization

Build a small process-tomography or equivalent channel-characterization demonstration.

Explain its assumptions and computational requirements.

### Experiment J — Measurement Calibration

Create simulated readout confusion matrices.

Measure classification errors.

Investigate assignment-error mitigation.

### Experiment K — Cavity Quantum Electrodynamics

Implement a simplified cavity–two-level-system model where supported.

Explore coupling strength, detuning, photon number, and dissipation.

### Experiment L — Quantum Zeno Effect

Provide a physically meaningful simulation illustrating how repeated measurements can modify quantum evolution under specified assumptions.

Do not exaggerate the scope of the effect.

### Experiment M — Quantum Tunneling

Use a suitable numerical model to study tunneling through a potential barrier.

Display wavefunctions, probability density, and transmission estimates.

### Experiment N — Two-Particle Interference

Show quantum interference and distinguish it from classical wave interference.

### Experiment O — Decoherence Comparison

Compare ideal closed-system evolution with noisy open-system evolution.

Use identical initial conditions.

## 4.8 Physical Quantum Hardware Models

Create separate simulated research modules for the following platforms.

### Superconducting Quantum Computing Lab

Model a simplified superconducting qubit or transmon-like device at an appropriate level of approximation.

Include:

- Energy levels
- Control pulses
- Rabi oscillations
- Ramsey experiments
- Relaxation and dephasing
- Readout errors
- Simplified resonator coupling
- Gate calibration concepts

Do not pretend the simulation reproduces the full fabrication or materials physics of a real superconducting chip.

### Trapped-Ion Quantum Lab

Model:

- Internal atomic states
- Selected motional states
- Laser-driven transitions
- Single-qubit rotations
- Simplified entangling interactions
- Heating and dephasing
- State-dependent fluorescence readout

Introduce realistic physical detail only when a suitable validated model exists.

### Neutral-Atom Quantum Lab

Investigate:

- Atom arrays
- Two-level and Rydberg-state models
- Simplified blockade interactions
- Optical control
- Entanglement
- Interaction graphs
- Noise and atom loss

Distinguish a simplified Hamiltonian simulation from a complete neutral-atom hardware digital twin.

### Spin-Qubit Laboratory

Explore:

- Spin Hamiltonians
- Magnetic resonance
- Coupling
- Spin control
- Dephasing
- Readout

### Quantum Dot Laboratory

Include simplified models for:

- Confined energy levels
- Charge or spin states
- Coupling
- Optical excitation where appropriate

### Quantum Sensing Laboratory

Investigate suitable models for:

- Phase estimation
- Interferometric sensing
- Spin-based magnetometry
- Atomic-clock principles
- Noise-limited sensitivity
- Quantum Fisher information, where mathematically appropriate

Do not claim that the application physically measures environmental fields.

## 4.9 Advanced Physics Visualizations

Provide:

- Bloch spheres
- Quantum state trajectories
- Energy-level diagrams
- Population dynamics
- Phase-space representations
- Density matrices
- Wigner functions where appropriate
- Measurement histograms
- Spectral response plots
- Coherence decay curves
- Pulse-sequence timelines
- Hamiltonian parameter sweeps

Every visualization must be connected to actual calculations.

## 4.10 Numerical and Scientific Validity

Check:

- State normalization
- Density-matrix trace
- Hermiticity
- Physical positivity
- Correct units
- Expected conservation laws
- Numerical tolerances
- Solver stability
- Reproducibility

For open-system simulations, clearly explain which approximations are used.

Do not claim all real environments can be accurately represented by simple Markovian noise models.

---

# PART 5 — VIRTUAL PHOTONICS LABORATORY

## 5.1 Primary Goal

Create a complete interactive optical and photonics laboratory where I can assemble and simulate optical experiments.

I want to study both classical photonics and quantum photonics.

The virtual laboratory should make it possible to construct optical benches, manipulate light, build interferometers, analyze waveguides, simulate photon statistics, and investigate photonic quantum computation.

Separate three simulation layers:

**Layer 1 — Geometrical optics**

Light rays, lenses, mirrors, refraction, and imaging.

**Layer 2 — Classical wave optics and electromagnetics**

Interference, diffraction, field propagation, polarization, waveguides, and electromagnetic field behavior.

**Layer 3 — Quantum optics**

Single photons, Fock states, squeezing, photon correlations, entanglement, and quantum optical circuits.

These layers must use different mathematical engines when appropriate.

Do not model inherently quantum effects using only decorative classical rays.

## 5.2 Interactive Optical Workbench

Create a visual optical table with a component palette.

Allow users to:

- Add optical components.
- Position components.
- Rotate components.
- Set distances.
- Edit optical parameters.
- Connect compatible optical ports.
- Choose a light source.
- Place detectors.
- Run the optical experiment.
- Inspect results.
- Save the setup.
- Duplicate experiments.
- Compare configurations.

Use a 2D canvas with snapping and component alignment.

Offer a 3D representation later when meaningful.

## 5.3 Virtual Photonics Equipment

Include an expandable library of:

### Light sources

- Monochromatic optical source
- Broadband light source
- Coherent laser model
- Gaussian beam source
- Pulsed optical source
- Polarized light source
- Single-photon source model
- Weak coherent pulse source
- Squeezed-state source
- Entangled-photon-pair source model

### Passive optical components

- Mirror
- Beam splitter
- Polarizing beam splitter
- Lens
- Prism
- Optical filter
- Aperture
- Diffraction grating
- Waveplate
- Polarizer
- Phase shifter
- Optical delay line
- Attenuator
- Fiber segment
- Waveguide
- Optical coupler
- Optical circulator as an advanced modeled device
- Resonator
- Ring resonator

### Advanced components

- Mach–Zehnder interferometer
- Michelson interferometer
- Fabry–Pérot cavity
- Integrated optical directional coupler
- Mode converter
- Electro-optic phase modulator model
- Optical amplitude modulator model
- Optical switch
- Nonlinear optical element
- Photon-pair generation component
- Frequency-conversion component, when supported

### Detectors

- Optical power meter
- Photodiode
- Camera sensor model
- Beam profiler
- Spectrometer
- Photon-number-resolving detector model
- Threshold single-photon detector
- Coincidence counter
- Homodyne detector
- Heterodyne detector
- Correlation measurement instrument

Each component must have explicit supported operating assumptions.

## 5.4 Laser and Beam Simulation

Implement Gaussian beam optics.

Allow control over:

- Wavelength
- Beam waist
- Propagation distance
- Divergence
- Optical power
- Phase
- Polarization
- Coherence assumptions

Display:

- Beam width
- Intensity profile
- Propagation curves
- Rayleigh range
- Optical phase
- Focal behavior

Use appropriate paraxial approximations.

Identify when those approximations cease to apply.

## 5.5 Geometrical Optics Experiments

Implement:

1. Reflection from mirrors.
2. Refraction through optical interfaces.
3. Snell's law.
4. Thin-lens imaging.
5. Lens combinations.
6. Focal length experiments.
7. Optical magnification.
8. Prism dispersion under a specified material model.
9. Total internal reflection.
10. Basic optical-system design.

Use ray tracing and appropriate transfer-matrix models where valid.

## 5.6 Wave Optics Laboratory

Develop physically calculated demonstrations of:

- Double-slit interference
- Single-slit diffraction
- Grating diffraction
- Coherent wave superposition
- Interference visibility
- Diffraction-limited resolution
- Fourier optics
- Fresnel propagation
- Fraunhofer diffraction
- Gaussian beam propagation
- Polarization interference
- Optical coherence

Show electric-field representations and intensity distributions.

Support interactive wavelength, slit spacing, aperture size, observation distance, and polarization settings.

Make approximations explicit.

## 5.7 Electromagnetic Field Simulation

Provide an advanced photonics simulation mode using Meep or a verified compatible FDTD engine.

Support selected:

- Waveguide propagation
- Field confinement
- Optical resonators
- Scattering
- Reflection and transmission
- Refractive-index variations
- Optical modes
- Interference
- Frequency response

Start with small two-dimensional models.

Expand to three-dimensional simulations only with adequate compute limits.

Display:

- Electric-field maps
- Magnetic-field maps where available
- Intensity maps
- Transmission and reflection spectra
- Frequency-domain responses
- Resonance behavior
- Field animation, when computationally feasible

Validate mesh resolution, boundary conditions, simulation duration, and numerical convergence.

Do not pretend FDTD simulations are instantaneous or computationally free.

## 5.8 Integrated Photonics Chip Designer

Create an optional photonic integrated circuit design workspace.

Support:

- Waveguide routing
- Optical splitters
- Directional couplers
- Ring resonators
- Mach–Zehnder interferometers
- Grating couplers
- Optical ports
- Phase shifters
- Simple optical networks

Use gdsfactory or another verified compatible layout library.

Allow:

- Parameter editing
- Component inspection
- Port validation
- Layout rendering
- Design export
- Simplified circuit simulations
- Optional electromagnetic solver integration

Keep circuit-level modeling distinct from full electromagnetic field simulation.

Support GDS-compatible layouts where appropriate.

Do not claim a layout is fabrication-ready without a validated process design kit, design-rule checks, and fabrication-specific verification.

## 5.9 Optical Communications Laboratory

Build simulations for:

- Optical signals
- Intensity modulation
- Phase modulation
- Fiber attenuation
- Signal-to-noise ratio
- Basic dispersion models
- Optical link budgets
- Detection noise
- Symbol-error behavior

Include simplified free-space optical communications.

This will be useful for future aerospace and satellite research.

Never describe a simulated optical link as proof of real-world mission performance.

---

# PART 6 — QUANTUM PHOTONICS & QUANTUM OPTICS LAB

## 6.1 Quantum Photonics Circuit Builder

Create a separate quantum optical circuit editor.

Use Perceval for supported discrete-variable linear-optical experiments.

Consider a compatible continuous-variable simulator when necessary.

Support:

- Optical modes
- Photon-number states
- Vacuum states
- Single photons
- Beam splitters
- Phase shifters
- Mode permutations
- Interferometers
- Photon detection
- Postselection
- Loss models
- Partial distinguishability where supported

Distinguish optical modes from qubits.

Do not use a qubit statevector simulator as a substitute for arbitrary bosonic optical states without a mathematically valid encoding.

## 6.2 Single-Photon Laboratory

Simulate a single photon traveling through an optical circuit.

Allow users to configure:

- Input state
- Optical modes
- Beam-splitter transmissivity
- Relative phase
- Detector efficiency
- Optical losses

Display:

- Output probabilities
- Photon-number distributions
- Detection events
- Statistical uncertainty
- Repeated-shot histograms

## 6.3 Hong–Ou–Mandel Interference

Build a fully interactive HOM interference experiment.

Users should be able to:

- Configure two incident photons.
- Adjust temporal overlap or a suitable distinguishability parameter.
- Set beam-splitter characteristics.
- Configure photon losses.
- Change detector efficiency.
- Repeat simulated experiments.

Show coincidence probability versus delay or distinguishability.

Calculate interference visibility.

Compare distinguishable and indistinguishable photon cases.

Explain the assumptions behind the result.

## 6.4 Mach–Zehnder Interferometry

Implement both:

- Classical optical-wave Mach–Zehnder interferometry
- Single-photon Mach–Zehnder interferometry

Allow users to compare the different descriptions and outputs.

Support phase adjustments, imperfect splitters, and loss.

Display phase-dependent detector probabilities.

## 6.5 Quantum State Preparation

Simulate suitable examples of:

- Fock states
- Coherent states
- Thermal states
- Squeezed states
- Two-mode squeezed states
- Entangled photonic states
- NOON states at small photon numbers

Use mathematically correct representations.

For continuous-variable simulations, manage Fock-space truncation and numerical resource constraints explicitly.

## 6.6 Quantum Optical Measurements

Include simulated:

- Photon counting
- Threshold detection
- Homodyne measurement
- Heterodyne measurement
- Quadrature measurements
- Correlation functions
- Coincidence measurements
- State tomography where supportable

Explain detector models and measurement uncertainty.

## 6.7 Quantum Optics Experiments

Implement progressively:

1. Single-photon beam splitter.
2. Hong–Ou–Mandel interference.
3. Single-photon Mach–Zehnder interferometer.
4. Coherent-state photon statistics.
5. Squeezed-state quadrature measurements.
6. Second-order correlation experiments.
7. Small photonic entanglement demonstrations.
8. Optical Bell-test simulations with explicit assumptions.
9. Quantum teleportation using optical-state models.
10. Small boson-sampling demonstrations.
11. Gaussian-state photonic circuits.
12. Simplified photon-pair generation models.

For experiments involving postselection, explicitly report its role and probability.

Avoid presenting postselected success rates as unconditional success rates.

## 6.8 Nonlinear and Advanced Photonics

Create experimental research modules for:

- Second-harmonic generation
- Sum-frequency generation
- Difference-frequency generation
- Spontaneous parametric down-conversion
- Four-wave mixing
- Kerr nonlinearities
- Optical squeezing
- Optical cavities
- Integrated nonlinear photonics

Begin with validated simplified mathematical models.

Use more sophisticated solvers only where technically justified.

## 6.9 Quantum Photonic Computing

Implement a dedicated research area for:

- Linear optical quantum computing
- Measurement-based photonic quantum computing concepts
- Discrete-variable photonic encodings
- Continuous-variable quantum computing
- Gaussian operations
- Non-Gaussian operations
- Photonic sampling
- Small optical quantum algorithms
- Loss-tolerant optical circuit experiments

Distinguish research demonstrations from scalable fault-tolerant architectures.

## 6.10 Photonics Learning Features

For every supported experiment provide:

- Theory
- Mathematical model
- Visual setup
- Equipment description
- Run controls
- Predicted outcome
- Simulated measurement
- Explanation
- Uncertainty
- Further exercises

Allow students to compare theory and observed simulated outcomes.

---

# PART 7 — QUANTUM ALGORITHMS LAB

Create a runnable quantum algorithm explorer.

Include:

- Bell-state preparation
- Deutsch algorithm
- Deutsch–Jozsa
- Bernstein–Vazirani
- Quantum Fourier Transform
- Grover search
- Phase estimation
- Quantum teleportation
- Superdense coding
- VQE
- QAOA
- Hamiltonian simulation
- Quantum kernel methods

Each implementation needs:

- A mathematical specification.
- Runnable code.
- Input validation.
- A supported simulator backend.
- Real computed outputs.
- Visualizations.
- Automated checks.
- Classical reference comparisons where appropriate.
- Limitations.

Do not make the user navigate through decorative pages to reach an actual experiment.

---

# PART 8 — QUANTUM OPTIMIZATION LAB

Develop an optimization research center using Qiskit, D-Wave Ocean where appropriate, SciPy, and OR-Tools.

Support:

- Max-Cut
- QUBO
- Ising models
- Knapsack
- Scheduling
- Assignment
- Routing on small instances
- Resource allocation
- Inventory optimization
- Supplier selection
- Synthetic portfolio optimization

Implement:

- Exact classical methods
- Heuristic classical methods
- QAOA
- Simulated annealing
- Hybrid optimization
- Optional quantum annealing execution

Compare equivalent problems under documented budgets.

Track:

- Objective value
- Feasibility
- Proven or estimated optimality gap
- Runtime
- Iterations
- Qubit count
- Circuit depth
- Shots
- Computational cost
- Repeated-run statistics

Do not fabricate performance claims or describe a best observed solution as a proven optimum.

---

# PART 9 — QUANTUM AI AND MACHINE LEARNING

Build a hybrid quantum-classical machine learning laboratory.

Support:

- Parameterized quantum circuits
- Variational quantum classifiers
- Quantum feature maps
- Quantum kernels
- Hybrid neural networks
- Differentiable quantum circuits
- Noise-aware learning
- Optimization experiments
- Small quantum generative models where feasible

Compare against suitable classical baselines.

Include:

- Data loading
- Preprocessing
- Train/validation/test splits
- Model definition
- Training controls
- Loss curves
- Generalization results
- Runtime
- Accuracy
- Confusion matrices
- Experimental repeats

Prevent test-data leakage.

Do not assume quantum models outperform comparable classical models.

---

# PART 10 — QUANTUM NOISE, ERROR MITIGATION AND ERROR CORRECTION

Implement:

- Bit-flip noise
- Phase-flip noise
- Depolarizing noise
- Amplitude damping
- Phase damping
- Readout error
- Gate imperfections
- Selected coherent errors
- Appropriate open-system noise models

Study:

- Ideal versus noisy computation
- Noise sensitivity
- Readout mitigation
- Zero-noise extrapolation where supported
- Error syndromes
- Three-qubit repetition codes
- Stabilizer concepts
- Logical versus physical qubits
- Small fault-tolerance demonstrations

Distinguish error correction from error mitigation.

Connect this laboratory with the Virtual Physical Quantum Lab's device-noise models whenever appropriate.

---

# PART 11 — QUANTUM COMMUNICATIONS LAB

Create educational simulations for:

- BB84
- Entanglement-based key distribution
- Quantum teleportation
- Superdense coding
- No-cloning demonstrations
- Quantum channel noise
- Photon loss
- Quantum repeater concepts
- Simplified optical quantum networks

Use the Virtual Photonics Lab and Quantum Optics Lab where relevant.

Distinguish simulated protocol behavior from real deployed cryptographic security.

---

# PART 12 — SPACE AND AEROSPACE QUANTUM RESEARCH

Create a specialized research area for potential future integrations with SRAI.

Investigate:

- Satellite task scheduling
- Ground-station scheduling
- Observation allocation
- Spacecraft resource optimization
- Constellation scheduling
- Small mission-planning problems
- Optical space communications
- Quantum communication concepts for satellites
- Quantum sensing concepts
- Atomic-clock principles
- Hybrid optimization for mission planning

Use synthetic mission data.

Separate orbital-dynamics models from quantum optimization algorithms.

Use physics-based orbital models when needed.

Do not claim a flight-ready subsystem or validated aerospace hardware without appropriate evidence.

---

# PART 13 — INTERACTIVE EXPERIMENT BUILDER

Build a unified experiment-design interface.

Users should be able to:

1. Select a laboratory.
2. Choose an experiment.
3. Configure the equipment or mathematical model.
4. Set input parameters.
5. Select a simulator.
6. Inspect assumptions.
7. Run an experiment.
8. View results.
9. Repeat the experiment.
10. Compare runs.
11. Export evidence.
12. Save research notes.

Provide experiment templates.

Support controlled parameter sweeps.

Support multiple random seeds when relevant.

Show a preview of compute requirements before expensive simulations.

Keep different physical domains scientifically separate even when using the same interface framework.

---

# PART 14 — VIRTUAL LAB INSTRUMENTATION

Build a reusable software instrumentation system.

## Virtual Oscilloscope

Display time-dependent signals generated by the simulation.

Support appropriate controls for:

- Time range
- Signal scaling
- Channel selection
- Signal noise
- Triggers
- Waveform export

## Virtual Spectrum Analyzer

Compute frequency-domain representations from simulated signals using appropriate numerical methods.

Show frequency resolution and windowing choices.

## Virtual Photon Counter

Simulate detection events using the relevant photon statistics and detector model.

Show:

- Event count
- Count rate
- Detection efficiency
- Dark counts where modeled
- Uncertainty estimates

## Virtual Coincidence Counter

Calculate coincidence statistics from relevant simulated detection events.

Support time-window configuration.

## Virtual Quantum State Analyzer

Display:

- State populations
- Density matrices
- Fidelity
- Purity
- Entanglement metrics where appropriate
- State tomography results

## Virtual Optical Power Meter

Compute modeled optical power.

Provide clear units and assumptions.

## Virtual Lab Data Logger

Capture all experiment outputs with timestamps and configuration metadata.

Do not merely animate changing numbers without mathematical calculations.

---

# PART 15 — SCIENTIFIC VISUALIZATION AND 3D LAB

Build scientifically useful visualization layers.

## 2D Visualizations

Prioritize:

- Quantum circuits
- Optical benches
- Hamiltonian evolution plots
- Oscilloscope traces
- Bloch spheres
- Interference patterns
- Beam propagation
- Quantum state distributions
- Waveguide cross sections
- Photon counting histograms
- Experimental comparison charts

## 3D Visualizations

Add when useful:

- Spatial optical beam propagation
- Quantum device schematic environments
- Optical table arrangements
- Electric-field intensity volumes
- Selected cavity or waveguide geometry
- Conceptual quantum hardware layouts

Every visual must be labeled correctly as:

- Physical-model output
- Simulation geometry
- Instrument readout
- Conceptual illustration

Do not depict conceptual animations as measured physical effects.

---

# PART 16 — RESEARCH ASSISTANT

Create an optional **Quantum Research Copilot**.

It should help me:

- Understand quantum physics.
- Learn experimental techniques.
- Explain calculations.
- Debug circuits.
- Investigate photonic components.
- Interpret simulation results.
- Compare physical models.
- Review scientific code.
- Suggest follow-up experiments.
- Explain relevant mathematics.
- Identify possible numerical errors.
- Develop original research questions.

Ground answers in actual experiment results and available documentation.

Separate generated explanations from computation outputs.

Never invent papers, citations, physical observations, or experimental conclusions.

Do not make this AI assistant a substitute for the scientific backend.

---

# PART 17 — INTERACTIVE QUANTUM LEARNING ACADEMY

Create a complete personal learning curriculum integrated with the software.

## Beginner Track

- Classical bits
- Complex numbers
- Vectors
- Matrices
- Probability
- Waves
- Quantum states
- Measurement
- Basic quantum gates

## Quantum Computing Track

- Quantum circuits
- Entanglement
- Quantum algorithms
- Qiskit
- Noise
- Optimization
- Hardware concepts

## Experimental Quantum Physics Track

- Hamiltonians
- Quantum dynamics
- Rabi oscillations
- Ramsey interferometry
- Spin echo
- Decoherence
- Readout
- Tomography
- Physical qubit architectures

## Photonics Track

- Electromagnetic waves
- Reflection
- Refraction
- Gaussian beams
- Lenses
- Interference
- Diffraction
- Polarization
- Waveguides
- Optical resonators
- Integrated photonics

## Quantum Optics Track

- Photons
- Fock states
- Coherent states
- Beam splitters
- Single-photon interference
- HOM interference
- Entangled photons
- Squeezed light
- Photon counting
- Quantum photonic computing

## Advanced Research Track

- Quantum noise
- Quantum control
- Error correction
- Scientific benchmarking
- Experimental uncertainty
- Numerical convergence
- Quantum machine learning
- Quantum photonic algorithms
- Research paper reproduction

### Teaching Requirements

Explain concepts clearly and progressively.

For equations:

- Define every symbol.
- Explain the physical meaning.
- Show important algebraic steps.
- Provide a numerical example.
- Connect the equation to a runnable experiment.

Use a beginner-friendly mode and a mathematical research mode.

Provide:

- Lessons
- Formula sheets
- Quizzes
- Interactive experiments
- Coding exercises
- Visual explanations
- Small research challenges
- Progress tracking

Allow me to learn by manipulating experimental parameters rather than only reading text.

---

# PART 18 — RESEARCH NOTEBOOK AND EXPERIMENT HISTORY

Implement a persistent research notebook.

Each experiment record should include:

- Experiment ID
- Title
- Scientific question
- Laboratory category
- Mathematical model
- Simulation backend
- Initial conditions
- Parameter values
- Random seed
- Software versions
- Assumptions
- Raw outputs
- Processed results
- Visualizations
- Numerical warnings
- Scientific interpretation
- Known limitations

Support Markdown research notes and experiment comparisons.

Allow exporting JSON, CSV, images, and Markdown where appropriate.

Do not automatically overwrite earlier experiment evidence when rerunning a simulation.

---

# PART 19 — SCIENTIFIC BENCHMARKING

Create a reproducible benchmarking framework across the platform.

## Quantum Circuit Tests

Check circuit outputs against analytical reference states and suitable independent implementations.

## Quantum Dynamics Tests

Check numerical evolution against exact solutions for simple systems.

## Photonics Tests

Validate:

- Energy conservation in ideal lossless optical networks.
- Correct beam-splitter behavior.
- Interference phase dependence.
- Known diffraction limits.
- Appropriate power accounting for lossy components.

## Quantum Optics Tests

Validate:

- Photon-number probabilities.
- State normalization.
- Beam-splitter transformations.
- Expected HOM interference in ideal limiting cases.
- Coincidence statistics.
- Density-matrix physicality.
- Detector and loss-model behavior.

## Physical Quantum Lab Tests

Validate:

- Rabi oscillation limits.
- Ramsey phase behavior.
- Relaxation and dephasing dynamics.
- Population normalization.
- Appropriate state properties.
- Expected zero-noise behavior.

## Computational Controls

Track:

- Solver tolerances
- Time-step choices
- Mesh resolution
- Fock-space cutoffs
- Number of repetitions
- Simulation resource usage
- Numerical convergence
- Execution errors

Use actual data.

Never manufacture scientific performance results.

---

# PART 20 — HARDWARE INTEGRATION AND CLOUD EXECUTION

Support optional connections to actual quantum services only after local simulation is reliable.

Consider:

- IBM Quantum
- Amazon Braket
- D-Wave Leap
- Supported photonic quantum computing services where accessible

Actual quantum hardware jobs must require explicit approval.

Provide:

- Backend discovery
- Device metadata
- Availability
- Cost information where available
- Job submission confirmation
- Job tracking
- Result retrieval
- Error handling
- Hardware-versus-simulation labeling

Do not silently submit paid jobs.

Never imply that a virtual lab connects to physical quantum equipment unless the connection really exists.

Do not introduce automated control of real lasers, cryogenic systems, vacuum systems, high-voltage devices, or other physical equipment as part of the initial project.

Any future real laboratory-control integration must be independently designed, authorized, and reviewed for equipment-specific safety.

---

# PART 21 — FUTURE INTEGRATIONS

Design documented interfaces for optional use with my other projects.

## ChainMind

Potential future applications:

- Logistics optimization
- Warehouse scheduling
- Supplier allocation
- Inventory optimization
- Routing
- Risk-based resource allocation

## SRAI

Potential future applications:

- Satellite task scheduling
- Spacecraft resource optimization
- Optical communications simulations
- Quantum sensing research
- Mission-planning experiments

## NexusLab

Potential future applications:

- Reliability testing for AI experiment assistants
- Research-agent evaluations
- Verification of generated scientific claims
- Simulation reproducibility checks

Do not combine the projects into one repository automatically.

Do not change production systems.

Use versioned APIs and synthetic data for integration development.

---

# PART 22 — INTERFACE QUALITY REQUIREMENTS

The interface must look and behave like a professional scientific software product.

Use:

- Consistent typography
- Clear navigation
- Adjustable experiment panels
- Appropriate scientific diagrams
- Responsive layouts
- Accessible contrast
- Dark and light modes where feasible
- Accurate status indicators
- Helpful input validation
- Meaningful error messages
- Real loading states
- Exportable results

Avoid:

- Empty decorative dashboards
- Fake status indicators
- Placeholder buttons presented as functional
- Invented statistics
- Fake live telemetry
- Physically meaningless animations
- Repetitive AI-generated explanations without simulation
- Excessive dependencies
- Unnecessary redesigns

The visual sophistication must reflect actual working science.

---

# PART 23 — IMPLEMENTATION ROADMAP

Do not attempt to implement every feature simultaneously.

Prioritize complete working slices.

## Phase 1 — Repository Audit and Scientific Foundation

Inspect the existing project and preserve working code.

Set up or validate:

- Python scientific environment
- Frontend/backend communication
- Data schemas
- Automated tests
- Experiment storage
- Basic numerical plotting

**Required deliverable:** A working quantum experiment with executable code, valid results, and a reproducible saved run.

## Phase 2 — Virtual Physical Quantum Lab MVP

Build:

- Two-level quantum system
- Pulse controls
- Rabi oscillation experiment
- Basic relaxation/dephasing
- Virtual oscilloscope
- Measurement plots
- Experiment save/load

**Required deliverable:** Change a pulse parameter, execute a real numerical quantum-dynamics calculation, and observe the resulting simulated signal.

## Phase 3 — Virtual Photonics Lab MVP

Build:

- Interactive optical bench
- Optical source
- Mirrors
- Beam splitter
- Phase shifter
- Detector
- Classical interference simulation
- Optical result visualization

**Required deliverable:** Construct a Mach–Zehnder interferometer and show calculated output intensity changing with phase.

## Phase 4 — Quantum Optics MVP

Build:

- Single-photon input state
- Optical mode representation
- Beam splitter
- Photon detectors
- Measurement sampling
- Coincidence measurement
- HOM experiment

**Required deliverable:** Run an ideal two-photon interference experiment and compare the numerical result against its analytical limit.

## Phase 5 — Quantum Algorithms

Build or improve:

- Circuit editor
- Bell-state experiment
- Grover example
- QFT example
- VQE
- Small QAOA problem

Include correct backend selection and automated tests.

## Phase 6 — Quantum Optimization

Implement:

- Max-Cut
- QUBO
- QAOA
- Classical exact baseline
- OR-Tools where appropriate
- Benchmark plots
- Repeatable experiments

## Phase 7 — Quantum AI

Implement a small variational quantum classifier with a classical baseline and a proper held-out evaluation.

## Phase 8 — Advanced Physics and Photonics

Add:

- Ramsey
- Spin echo
- Tomography
- Cavity dynamics
- Waveguide models
- Selected FDTD experiments
- Integrated photonic circuits
- Squeezed-light experiments

## Phase 9 — Full Research Platform

Expand:

- Research notebook
- Experiment comparison
- Learning Academy
- AI copilot
- Optional hardware providers
- Scientific reporting
- Cross-project APIs

At the end of each phase, verify working functionality before starting the next one.

---

# PART 24 — FIRST REQUIRED END-TO-END BUILD

Begin with two scientifically meaningful demonstrations.

## Demonstration 1: Virtual Qubit Rabi Experiment

Create a working UI where I can:

1. Select a two-level system.
2. Choose a drive amplitude.
3. Set detuning.
4. Set pulse duration.
5. Configure relaxation and dephasing.
6. Run the physics simulation.
7. View qubit excited-state probability versus time.
8. Inspect pulse parameters.
9. Compare noiseless and noisy runs.
10. Save the experiment.

Use QuTiP or an equivalently validated solver.

Write tests against analytical behavior in simple limits.

## Demonstration 2: Virtual Optical Interferometer

Create a working UI where I can:

1. Select an optical source.
2. Place two beam splitters.
3. Configure optical paths.
4. Adjust relative phase.
5. Position detectors.
6. Execute the optical model.
7. View output intensities.
8. Inspect interference visibility.
9. Save the experiment.
10. Compare alternative phase settings.

Start with a validated classical optical model.

Extend to single-photon operation as a separate explicitly quantum model.

Do not label a classical wave simulation as a photon-counting quantum experiment.

These two demonstrations should prove that the new virtual laboratories have genuine computational engines.

---

# PART 25 — QUALITY ASSURANCE

Add automated tests covering:

- Quantum state normalization
- Correct gate matrices
- Hamiltonian construction
- Density-matrix validity
- Quantum evolution
- Pulse sequence behavior
- Optical component transformations
- Wave propagation assumptions
- Photon counting
- Detector efficiency
- Loss models
- Experiment serialization
- JSON export
- Parameter validation
- Error handling
- Scientific units
- Reproducible random seeds

Run tests before reporting success.

If a dependency is unavailable, implement only the physically valid supported subset and document the limitation.

Never claim that a planned module is operational.

---

# PART 26 — RESEARCH INTEGRITY

This project must follow strict scientific honesty.

Distinguish:

1. Analytical solutions.
2. Deterministic numerical simulations.
3. Monte Carlo simulated measurements.
4. Ideal quantum circuit simulation.
5. Noisy circuit simulation.
6. Classical electromagnetic simulation.
7. Quantum optical simulation.
8. Quantum-inspired classical algorithms.
9. Cloud simulation.
10. Actual quantum hardware measurements.

Display the relevant execution type prominently.

Never fabricate experimental observations.

Never claim that simulation results are proof of quantum advantage.

Never invent citations or research papers.

Do not present photonics animations as evidence of physical photon measurements.

Clearly describe model assumptions.

Report meaningful uncertainty and numerical limitations.

Use reproducibility as a central design principle.

---

# PART 27 — RESOURCE AND COST MANAGEMENT

Ensure the application is usable on an ordinary development computer for its initial experiments.

Provide:

- Memory estimates where feasible
- Qubit-count limits
- Optical-mode limits
- Fock-space cutoff limits
- FDTD grid limits
- Maximum runtime
- Job cancellation
- Background job status
- Clear failure messages
- Safe local defaults

Protect users from accidentally initiating computationally extreme simulations.

For expensive operations, warn before running and require confirmation when warranted.

Hardware execution must remain off by default.

---

# PART 28 — DEFINITION OF DONE

Do not report a feature as implemented unless:

- The code exists.
- The interface is connected to actual logic.
- Inputs affect calculations correctly.
- The operation can be executed.
- Results are displayed accurately.
- Error states are handled.
- Scientific validation has been performed to an appropriate level.
- Relevant automated tests pass.
- Documentation explains the functionality.

A beautiful interface without actual scientific execution is not complete.

A standalone numerical script without a usable experiment workflow is an incomplete application feature.

Both scientific correctness and practical usability matter.

---

# PART 29 — DEVELOPMENT COMMUNICATION

When working in Codex:

1. Start by inspecting my existing repository.
2. Summarize its actual capabilities and architecture.
3. Identify what can be reused.
4. Prioritize the first scientific experiment.
5. Make focused code changes.
6. Run available tests.
7. Fix failures.
8. Report exactly what changed.
9. Explain scientific assumptions.
10. List only genuine outstanding limitations.

Keep architecture and implementation decisions understandable.

Teach me the important engineering and physics concepts as you build.

Do not repeatedly ask whether to proceed with routine non-destructive work.

Do not request credentials or expensive hardware execution unless strictly necessary and authorized.

Do not stop at writing plans when implementation is possible.

---

# FINAL MASTER INSTRUCTION

Transform Quantum Lab into an advanced integrated research platform combining:

**Quantum Computing + Experimental Quantum Physics + Photonics + Quantum Optics + Quantum AI + Quantum Optimization + Scientific Simulation + Interactive Learning.**

The software should support meaningful virtual experiments and reproducible scientific investigation.

I want to use it to:

- Learn the mathematics.
- Understand experimental quantum physics.
- Understand how physical quantum hardware operates.
- Build and simulate optical experiments.
- Experiment with photonic quantum computing.
- Develop quantum algorithms.
- Research hybrid quantum AI.
- Compare quantum and classical optimization.
- Explore aerospace and industrial applications.
- Build real scientific software engineering skills.
- Eventually develop original research projects.

Treat the Quantum Lab as a serious long-term software and research undertaking.

**IMMEDIATE EXECUTION ORDER:**

Inspect the existing repository, preserve working features, verify current dependencies, and implement the smallest fully working Virtual Physical Quantum Lab experiment and Virtual Photonics Lab experiment.

Start with:

**A. A simulated Rabi oscillation experiment using a two-level quantum system.**

**B. A simulated Mach–Zehnder optical interferometer with adjustable phase.**

Make both executable through the existing application, validate their results, save experimental records, and run automated tests.

Then proceed incrementally toward the rest of the platform.

Prioritize actual science over simulated sophistication. Build a real foundation that can grow into an advanced quantum research laboratory.