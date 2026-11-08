# Quantum Forge QUBO workspace implementation plan

> **For agentic workers:** Use executing-plans for integration and focused independent agents for engine, workspace, and review. Checkboxes track verified deliverables.

**Goal:** Extend the existing laboratory with an editable binary QUBO model, equivalent Ising visualization, and a comparison of five executed solvers, presented in the Quantum Forge visual language.

**Architecture:** Keep the FastAPI isolated worker, SQLite records, React/TypeScript, and current numerical packages. Add a bounded `qubo` job and a focused React workspace. Preserve every existing lab and saved experiment.

**Tech stack:** NumPy, PennyLane, SciPy COBYLA, Ocean CPU annealing; React, SVG, Recharts.

**Spec:** [User master request](../../requirements/quantum-forge-master.md), especially parts 1–4, 16–20 and 23. The five user images guide visual design only; their illustrative benchmarks are not data.

## Constraints and decisions

- The scientific foundation and problem-specific comparisons already work. Complete the missing editable modeling part of Phase 2 before expanding into AI, chemistry, or integrations.
- Use a canonical upper triangular matrix: `E(x)=offset+ΣQii xi+Σi<j Qij xi xj`; q0 is the first displayed bit. Reject nonzero lower entries to avoid double-counting ambiguity.
- 2–8 variables, finite coefficients ±100, finite offset ±1000, p≤3, ≤80 COBYLA evaluations, ≤4096 samples; existing global limits and cancellation still apply.
- Compare exhaustive enumeration, greedy assignment, multistart one-bit local search, classical simulated annealing, and simulated QAOA on exactly the same energy. Show absolute gaps; arbitrary offsets make energy ratios misleading.
- Encode constraints in matrix coefficients only. Explain the one-hot penalty example and its limits; no claim of a general symbolic constraint parser.
- No Git repository is present. Edit the existing workspace and preserve a SQLite backup at `data/experiments-before-qubo.sqlite3`; no migration or history deletion.
- No new dependencies, hardware accounts, paid services, or fabricated connections.

## Review focus

1. Upper/lower triangle conventions and Ising offset must agree for every bitstring, including negative coefficients and nonzero offsets.
2. Degenerate or zero-energy models must remain finite; QAOA must not divide by zero or leak the exhaustive answer into a heuristic.
3. Saved results must stay tied to their own matrix when users edit the current form or reload history.
4. CSV must preserve energies, gaps, solver settings, and provenance; the history summary must accept a new solver schema.
5. Small screens, invalid JSON imports, and job cancellation must leave the workspace usable.

## Task 1: Model and computation

**Files:** `backend/qubo.py`, `tests/test_qubo.py`, `docs/qubo-model.md`.

- [x] Write and observe failing analytical tests for QUBO/Ising equivalence, known minima, validation boundaries, and finite normalized QAOA output.
- [x] Implement `QuboRequest` and `run_qubo`, independent baselines, deterministic seeds, actual optimization traces, and explicit cost units.
- [x] Run focused scientific tests and document algorithms and limits.

## Task 2: API, persistence and exports

**Files:** `backend/app.py`, `backend/jobs.py`, `backend/store.py`, `tests/test_qubo_api.py`.

- [x] Write a failing actual-job round-trip test with triangle minimum −2, five solvers, JSON/CSV provenance, and history reload.
- [x] Register `qubo` validation and worker execution; export actual solver rows and preserve legacy history summaries.
- [x] Verify invalid/noncanonical models are rejected before creating jobs.

## Task 3: Editable laboratory

**Files:** `frontend/src/QuboLab.tsx`, `frontend/src/qubo.css`, `frontend/tests/qubo.spec.ts`, shared types and App registration.

- [x] Implement bounded matrix editing, Max-Cut and one-hot presets, model import/export, derived Ising couplings, and run controls.
- [x] Show actual solver energies, absolute gaps, wall time, sampled distribution, and QAOA convergence; show no pre-run benchmarks.
- [x] Exercise coefficient editing, history restoration, exports, and desktop/mobile overflow in browser tests.

## Task 4: Quantum Forge presentation and completion

**Files:** `frontend/src/CommandCenter.tsx`, `frontend/src/forge.css`, `frontend/src/App.tsx`, `frontend/index.html`, README and audit.

- [x] Apply the cyan/violet Quantum Forge branding and a working command center that routes to implemented modules.
- [x] Label dashboard counts as the latest 200 saved records and distinguish implemented capabilities from planned ones.
- [x] Run backend regression, frontend production build, and browser workflows. Inspect screenshots and resolve review findings.
- [x] Record feature inventory, verified test results, limits, and the next research milestone.


## Verified delivery

Final code checks on 2026-11-07:

- `.venv/bin/python -m pytest -q`: **215 passed**, 14.09 s; one existing Starlette/httpx adapter deprecation warning.
- `npm run build`: **passed** TypeScript and Vite production compilation. Main JS 385.87 kB, chart chunk 417.56 kB before gzip; no new packages.
- `npm run test:ui`: **18 passed**, 51.5 s, real Chrome against the running production service. Includes actual QUBO matrix-edit reruns, CSV content, history replay, guide provenance reset, strict model import, coupling selection, exact-reference visibility and responsive layouts.
- `.venv/bin/python -m pip check`: **no broken requirements**. Installed frontend package versions agree with the lockfile.
- Database comparison against the pre-change SQLite backup: **87 experiments and 7 saved circuits preserved byte-for-byte**, no missing or changed original records. Browser checks added real new runs.
- Independent review checked 496 binary-state energies and 12 coupled, two-layer QAOA cases against separate calculations. Maximum reported discrepancies were below 4e-13 energy and 2e-15 probability. Review findings were resolved.

A parallel build initially cleared `dist/assets` while four API fixtures were starting; those tests were rerun after the build, then the final complete suite passed. Builds and production-browser verification were subsequently kept sequential. No runtime workaround or weakened expectation was added.

### Files and responsibilities

| Files | Change |
| --- | --- |
| `backend/qubo.py`, `docs/qubo-model.md` | Bounded binary model, complete Ising mapping, five actual solvers, separate initialization/work timings, numerical conventions. |
| `backend/app.py`, `backend/jobs.py`, `backend/store.py` | Validated QUBO jobs, worker dispatch, history compatibility, complete JSON/CSV exports. |
| `backend/http_limits.py`, `backend/science.py` | Actual body-size enforcement and bounded repetition seeds. |
| `frontend/src/QuboLab.tsx`, `qubo.css` | Editable model, penalty examples, coefficient inspection, executed solver evidence and provenance. |
| `frontend/src/CommandCenter.tsx`, `forge.css` | Quantum Forge command center, supported-lab navigation, actual saved-record statistics, cyan/violet visual language. |
| `frontend/src/App.tsx`, `types.ts`, `main.tsx`, `frontend/index.html` | New workspace routing, branding, guide reset on run changes, unit-weight triangle challenge condition, shared styles. |
| `tests/test_qubo.py`, `test_qubo_api.py`, `test_http_boundaries.py`, `test_science.py` | Scientific, API/export, body-stream and seed-boundary regressions. |
| `frontend/tests/qubo.spec.ts`, `workflows.spec.ts` | Real browser workflows, guide regression, command-center and QUBO desktop/mobile verification. |
| `README.md`, `docs/feature-inventory.md`, `docs/requirements/quantum-forge-master.md` | Usage, honest feature inventory, retained full user request. |
| `frontend/package.json`, `package-lock.json` | App version 0.4.0; dependency versions preserved. |

Screenshots: `docs/screenshots/overview.png`, `quantum-forge-overview-mobile.png`, `qubo-lab-desktop.png`, and `qubo-lab-mobile.png`. Final screenshots were visually inspected. A Chrome full-page capture immediately after viewport resize initially repeated the top viewport; scrolling the actual mobile laboratory grid into view before returning to the top produced a correct capture. The DOM contained one command-center heading, the mobile grid rendered correctly, and the focused responsive workflow passed again (4.8 s). No production rendering change was needed. The previous physics, optics, circuit, and virtual-computer browser workflows also passed with the updated shared shell.

### Interpretation and remaining work

The generic workspace solves only the supplied energy polynomial on 2–8 binary variables. Constraints must be encoded in coefficients; absolute gaps are relative to exhaustive enumeration of that same model. QAOA is CPU statevector simulation with exact expectation training, followed by finite shots. No hardware result, statistical speedup, arbitrary symbolic constraint system, quantum AI, molecular chemistry or domain-specific integration is claimed.

The next master-roadmap slice is Phase 3: bounded reproducible parameter sweeps and multi-run benchmark reports. Single-photon/HOM and Ramsey models remain subsequent scientific extensions. The full requested platform is an iterative roadmap; this delivery completes a working QUBO modeling and comparison slice while retaining the existing labs.
