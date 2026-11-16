# Nexus Lab development backlog

Last updated: 2026-11-15. Continue the existing Quantum Forge application; no replacement project.

## Current milestone sequence

- M0 complete: approved v0.6 snapshot `701f87a`, guidance/audit checkpoint `0eb18ac`, 393 Python and 40 browser tests verified; original data and historical evidence preserved.
- M1 locally verified: independent bounded NumPy circuit references, 248 reference tests, 300 ideal and 30 noisy comparisons, metamorphic and mutation/import checks. Full suite: 641 passed in 24.86 s. Publication is separately verified after the authorized push; see BUILD_STATUS.md and the final report.
- Next is M2, only after user review/go-ahead: targeted localhost security and storage hardening from `docs/codex/MASTER_PROMPT.md`. User database migrations require explicit approval; preserve compatibility and backup first.
- M3 readability, M4 nuisance-aware inference, M5 blind-device challenges and M6 scaling remain separate future milestones. Optional dependencies and paid/cloud services are not authorized by this milestone.

Earlier development priorities and checkpoints below are historical context. Use the current M0–M6 sequence rather than skipping directly to new inference or facility modules.

## Verified foundation

- Main Quantum Lab: navigable R3F equipment, real local photos and labeled concept references; Bell runs through Python and persists in SQLite.
- Circuit/virtual computer/general experiments, two-level Rabi Lindblad model, classical photonics and optimization remain functional.
- Priority zero baseline: dependencies clean, production build, 215 Python and 26 browser tests passed on this session's untouched baseline. Logs: `docs/verification/nexus-baseline-*`.

## Implemented milestone: connected superconducting-qubit bench

- Typed cryostat, microwave source, pulse controller, two-level device and binary readout, connection ports, limits, states and injected faults.
- Persistent editable apparatus, immutable run snapshots, validation before acquisition, explicit virtual cooldown time.
- Thermal initialization and detailed-balance relaxation; power/frequency/pulse/readout controls determine computed probabilities.
- Rabi, Ramsey, echo, T1, frequency/amplitude sweeps and synthetic readout calibration.
- Independent analytic/ODE/convergence/physicality tests, real backend job + History/export browser workflow.
- Local resource metering and automatic CI regression; no paid services, accounts or remote compute.

## Implemented next milestone: bounded quantum research

- Three-qubit bit-flip repetition code: actual encoding, independent X channel, parity projection, recovery and decoding, with analytic logical-channel and arbitrary-state fidelity checks.
- Single-photon Mach–Zehnder density matrix: coherent paths, phase damping, unequal loss/vacuum, detector efficiency and exclusive counts. Existing classical photonics remains separate.
- Both expose numerical results, seeds, history/export and actual worker resource measurements. Browser tests change controls and reopen saved results.

Final integrated verification: **343 Python / 35 browser tests passed**, with production build, startup and dependency checks. See BUILD_STATUS.md.

## Next highest-value tasks

1. Noise inference / calibration uncertainty: fitted parameters and identifiability, synthetic reference datasets, uncertainty intervals and independent validation.
2. Device characterization: only add a facility workspace when supported by a validated experiment. Connected bench currently combines cryogenics, microwave control and acquisition; these are not independent hardware simulations.
3. Materials research: choose a bounded validated Hamiltonian and analytical reference before introducing a room/module.
4. Compute service extension: provider boundary and explicit budget/consent, only after separate authorization; payments remain out of scope.

5. Two-photon HOM with a documented mode-overlap model and independent tests; noisy syndrome cycles/general-error codes only with explicit failure models.

## Existing nonblocking limitations

Large lazy-loaded Three.js bundle, upstream Three.Clock and Starlette/httpx deprecations. Educational models are not manufacturer CAD or calibrated physical equipment. No physical hardware connected.

## Current phase: v0.6 runnable and regression-verified

Implemented: multistage thermal network/energy balance; typed physical/signal/calibration/uncertainty snapshots; conditional sampled pulse-amplitude calibration; explicit dephasing/T2 reference; Wilson intervals; equipment-specific controls; immutable pinned comparison; numerical error-before-save and extended CSV evidence.

Verified 393 Python tests, 40 browser tests, production build, dependency checks, isolated startup and real user-instance launcher/health. A visible Bell experiment completed and persisted. Main Lab, Photonics and earlier modules remain covered by the complete suite. See BUILD_STATUS.md for logs and actual run evidence.

Next: independent whole-phase scientific/code review before additional inference or facility expansion. Then nuisance-aware calibration/T1 inference, documented microwave heating feedback, bounded device/materials characterization, HOM or noisy QEC. Remote compute/billing remain disabled.
