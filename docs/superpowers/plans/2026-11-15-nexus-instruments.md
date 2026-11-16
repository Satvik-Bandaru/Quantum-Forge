# Nexus Connected Instruments Implementation Plan

> **For agentic workers:** Use the development and verification workflows; the user has explicitly authorized autonomous execution in this session.

**Goal:** Make one fully connected, persistent, scientifically validated quantum-instrument experiment available in the existing lab.
**Architecture:** Typed Python apparatus models and a piecewise Lindblad engine feed the existing isolated job worker and SQLite history. A separate React workspace configures instruments and renders returned evidence; Main Lab and existing modules remain intact.
**Tech Stack:** Existing React/TypeScript/R3F, FastAPI/Pydantic, NumPy/SciPy, SQLite, pytest, Playwright.
**Spec:** ../specs/2026-11-15-connected-instruments-design.md

## Constraints

No new paid infrastructure, no invented measurements, no destructive reset of the existing uncommitted work. One bounded CPU job at a time. All unit conventions and approximations explicit. All files remain in the current project so the user's running application receives the implementation.

## Review focus

Disconnected or incompatible ports; stale saved configurations and stale plots; finite-temperature rate/unit/sign errors; calibration mistaken for physical hardware calibration; API cancellation, overload, malformed input and saved-history replay.

## Tasks

- [x] 1. Baseline: verify installed dependencies, all existing 215 Python / 26 UI tests, build, startup and 3D interactions. Preserve logs. Add portable CI and regression command.
- [x] 2. Core instrument and sequence engine: write failing independent analytic/physicality/thermal/readout/connection/fault/convergence/seed tests; implement backend/instruments.py and backend/connected.py; verify component suite. Document sources and exact contract.
- [x] 3. API/persistence: write failing tests for typed connected jobs, apparatus revisions, invalid state, exports, restart and resource policy; implement store/app/jobs integration without breaking existing kinds.
- [x] 4. Frontend: implement typed controls, ports, states, calibration/run plots, saved apparatus, History restoration and 3D module entry. Browser-test actual changed control -> changed backend output, fault handling, save/reload and mobile layout.
- [x] 5. Scientific review and full regression: independent review, resolve material findings, run full Python/build/browser checks; record actual measurements/screenshots and limitations in DEVELOPMENT_BACKLOG.md, SCIENTIFIC_VALIDATION.md, BUILD_STATUS.md and NEXT_SESSION.md.
- [x] 6. Select next highest-value unblocked milestone: bounded error correction and single-photon optics with independent references, tests and integrated workflows, or fix new verified defects first. Keep unimplemented facility capabilities clearly planned.

## Execution ledger

2026-11-15: Existing Main Lab implementation is uncommitted on feat/main-quantum-lab. Work continues in-place to preserve the user's integrated app. Baseline agent owns CI and baseline evidence; science agent owns new physical core; UI agent owns new workspace; root owns integration and validation records. No blanket design-approval pause: autonomous continuation is explicitly authorized by the user's directive.

P0 complete: dependencies verified, baseline 215 Python / 26 browser/build/startup passed; portable CI and isolated regression runner added.
New scientific/API tests: 128 passed (2.82s). Connected core 63 + research 56 + API 9. Connected browser 5 passed, 17.5 s and research browser 3 passed, 8.6 s before final whole-suite verification.
Independent review: physical detuning, thermal model, finite pulses, eight-dimensional QEC and photon vacuum channel checked; randomized independent QEC/photon references agreed within4.44e-16 and 1.11e-16. Material finding: apparatus revision refreshed on navigation without matchingdraft. Fixed by retaining draft/base revision together inApp; navigation-conflict browsercase passes. Initial unsavedtimestamp now explicit ratherthanepoch; initialmetadata loading guard receiving additional coverage. No physical hardware accuracy or large-facility completeness claimed.
Next bounded milestone selected after foundation verification: completed real quantum density models for basic repetition-code errorcorrection and single-photon optics. Both integrated through existing jobs/history/export, with separate working workspaces and MainLab links.

Final whole regression: bash scripts/check-regression.sh exited0;343Pythonpassed11.42s, buildpassed3.09s,35browserpassed1.6min. The temporary server/database shut down cleanly. User instance restarted atv0.5.0. Both reviewer findings and delayed-initial-load race are fixed; no important review finding remains. No remote CI execution or full research-facility completion is claimed.
