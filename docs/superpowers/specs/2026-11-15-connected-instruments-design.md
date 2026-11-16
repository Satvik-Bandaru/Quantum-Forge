# Nexus Lab: connected physical instruments

The user explicitly authorized autonomous development in the current session, beginning with verification. Preserve the existing Main Lab, Photonics, physics, circuits, history and optimization modules. This design records implementation choices rather than claiming hardware calibration.

## Approach and first bounded milestone

Extend the existing local FastAPI job/persistence architecture and SciPy two-level Lindblad solver. A separate Connected Instruments workspace models one superconducting qubit bench with a dilution refrigerator, microwave source, pulse sequencer, device and binary readout. Reuse existing packages; add no paid infrastructure. A general arbitrary-circuit simulator for instruments would be premature, while purely visual controls would not satisfy the request.

The instrument schema is authoritative in Python, rejects unknown/nonfinite/out-of-bound inputs, and exposes identities, typed ports, limits, configurations, status and faults. Only compatible directed links are accepted. Missing required links, disabled instruments and injected faults prevent acquisition with explicit reasons. Saved apparatus state has an optimistic revision in SQLite. Every experiment separately stores an immutable full apparatus snapshot and seed.

The refrigerator uses an explicit simulated elapsed time and a first-order thermal relaxation approximation. Temperature sets the qubit's Gibbs population and finite-temperature upward/downward Lindblad rates, using declared device frequency and zero-temperature T1. Microwave power and pulse amplitude determine drive amplitude through a declared model coupling; source/device frequency sets detuning. Piecewise square pulses drive Rabi, Ramsey and echo sequences. Readout assignment errors transform the physical excited-state probability before seeded binomial sampling. No control changes a fictitious reading.

Add time, frequency and amplitude sweeps, T1 and readout calibration. Calibration is a synthetic experiment under explicit preparation assumptions, not evidence for a physical device. Preserve deterministic density predictions separately from sampled measurements. Verify exact segment exponentials with subdivision consistency and an independent ODE reference in tests. Enforce physicality on all outputs. Record measured runtime and process memory with their meaning and bounds.

## User flow

Main Lab equipment inspectors retain their existing links and gain a Connected Instruments entry. The new workspace presents a signal-chain diagram, selectable instrument controls, editable validated port connections, actual operational states, save/reload, run configuration and measured-result plots. Controls are in normal document flow, responsive on mobile. Saved runs reopen from History and show stale-result notices after configuration edits.

## Validation and later milestones

P0: dependency checks, all existing backend/browser tests, build/startup and actual 3D clicks; establish automatic CI. P1/P2: independent component tests, API persistence/fault/limit coverage and end-to-end connected acquisition. P3: validate Ramsey/echo, calibration and sweeps; then add bounded basic error correction and quantum single-photon experiments if session capacity permits. P4 adds only laboratories supported by functional experiments; materials research remains planned until a validated model exists. P5 records local educational vs advanced bounded budgets and a future provider interface, without accounts/payments/services.

Non-goals: manufacturer digital twins, multilevel transmons, refrigerator thermodynamics from first principles, microwave transmission-line electromagnetics, physical QPU execution, arbitrary lab networks, actual calibration accuracy and hidden background compute. All omissions remain labeled in results and SCIENTIFIC_VALIDATION.md.
