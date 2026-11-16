# Build status — Quantum Forge v0.6, runnable and verified locally

Verified 2026-11-15. Branch `feat/main-quantum-lab`; changes remain local and uncommitted, with no GitHub push in this phase.

## Startup and complete regression

The actual `./start.command` launcher started the user instance at http://127.0.0.1:8777/. `/api/health` reports version 0.6.0 and ready. The in-app browser loaded the 3D Main Lab, selected the quantum computer and executed a Bell experiment through Python. The result was saved in the user's existing SQLite history; previous records were preserved.

`QF_REGRESSION_ARTIFACTS=docs/verification/runnable-2026-11-15 bash scripts/check-regression.sh` completed with exit 0:

- **393 Python tests passed in 16.66 s.**
- **40 browser tests passed in 2.0 minutes.** All existing modules and five new thermal/context/comparison/calibration workflows are included.
- TypeScript/Vite production build passed in 3.18 s.
- Python and npm dependency checks passed; no installation or new dependencies were needed.
- The regression's own temporary backend/database started as 0.6.0 and was cleaned up; it did not replace user history.

Logs: `docs/verification/nexus-runnable-{pytest,playwright,build,health,pip-check,npm-ls,server}.log`. Live health: `nexus-runnable-live-health.json`. The prior approval-review usage failure is resolved for these actions; no restriction was bypassed.

## Visible live experiment

Run `6ebe7a33-8e07-4bba-bf8a-b5138666fd01`: Bell state, 1,024 shots, seed 42, counts 00 = 526 and 11 = 498, Qiskit Aer local CPU. Full returned record: `docs/verification/nexus-runnable-live-bell.json`. Screenshot: `docs/screenshots/nexus-runnable-bell.jpg`.

The browser suite also verifies all five equipment selections, camera navigation, low-graphics mode, real local asset loading/retry, Photonics, connected instrument control sensitivity, faults, readout intervals, conditional amplitude calibration, dephasing, pinned comparisons, persistence and exact seeded thermal-run replay. Updated thermal evidence/screenshots are in `docs/verification/nexus-thermal-workflow.json` and `docs/screenshots/nexus-thermal-laboratory.png`.

## Reopening and downloading

Double-click `start.command` in the project or extracted download. Keep its Terminal window open while using the lab; Ctrl+C stops it. It opens an existing lab on 8777 when one is already running. Stop an older instance first if you intend to run another extracted version.

The macOS ZIP contains source, prebuilt frontend, local assets, executable launcher and handoff documents. It requires Python 3.12 and internet for first-time dependency installation; Node is not needed to use the included build. This is an unsigned source distribution, not a self-contained signed macOS app. The previous verified 0.5 archive is retained separately when refreshing the main download.

## Remaining boundaries

No physical hardware or paid service is connected. Thermal coefficients and two-level dynamics are educational approximations; calibration confidence assumes the declared nuisance settings. See SCIENTIFIC_VALIDATION.md for explicit scientific limits.

A separate independent whole-phase scientific/code review remains a development backlog item; startup/package review and the complete numerical/browser regression are verified. Hosted GitHub CI has not been run. Nonblocking advisories remain: large lazy Three.js bundle and upstream Three.Clock/Starlette deprecations.
