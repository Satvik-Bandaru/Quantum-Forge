# Connected thermal laboratory implementation plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans. Preserve existing changes; no reset or automatic commit.

**Goal:** Complete the connected physical workflow using validated thermal dynamics, calibration evidence and contextual equipment controls.

**Architecture:** Extend existing Pydantic instruments and SciPy solver; retain the legacy cryostat default for compatibility. Independent backend modules feed the existing React instrument interface and immutable experiment history.

**Tech stack:** Python/FastAPI/Pydantic/SciPy/SQLite, React/TypeScript/R3F, pytest/Playwright.

**Spec:** `docs/superpowers/specs/2026-11-15-connected-thermal-v06-design.md`

## Constraints and review focus

- No calibrated hardware claim, new external service, billing, or dependency unless necessary.
- Preserve old snapshot replay and live SQLite data.
- Reject nonfinite/out-of-model thermal states; do not hide failures by clipping.
- Zero elapsed time, zero cooling/coupling, extreme supported loads and changed connections require meaningful behavior.
- Calibration with insufficient contrast or sampled boundary counts must report uncertainty or failure honestly.
- Comparison must identify runs and distinguish different axes/configurations; navigation must not overwrite drafts.

## Milestones

- [x] Baseline: dependency checks, 343 Python tests, build, startup and 35 browser tests via isolated regression runner. Evidence: `docs/verification/phase6-baseline/`.
- [x] Thermal/instrument backend: test first in `tests/test_thermal.py` and instrument tests; implement `backend/thermal.py`, extend `backend/instruments.py` without changing legacy results. Expose serializable thermal evidence and typed input/output/calibration/uncertainty state; document equations in `docs/thermal-model.md`.
- [x] Calibration engine: write failing analytical, finite-shot and failure tests; extend `backend/connected.py` with explicit dephasing/amplitude-calibration protocols and sample-derived estimates; provide uncertainty intervals and model/reference labels. Document in `docs/connected-model.md`.
- [x] Connected UI: extend `frontend/src/connected/` types and controls, stage results, calibration/signal evidence and pinned comparison. Add contextual equipment targets in `App.tsx` and `main-lab/MainQuantumLab.tsx`. Add browser tests proving actual backend behavior and history replay.
- [ ] Integration: add API persistence/replay/failure tests for new models; run full suite and independent scientific/code review, fix actual defects.
- [ ] Delivery: verify live startup and browser workflow, record screenshots and run evidence, update four status/handoff files, refresh and independently verify downloadable ZIP.

Each implementation milestone follows failing test → minimal implementation → targeted passing tests. The final isolated regression runner validates all integrated source before completion claims.

Current checkpoint:393Python tests and productionbuild pass. UI source and five new tests are implemented; final browser/regression/review/live startup/delivery promotion remain pending after an approval-review usage failure. See BUILD_STATUS.md and NEXT_SESSION.md.

2026-11-15 runnable verification: full393 Python / 40 browser regression, build, dependencies and actual user launcher / Bell run passed. Four status documents and main macOS download refreshed. Independent whole-phase review remains pending separately; no complete hardware validation claim.
