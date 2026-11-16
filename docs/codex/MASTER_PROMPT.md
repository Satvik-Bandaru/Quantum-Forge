# Nexus Lab — Master Implementation Prompt (for OpenAI Codex: CLI, IDE or cloud)

Version 1.0 · 15 Nov 2026 · Derived from "Nexus Lab — Deep Research Report". Put `AGENTS.md` (supplied separately) in the repo root. Keep this file as `docs/codex/MASTER_PROMPT.md`. Start **each milestone in a new Codex chat** with:

> Read `docs/codex/MASTER_PROMPT.md` and `AGENTS.md`. Do milestone **Mx** only. Plan first, then implement, verify and stop.

---

## 0. How to run Codex for this repo

**Recommended: local Codex CLI on the Mac.** Codex cloud only sees what is on GitHub, and GitHub has only the 8 Nov initial commit.

```sh
cd "/Users/satvikbandaru/Documents/AI and Database Projects/quantum-forge-lab"
codex --sandbox workspace-write --ask-for-approval on-request
```

- Never use `--dangerously-bypass-approvals-and-sandbox` / `--yolo` or `--sandbox danger-full-access`.
- Do not set `approval_policy = "untrusted"`. It is retired.
- Network access is off in `workspace-write`. Codex must ask before `pip install`, `npm ci` and `npx playwright install`. Approve each one individually.
- `scripts/check-regression.sh` starts a loopback server and a browser. If the sandbox blocks it, Codex asks. Approve that exact command; do not widen the sandbox globally.
- Use `/plan` at the start of each milestone and `/review` (against the milestone's base commit) before reporting.

**Codex cloud (only after you decide to push v0.6 to GitHub; pushing is your decision, never the agent's).** Use this setup script. Setup has internet access; the agent phase is offline by default.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
npm --prefix frontend ci
(cd frontend && npx playwright install --with-deps chromium)
echo 'export PLAYWRIGHT_BROWSER=chromium' >> ~/.bashrc
```

Keep agent internet access **Off**. The locked dependencies were verified to install and pass (393 pytest, build, 40 Playwright) on Linux x86-64 on 15 Nov 2026.

---

## 1. Your role and hard rules

You are the implementation agent for **Quantum Forge Nexus Lab v0.6**, a local-first educational quantum laboratory. This is *continuing an existing, verified application*, not a rewrite.

The following are failed-task conditions:

1. **One milestone per chat.** Do only the milestone named. Stop at its end and report using Section 7. Do not start the next one.
2. **Preserve the original.** Do not delete, move or rewrite existing features, history compatibility, user data (`data/*.sqlite3*`) or historical evidence (`docs/verification/*`, `docs/screenshots/*`).
3. **Branch work only.** Create `codex/mX-<slug>` from the approved base. Never commit to `main`. Never push, open PRs, tag remotely, merge or rebase published history without an explicit instruction in this chat.
4. **Other repositories are off-limits.** Do not read, modify or import from SRAI, ChainMind, VectorForge (any version), Orbital Forge, other Quantum Forge copies, or `../Quantum Forge Downloads/`.
5. **No paid services, accounts, API keys, telemetry, remote compute, hosting or deployment.**
6. **Never fabricate.** No invented test counts, timings, versions, APIs or citations. If you are unsure an API exists, read the installed package source in `.venv` or run a small probe and show its output.
7. **Evidence before claims.** "Done" requires pasted real output of the commands in Section 6 and the milestone's acceptance commands.
8. **Approval required for:**
   - deleting or moving files
   - `git reset --hard`, `git clean`, `git checkout -- <dirty file>`, `git stash drop`
   - adding any dependency (including dev tools such as ruff, prettier, vitest or stim)
   - network commands
   - SQLite schema changes
   - writing outside the repo
   
   When you need approval, state the exact command and why, then wait.
9. **Do not weaken science or safety to pass.** Do not loosen tolerances, limits, Host/Origin checks, body caps or worker timeout/memory limits, and do not skip tests. A failing scientific check is a result: report it.
10. **Separate formatting from logic.** Formatter-only changes go in their own commit with no logic edits.

---

## 2. Facts about the codebase (verified 15 Nov 2026; re-verify in M0)

- The project path on the Mac (per `NEXT_SESSION.md`) is `/Users/satvikbandaru/Documents/AI and Database Projects/quantum-forge-lab`, on branch `feat/main-quantum-lab`, base `d431825162b70f357b2737137b36afdf7e870e8f`. The package manifest lists **86 uncommitted or untracked entries**, including all of `backend/{connected,instruments,thermal,research,compute_policy}.py`, `frontend/src/{connected,main-lab,research}/`, `.github/`, `scripts/` and 10 test files.
- GitHub `Satvik-Bandaru/Quantum-Forge` is public. It has one commit on `main` and **no LICENSE**.
- Commands:
  - `.venv/bin/python -m pytest -q` gives 393 passed
  - `npm --prefix frontend run build` passes
  - `bash scripts/check-regression.sh` gives 40 Playwright tests passed (on Linux, set `PLAYWRIGHT_BROWSER=chromium`)
- Known debt:
  - Dense TSX: `frontend/src/App.tsx` is 38 KB in 106 lines; `connected/ConnectedLab.tsx` is 36.6 KB.
  - `'testserver'` is accepted as a production Host.
  - The Origin check accepts any localhost port and also requests with no Origin.
  - No SQLite schema version.
  - The `circuits` table is unbounded.
  - The watchdog joins worker processes while holding the lock.
  - Full-amplitude payloads: 22 qubits measured 1.24 GiB peak RSS.
- Scientific conventions:
  - q0 is the leftmost bit.
  - Units: µs, MHz, GHz, K, mW, rad.
  - Connected bench: detuning δ = f_device − f_source, H/ħ = π(−δZ + Ω(cosφX + sinφY)). The Physical lab uses +ΔZ.

---

## 3. Target additions (do not redesign without a `docs/DECISIONS.md` entry)

```
backend/reference/     M1  independent NumPy-only statevector & density-matrix kernels (no qiskit/pennylane imports)
backend/inference/     M4  likelihoods, grid posterior, identifiability, SBC utilities (NumPy/SciPy only)
backend/migrations/    M2  schema_version table + ordered migration functions
tests/reference/       M1  differential + metamorphic tests, marker `reference`
tests/security/        M2  host/origin/body/limit/store tests
docs/AUDIT-2026-11.md  M0  baseline evidence
docs/DECISIONS.md      M0  ADR-style log
docs/VALIDATION-PLAN.md M1 methods, α levels, seeds, tolerances
docs/codex/MASTER_PROMPT.md  M0  this file
```

Import rule: `backend/reference/*` and `backend/inference/*` may import only the standard library, NumPy, SciPy and Pydantic. Add a test that greps imports and fails otherwise. Register `reference` and `sbc` markers in `pytest.ini`. The default `pytest -q` must still finish in under about 60 s, so mark slow SBC runs `sbc` and run them explicitly.

---

## 4. Milestones (one per chat; stop after each)

### M0 — Preserve, audit, checkpoint (no feature code)

1. `pwd`, `git rev-parse --abbrev-ref HEAD`, `git rev-parse HEAD`, `git status --short | wc -l`, `git status --short`. Confirm the branch is `feat/main-quantum-lab` and HEAD is `d431825…`. If anything differs, **stop and report**.
2. Check that `data/` exists and list its files and sizes with `ls -la data`. Do not open or modify the database.
3. **Ask for approval**, then commit the existing working tree on `feat/main-quantum-lab` as `chore: snapshot v0.6 working tree (pre-Codex baseline)`. First confirm that `.gitignore` excludes `.venv/`, `node_modules/`, `frontend/dist/` and `data/*.sqlite*`, and show `git add -A --dry-run | head -100` plus the count. If the user declines, stop. Do not continue on an uncommitted base.
4. Create the branch `codex/m0-agents-baseline`.
5. Add `AGENTS.md` (the supplied file, unchanged unless a fact is wrong; if so, record why in `DECISIONS.md`), `docs/codex/MASTER_PROMPT.md`, `docs/AUDIT-2026-11.md` and `docs/DECISIONS.md`.
6. Run the baseline: `.venv/bin/python -m pytest -q`, `npm --prefix frontend run build`, `bash scripts/check-regression.sh` with `QF_REGRESSION_ARTIFACTS=docs/verification/codex-m0-baseline`. Record the counts and times in `AUDIT-2026-11.md`.
7. Commit: `M0: AGENTS.md, audit baseline`.

**Acceptance:** `git log --oneline -3`; `git status --short` (empty); pytest summary line; the build's last 5 lines; the regression script's exit code and Playwright summary line; `git diff --stat feat/main-quantum-lab...HEAD` (only docs, AGENTS.md and new verification logs).

### M1 — Independent reference and differential test suite

1. `backend/reference/statevector.py`: apply the gate set from `backend/models.Gate` (X, Y, Z, H, S, SDG, T, TDG, P, RX, RY, RZ, CNOT, CZ, CP, SWAP, CCX) to a q0-leftmost NumPy statevector for ≤ 8 qubits.
2. `backend/reference/density.py`: a density matrix for ≤ 6 qubits with the same depolarising channel (ρ → (1−λ)ρ + λI/d on the gate's qubits) and independent readout flips as `quantum.execute_circuit`.
3. `tests/reference/test_differential.py`:
   - (a) 300 seeded random circuits: reference amplitudes vs `inspect_state` amplitudes, equal up to global phase, atol 1e-10.
   - (b) Noisy sampling: for 30 seeded small circuits, compare exact reference outcome probabilities with Aer counts using a chi-square goodness-of-fit with Holm correction at family α = 0.001 and fixed seeds. Document α in `VALIDATION-PLAN.md`.
4. `tests/reference/test_metamorphic.py`: inserting H·H, X·X, S·SDG or T·TDG pairs, commuting disjoint gates, and relabelling qubits (with outputs permuted) must leave the ideal state unchanged. (MorphQ-style.)
5. A mutation guard: a test that applies a deliberately wrong reference (for example a sign flip in RY) and asserts the differential check *detects* it.
6. Import-boundary test for `backend/reference/`.
7. Optional (ask first; dev-only file `requirements-dev-reference.txt`): Stim for Clifford cross-checks and QuTiP `mesolve` for the Lindblad models, both skipped when not installed.

**Acceptance:** `.venv/bin/python -m pytest -m reference -q`; the full `pytest -q` (393 + new tests); the mutation-guard test output; a short table in `SCIENTIFIC_VALIDATION.md` with the new evidence (date and numbers only).

### M2 — Security and storage hardening

1. `create_app(..., testing: bool = False)`. Allow `'testserver'` only when `testing=True`, and update the tests to pass it.
2. Origin on mutating methods must equal the server's own `scheme://host:port`, or be absent only when `testing=True`, or `QF_ALLOW_ORIGINLESS=1` is set for CLI use (document this). Add tests for `Origin: http://localhost:3000` → 403.
3. SQLite: add a `meta(schema_version)` table and `backend/migrations/` (v1 = current schema). Make migrations idempotent and test them on a copy of a fixture DB created with the *old* schema. **Ask before applying any migration to the user's real DB**; the app may only migrate on startup after backing the file up to `data/backup-<timestamp>.sqlite3`.
4. History speed-up: store a `summary` JSON column populated on update, and fall back to parsing for old rows. Add a test that old rows still load.
5. `circuits` retention: `QF_MAX_SAVED_CIRCUITS` (default 1000, minimum 100). Prune the oldest only beyond the cap, and test it.
6. `jobs.finish`: perform `join`/`kill` outside the lock without race conditions, and add a test that a cancel during termination does not deadlock.

**Acceptance:** `pytest tests/security -q`; full `pytest -q`; full regression; a `curl` probe table (Host evil → 403, Host testserver → 403 in production mode, Origin localhost:3000 → 403, 300 KB body → 413, chunked 300 KB → 413, second job → 409).

### M3 — Frontend readability (no behaviour change)

1. **Ask before adding Prettier** as a devDependency, pinned exactly. Commit 1: formatter only (`npx prettier --write "frontend/src/**/*.{ts,tsx}"`), with no other edits. Show `git diff --stat` and confirm the build and all 40 Playwright tests pass.
2. Commit 2+: extract page state from `App.tsx` into hooks (`useHistory`, `useJobRunner`, `useApparatus`, …) and components. Do not change `data-testid`s, text that tests select on, routes, or API calls.
3. Optional: convert `src/assets/quantum-photonics-studio.png` (2.39 MB) to WebP with an `<img>` fallback, only if the tests still pass and the image is visually equivalent (attach before/after screenshots under `docs/screenshots/codex-m3-*`).

**Acceptance:** `npm --prefix frontend run build`; the regression script's Playwright summary showing 40 passed; `wc -l -c frontend/src/App.tsx` before and after; max line length before and after (`awk '{if(length>m)m=length}END{print m}'`).

### M4 — Nuisance-aware calibration and T1 inference (backlog item 1)

1. `backend/inference/likelihood.py`: a binomial likelihood for connected-bench sweeps (amplitude, T1) as a function of θ = (gain, T1, Tφ, e01, e10). Use the existing `evolve_segment` / analytic `resonant_excited_probability` for forward models, and do not modify them.
2. `backend/inference/posterior.py`: a grid posterior (≤ 3 free parameters at a time, with the others fixed or marginalised on a coarse grid) using declared priors. Return the posterior mean, 90% credible intervals, the posterior correlation matrix, and identifiability flags (Fisher-information rank or condition number above a threshold, or a flat profile).
3. `backend/inference/sbc.py`: simulation-based calibration. Draw θ from the prior, simulate counts with a seeded RNG, compute the posterior and record the rank of the true θ.
4. Expose it as a new connected sequence option or a new `/api/jobs` kind `inference`. It must run in the existing worker with the existing limits. The schema is bounded, and the results carry `limitations` and `model` blocks like the other modules.
5. Tests:
   - a known-θ recovery test (the true value inside the 90% interval for a fixed seed)
   - a non-identifiable configuration (for example gain and e01 confounded) that **must** raise the identifiability flag
   - SBC with ≥ 200 seeded datasets, marked `sbc`
   - a rank-histogram χ² uniformity test at α = 0.01
   - 90% interval coverage within the 99% binomial band
6. Docs: `docs/inference-model.md` with equations, priors, grid resolution, and what is and is not propagated.

**Acceptance:** `pytest -m "not sbc" -q`; `pytest -m sbc -q` with the coverage numbers pasted; one new browser test covering run → result → History reopen; updates to `SCIENTIFIC_VALIDATION.md`.

### M5 — Blind-device characterisation challenge

The backend samples hidden device parameters from a seeded prior and stores them server-side only. The user runs experiments with a shot budget, then submits estimates and intervals. The score is an interval score or log score plus a shot cost. The reveal comes only after submission. Tests: hidden values never appear in any response before submission (API test that walks every endpoint), scoring unit tests, and one Playwright workflow. Label it educational. Do not claim it is the first of its kind.

**Acceptance:** `pytest -q`; regression with 41 or more browser tests; the leak test output.

### M6 — Scaling and performance (measure on the user's M4)

Add a memory estimator (statevector 16·2ⁿ bytes, density 16·4ⁿ) that rejects requests before allocation. Replace full amplitude lists with top-k (k ≤ 4096), and add a "download full statevector" path for n ≤ 16. Make `QF_MAX_QUBITS` allowed up to 24, gated by the estimator. Add an optional `QF_THREADS` (1–4). Add `scripts/bench_scaling.py`, which prints n, time and peak RSS.

**Acceptance:** the benchmark output **run on the Mac** (do not quote Linux numbers as Mac numbers); a watchdog test at 22 qubits (memory-limited or completed within budget); all existing tests.

### M7+ — Optional, separate plans and separate approval each

Options, each needing its own plan and approval:
- repeated QEC memory (Stim + PyMatching)
- HOM two-photon interference (mode overlap, analytic dip)
- a Ramsey-magnetometry sensing module
- temperature-dependent thermal C(T)
- a LICENSE file (the user chooses the license)
- pushing to GitHub and enabling CI (the user performs or explicitly authorises this)

---

## 5. Non-goals (do not build)

- decorative rooms without a validated model
- accounts, payments, billing, remote or cloud compute, hosted deployment
- LLM features inside the app
- replacing FastAPI, React or SQLite
- GPU or Metal kernels
- claims of hardware fidelity, calibration of real devices, or quantum advantage
- touching other repositories

---

## 6. Checks to run before reporting any milestone

```sh
.venv/bin/python -m pytest -q
npm --prefix frontend run build                 # if any frontend file changed
bash scripts/check-regression.sh                # if API, jobs, store or UI changed
git status --short && git diff --stat <base>...HEAD
```

On Linux or in Codex cloud, prefix the regression command with `PLAYWRIGHT_BROWSER=chromium`. If a command cannot run (for example it is blocked by the sandbox and approval was declined), say so explicitly. Do not substitute a different command and call it equivalent.

---

## 7. Report format (end of every milestone)

```
Milestone: Mx — <name>
Branch / commits: <branch>, <short SHAs + messages>
Changed files: <list>
Commands run and real output:
  $ .venv/bin/python -m pytest -q
  <summary line>
  $ <acceptance command>
  <output>
Verified: <bullets tied to the outputs above>
Not verified / known gaps: <bullets>
Scientific findings or failed checks: <bullets or "none">
Approvals requested/granted/declined: <list>
Proposed next milestone: <id> — waiting for go-ahead
```

## 8. First instruction

Do **M0 only**. Do not write feature, science or test code in this chat.
