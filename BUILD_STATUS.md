# Build status — Quantum Forge v0.6 with M1 reference validation

Updated 2026-11-15. M0 preserved v0.6 in local commits `701f87a` and `0eb18ac`. M1 uses branch `codex/m1-independent-reference` from `0eb18ac`; the user explicitly authorized publication to GitHub. Publication is verified separately after the M1 commit.

## M1 — Independent circuit references

Added bounded NumPy statevector/density references, 248 component/differential/metamorphic/import tests, fixed-seed reports, and documented statistical methods. Production application execution, API, worker/store logic, frontend, dependencies and user data are unchanged.

- `.venv/bin/python -m pytest -m reference -q`: **248 passed, 393 deselected, 1 warning in 12.37s**, exit 0.
- Explicit amplitude-sign and noise-oracle mutation guards: **2 passed in 0.71s**, exit 0.
- 300 ideal circuits: max phase-aligned amplitude error **1.5463617361248926e-15**; max norm deviation **1.5543122344752192e-15**.
- 30 noisy Aer comparisons: **0 Holm rejections** at family alpha 0.001; minimum adjusted p **0.725540558978316**. Minimum expected count **203.72163049717665**, minimum observed count **213**. Seeds and thresholds were not tuned after outcomes.
- `.venv/bin/python -m pytest -q`: **641 passed, 1 warning in 24.86s**, exit 0. `/usr/bin/time -l` reported **25.38s wall time**, **294,043,648 bytes maximum resident set size** (~280.4 MiB), and 239,289,400 bytes peak memory footprint. These are whole pytest-process measurements including imports, not per-model allocation or aggregate concurrent-worker memory. The full suite remains below the approximately 60-second target on this Mac.

Evidence: `docs/verification/codex-m1-reference/`; methods: `docs/VALIDATION-PLAN.md`. The first instrumented reference run passed all 248 tests in 10.60s, but macOS `/usr/bin/time -l` exited 1 because the sandbox denied its `sysctl kern.clockrate` query. The plain pytest retry above succeeded; the full-suite measurement uses scoped permission. Both records are retained.

M1 changes no API/job/store/UI code, so the build and browser suite were not rerun locally for this milestone. The latest complete application regression remains **M0: 393 Python tests, 40 browser tests, production build and isolated startup passed**, with evidence in `docs/verification/codex-m0-baseline/` and `docs/AUDIT-2026-11.md`. GitHub CI results, if triggered, must be distinguished from these local results.

## Historical v0.6 startup and integrated verification

The following records describe the earlier runnable v0.6 checkpoint; they are retained as historical evidence, not new M1 executions.

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

M1 independently checks the circuit/reference scope; a whole-phase scientific review of thermal/calibration and other models remains broader work. The prior runnable checkpoint had no hosted GitHub CI result; any new publication result is recorded separately. Nonblocking advisories remain: large lazy Three.js bundle and upstream Three.Clock/Starlette deprecations.
