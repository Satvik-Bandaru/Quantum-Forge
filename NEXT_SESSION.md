# Next session — runnable v0.6 handoff

Project: `/Users/satvikbandaru/Documents/AI and Database Projects/quantum-forge-lab`.
Branch `feat/main-quantum-lab`, base d431825162b70f357b2737137b36afdf7e870e8f. Preserve all uncommitted Main Lab/v0.5/v0.6 source and user SQLite history. No commit or push has occurred.

## Verified checkpoint

2026-11-15: complete isolated regression passed 393 Python tests, 40 browser tests, TypeScript/Vite build, dependency checks and backend startup. Logs: docs/verification/nexus-runnable-*.log. Read BUILD_STATUS.md and SCIENTIFIC_VALIDATION.md.

Actual `./start.command` was launched successfully. User backend v0.6.0 is ready on http://127.0.0.1:8777/ (PID 86472, exec session 95942 at verification; identify actual process again before any restart). The in-app browser shows a completed saved Bell run 6ebe7a33-8e07-4bba-bf8a-b5138666fd01, counts 00 = 526 and 11 = 498 from 1,024 shots. Full record and screenshot are saved under docs/verification/nexus-runnable-live-bell.json and docs/screenshots/nexus-runnable-bell.jpg. User history is preserved.

The earlier approval-review usage failure is no longer blocking: startup, health and full isolated browser tests were approved and executed normally. Do not treat the historical blocker as current or bypass future review failures.

## Running and packaging

`./start.command` starts the service and opens the browser, or opens an existing instance on 8777. Keep the launcher Terminal open; Ctrl+C stops it. If an older version already occupies 8777, stop that identified instance before running another copy. The launcher does not distinguish versions/folders of an already-running lab.

`bash scripts/check-regression.sh` verifies with an isolated temporary server/database and cleans up. Run sequentially: rebuilding assets alongside Python API tests can create transient missing-directory failures.

`python3 scripts/package-macos.py` refreshes `../Quantum Forge Downloads/Quantum-Forge-Nexus-Lab-macOS.zip` after source/docs/build settle. The package includes prebuilt v0.6 assets and excludes personal DBs, environments and dependencies. Python 3.12 and first-setup internet remain prerequisites. Preserve the older v0.5 archive backup.

## Remaining development

The requested runnable state is achieved. A fresh independent whole-phase review remains useful before further scientific expansion, especially thermal model boundaries, calibration identifiability/uncertainty and signal-state semantics. After review: nuisance-aware calibration/T1 inference, microwave heating feedback only with explicit assumptions, or bounded materials/device characterization. Do not add decorative rooms or paid infrastructure.

Retain legacy exponential defaults/history compatibility, error-before-save behavior, immutable pin snapshots, matching-axis comparison, honest unavailable signals, field-resolution and subnormal calibration guards, and paired draft/revision loading. All 393 tests and 40 browser workflows currently pass. No work is promised after this session ends.
