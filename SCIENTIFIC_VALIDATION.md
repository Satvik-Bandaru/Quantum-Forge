# Scientific validation ledger

## Interpretation

This application performs classical CPU simulations. Numerical agreement with mathematical references does not establish physical-device accuracy. Educational equipment and photographs are distinct from measured simulation outputs. No hardware calibration has been performed.

## Existing verified models

- `docs/rabi-model.md`: rotating-frame driven two-level system, constant Lindblad generator, analytic resonant/detuned Rabi and T1/T2 references; density trace, Hermiticity and positivity tests.
- `docs/mzi-model.md`: classical coherent optical amplitudes, loss and optical power; this is not a single-photon experiment.
- `docs/qubo-model.md`: bounded optimization with exact reference and objective consistency.
- `docs/virtual-computer.md`: ideal states and final noisy sampled counts are explicitly distinct.
- Baseline215 Python tests and26 browser tests passed2026-11-15; raw evidence is in `docs/verification/`.

## Connected bench — implemented and component-validated

See [full equations, conventions and sources](docs/connected-model.md). Five typed instruments and five directed signal links determine one finite-temperature, rotating-frame two-level experiment. The basis is ground |0>, excited |1>, with Z = diag(1,−1); stored detuning is device minus source, so the Hamiltonian has −detuning × Z. Time is µs, drive/detuning MHz, absolute carrier GHz, bath temperature K.

- Exponential cooldown advances only through explicit simulated elapsed time. Temperature fixes Gibbs initialization and bosonic upward/downward rates with detailed balance.
- Microwave power after line attenuation determines field drive through the declared device coupling. Pulse phase/duration and source/device frequency change actual segment propagators.
- Finite square pulses include detuning and decoherence throughout Rabi, Ramsey, echo, T1, frequency and amplitude sweeps. Readout applies a confusion channel followed by seeded binomial trials.
- Readout calibration prepares ideal synthetic |0> and |1>; estimates and plug-in standard errors identify the configured assignment model only. No physical device was calibrated.
- 63 component tests cover analytical Rabi/thermal/T1/Ramsey/echo references, physical sign/phase, an independently coded DOP853 ODE, subdivision consistency, maximal bounded requests, density finiteness/trace/Hermiticity/positivity, faults, ports, seeds and failed numerical propagation.
- Same-method subdivision is explicitly a floating-point consistency check, not an independent error estimator. Dense sampling may still miss oscillations; the result and UI show resolution warnings.

[Real browser control comparisons](docs/verification/nexus-connected-controls.json) contain full returned records for power, detuning and temperature changes. The visible in-app Ramsey run [96e7ff4b](docs/verification/nexus-native-ramsey-run.json) executed 101 ensembles × 1024 shots at source 5.0003 GHz, device 5 GHz. Numerical checks passed; model runtime 0.0240 s, worker wall 0.2464 s, worker high-water RSS 62,291,968 bytes (~59.4 MiB). These are actual observations, not performance guarantees.

## Quantum research — implemented and component-validated

See [quantum channel definitions and primary references](docs/research-models.md).

- Bit-flip QEC: encode arbitrary α|0>+β|1> into 8-dimensional space, apply all eight independent X-error patterns, parity projectors and ideal recovery, then decode/partialtrace. The independent logical probability is pL=3p²−2p³; arbitrary-state fidelity is compared with the logical mixture, not equated to1−pL for every input. Pattern/syndrome/logical error counts and computational-basis measurements have distinct meanings. No general-noise protection or noisy-syndrome performance is claimed.
- Photon optics: propagate vacuum plus two one-photon modes, apply complete-positive path dephasing, unequal arm loss and detector inefficiency. Optical population and detector outcomes conserve probability; counts sum to exactly the submitted trials. Loss and missed detection are separate. Classical-looking fringe shape alone is not evidence of nonclassical light.
- 56 tests cover independent polynomials, complex states, interference amplitudes, complete loss, disabled detectors, endpoint channels, density physicality, seeds and request bounds. Exact 101-point reference sweeps are not additional sampled measurements.
- Independent review additionally checked 30 randomized QEC and 30 photon cases: maximum deviations 4.44e−16 and 1.11e−16 respectively.

## Persistence, failures and resource evidence

Nine new API tests execute real workers, verify immutable history/CSV/JSON, restart persistence, invalid inputs, graph interlocks, cancellation and explicit local compute policy. Apparatus saves use transactional optimistic revisions. Browser regressions cover a second session saving while a draft navigates away/back, and delayed initial loading; an older draft cannot silently acquire a newer base revision.

Every completed worker records wall time and process high-water RSS, including imports. Connected results separately record model time and a current RSS snapshot; these labels are not interchangeable. Existing watchdog time/memory bounds and single-job concurrency remain. `/api/compute/policy` declares two free local categories and an inactive remote boundary; no accounts, metering charges, payments or remote services exist.

## Remaining scientific limits

No calibrated hardware accuracy is established. The connected model excludes multilevel transmon leakage, pulse distortion, non-Markovian noise and correlated environments. Cryogenic cooldown supports the legacy first-order model and the new constant-coefficient lumped thermal network; neither is calibrated refrigerator thermodynamics. The photon model excludes source imperfections, dark counts, detector timing and multiphoton/HOM effects. Materials science, noisy repeated QEC and inference with uncertain nuisance parameters remain backlog items. Final integrated build/test evidence is recorded in BUILD_STATUS.md.

## Final integrated verification

On 2026-11-15, the complete regression passed: 343 Python tests, 35 browser tests, dependency checks, production build and isolated backend startup. See BUILD_STATUS.md and docs/verification/nexus-final-*.log. The prior215/26 baseline and all new tests are included; no separate full-platform/hardware validation is implied.

## v0.6 connected thermal and calibration extension

See docs/thermal-model.md for the three-node energy equations, capped cooling, fixed room boundary and numerical limits. Twenty-two added thermal/signal tests verify independent exponential/linear limits, isolated equilibrium, energy conservation, DOP853 agreement, tolerance refinement, boundary behavior, faults and declared signal provenance. The calculated mixing-chamber temperature drives existing Gibbs populations and thermal transition rates. No heat is silently inferred from microwave attenuation.

Twenty added calibration tests cover a separate analytical damped Bloch formula, sampled-count likelihood recovery, fixed-seed repeatability, changed power, Wilson intervals including zero/all-success counts, conditional confidence intervals, invalid/weak/unbracketed fits, optimizer failure, undersampling aliases and subnormal ranges. Dephasing uses actual finite Ramsey pulses; its ideal instantaneous-pulse T2 reference is an approximation comparison, not a fitted Tphi measurement.

Eight new integration tests cover numerical failure without apparatus mutation, CSV physical evidence, connected timeout lifecycle, worker numerical failure, actual thermal jobs and exact saved replay, both new protocols and legacy configs. Latest complete verification: 393 Python tests passed in 16.66 s,40 browser tests passed in 2.0 minutes, production build passed in 3.18 s, and the actual v0.6 launcher/live backend completed a saved Bell run. The former approval-review blocker was resolved through normal approval. Independent whole-phase review remains separate from these verified execution checks; see BUILD_STATUS.md.

Pulse-calibration uncertainty is conditional on the declared temperature, coherence and assignment parameters; it excludes their uncertainty and model discrepancy. The conservative resolution guard deliberately declines calibration for undersampled acquisitions even when a low-frequency aliased likelihood fits well. Physical parameter uncertainties remain unknown/null until evidence supports an estimate; numerical tolerances are not physical error bars.
