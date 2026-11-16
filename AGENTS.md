# AGENTS.md — Quantum Forge / Nexus Lab

Local-first educational quantum laboratory: FastAPI + spawned CPU worker + SQLite backend (`backend/`), React 19 / TypeScript / Vite / React Three Fiber frontend (`frontend/`). Version 0.6.0. Single trusted local user on 127.0.0.1:8777. Classical simulation only — never claim hardware accuracy, quantum advantage or calibrated devices.

## Hard rules
- Work on a feature branch (`codex/<milestone>-<slug>`). Never commit to `main`, never push, never open PRs, never force-push or rewrite history unless the user explicitly asks in this chat.
- Ask before: deleting/moving files, `git reset --hard`/`clean`/`checkout --` on dirty files, schema or file-layout changes, adding ANY dependency (Python or npm, including dev tools), network access, writing outside this repo.
- Never touch other repositories or folders (SRAI, ChainMind, VectorForge, Orbital Forge, other Quantum Forge copies, `../Quantum Forge Downloads/`). Never import from them.
- No paid services, accounts, API keys, telemetry, remote compute or deployment. Keep `/api/compute/policy` remote/payments disabled.
- Never fabricate results, test counts, timings, versions or citations. Paste the real command output. If something was not run, say "not run".
- Never delete or rewrite user data: `data/*.sqlite3*`. Tests must use temporary DBs (`create_app(db_path=tmp)`), as existing tests do.
- Do not edit historical evidence in `docs/verification/` or `docs/screenshots/`; add new dated files instead.
- Do not weaken limits, validation, physicality checks or tests to make something pass. A failing scientific check is a finding — report it.

## Layout
- `backend/app.py` routes + loopback Host/Origin middleware; `http_limits.py` 256 KB body cap; `jobs.py` one spawned worker, timeout, RSS watchdog; `store.py` SQLite JSON documents; `models.py` request schemas and caps.
- Science: `quantum.py` (Qiskit/Aer circuits), `experiments.py` (11 algorithms), `machine.py` (assembly/QASM subset), `physics.py` (two-level Lindblad), `connected.py` + `instruments.py` + `thermal.py` (connected bench), `research.py` (bit-flip code, single-photon MZI), `photonics.py` (classical MZI), `science.py` + `qubo.py` (optimization/QUBO).
- Tests: `tests/` (pytest, 712 cases including 248 marked `reference`), `frontend/tests/` (Playwright, 40 tests). Docs: model equations in `docs/*-model.md`; status in `BUILD_STATUS.md`, `SCIENTIFIC_VALIDATION.md`, `DEVELOPMENT_BACKLOG.md`, `NEXT_SESSION.md`.
- Independent circuit references: `backend/reference/` (NumPy, 8-qubit pure / 6-qubit density caps); scientific comparison methods and seeds in `docs/VALIDATION-PLAN.md`. No imports from production execution, Qiskit or PennyLane in the reference package.
- `frontend/dist/` is build output (gitignored) — never hand-edit.

## Commands (macOS: Python 3.12, Node 22.12+)
- Setup (needs network → ask): `python3.12 -m venv .venv && .venv/bin/python -m pip install -r requirements.lock.txt && npm --prefix frontend ci`
- Python tests: `.venv/bin/python -m pytest -q`
- Frontend build/type-check: `npm --prefix frontend run build`
- Full regression (isolated temp server + DB, then Playwright): `bash scripts/check-regression.sh`
  - Linux/cloud: `PLAYWRIGHT_BROWSER=chromium QF_PYTHON=.venv/bin/python bash scripts/check-regression.sh` (Chromium must be installed in setup: `(cd frontend && npx playwright install --with-deps chromium)`).
  - Run sequentially; do not rebuild assets while Python API tests run.
- Never stop or restart the user's running instance on port 8777; the regression script uses its own ephemeral port.

## Scientific conventions (do not change silently)
- Bit order: leftmost bit is q0 everywhere in UI/exports; Qiskit little-endian is reversed at the boundary.
- Units: time µs, frequency MHz (cycles/µs), carrier GHz, temperature K, optical power mW, angles rad unless explicitly suffixed `_deg` (connected microwave/controller phase inputs use degrees).
- Basis |0> ground, Z=diag(1,-1). Connected bench: detuning = f_device − f_source, H/ħ = π(−δZ + Ω(cosφX + sinφY)). Physical lab: +ΔZ (documented separately).
- Keep ideal vs noisy vs sampled results distinct; keep every `limitations` list accurate; keep error-before-save, immutable pinned snapshots, legacy history compatibility.
- Every new model needs an independent analytic or reference test that does not import the production code path it checks.

## Definition of done (for every task)
1. `.venv/bin/python -m pytest -q` all green (state the count).
2. `npm --prefix frontend run build` exits 0 if any frontend file changed.
3. `bash scripts/check-regression.sh` exits 0 for any change touching API, jobs, store or UI (or say why it could not run).
4. Milestone acceptance command(s) pasted with real output.
5. Docs updated: relevant `docs/*-model.md`, `SCIENTIFIC_VALIDATION.md`/`BUILD_STATUS.md` with date and measured numbers only.
6. `git status --short` and `git diff --stat` shown; one logical commit per step on the feature branch.
7. Stop and report; wait for the user's go-ahead before the next milestone.

## Code Review Rules
- Flag any claim of hardware realism, speed-up or validation without a test.
- Flag tests that were loosened, skipped or deleted; flag new dependencies; flag network calls in tests.
- Flag changes to Host/Origin checks, body limits, worker timeout/memory limits or concurrency.
- Flag formatting mixed with logic changes in the same commit (frontend files are dense; keep formatter commits separate).
