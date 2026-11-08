# Quantum Forge Lab Implementation Plan

**Goal:** Deliver the user's Phase 1 as a real local research application.
**Architecture:** React/TypeScript frontend served by FastAPI after a Vite build. Isolated CPU worker processes execute bounded jobs; SQLite stores actual runs and saved circuits.
**Tech Stack:** Python 3.12, PennyLane, Qiskit Aer, dwave-samplers, OR-Tools, NumPy/SciPy, FastAPI, React, Recharts.
**Spec:** User's attached Quantum Forge Lab request, Phase 1 priorities. User explicitly requested implementation without further design approval.

## Global Constraints
Local simulation only; no cloud calls, production integrations or credentials. No fabricated metrics. Default 12 qubits maximum, one concurrent job, 45 second job timeout, 8192 shots maximum. Backend binds loopback. Export instance, configuration, versions, validation, runtimes and simulator limitations.

## Review Focus
Qubit ordering and complex amplitudes; infeasible sampled knapsack states; duplicate edges and malformed inputs; cancellation/timeout cleanup; restored history and circuit schema validation.

### Task 1: Scientific core
Files: backend/models.py, backend/science.py, tests/test_science.py.
Interfaces: validated CircuitRequest and OptimizationRequest; run_circuit(request), run_optimization(request) return JSON-safe results.
- [x] Write and run failing tests for Bell-state probabilities, phase/rotation, invalid gates, Max-Cut triangle optimum, knapsack exact optimum, QUBO equivalence and reproducible samples.
- [x] Implement Qiskit circuit simulation, PennyLane QAOA, Ocean annealing, OR-Tools and exact small-instance comparisons.
- [x] Run the scientific test suite.

### Task 2: Local API and persistence
Files: backend/app.py, backend/store.py, backend/jobs.py, tests/test_api.py.
Interfaces: /api/jobs POST/GET/DELETE; /api/history GET; /api/history/{id} GET; exports; /api/circuits GET/POST.
- [x] Write and run failing integration tests covering run-save-load, validation, cancellation and concurrency.
- [x] Implement process jobs with hard timeout/cancellation, SQLite transactions and structured errors.
- [x] Run all backend tests.

### Task 3: Interactive interface
Files: frontend/src/{App.tsx,styles.css,api.ts,types.ts}, frontend/package.json.
- [x] Build overview, optimization editor, circuit builder with draggable gates, SVG diagram downloads, Bloch visualization, probability and convergence plots, algorithm guide, challenges and run history.
- [x] Include beginner/experiment/research views, JSON/CSV export, live progress, error feedback and save/load.
- [x] Compile TypeScript and production frontend; smoke test actual browser workflows against API.

### Task 4: Delivery and review
Files: README.md, start.command, requirements.lock.txt, docs/compatibility.md.
- [x] Document exact tested versions, math conventions, limitations, startup and roadmap.
- [x] Review core correctness, API input boundaries and UI workflows; fix findings.
- [x] Run full backend suite, dependency checks, frontend build and browser smoke test; leave app running locally.

## Rulings and progress
- Fresh directory: parent is not a Git repository, so no worktree or existing branch to isolate. Existing projects remain separate.
- Phase 2+ modules remain documented roadmap; no placeholder results or pretend integrations.
- Execute inline per user's direct request to make the application.

## Verification and completion record
- Scientific core and API: 38 tests passed. One upstream Starlette/httpx test adapter deprecation warning is documented.
- Production TypeScript/Vite build passed; dependencies checked with pip check (no broken requirements).
- Seven browser workflows passed using actual Chrome and the live service, including drag/drop, save/restore, exports, error handling, and responsive rendering.
- Independent reviewer identified four defects; all were fixed and targeted re-review found no remaining important defects.
- Default local app is running on port 8777. Screenshots are in docs/screenshots/.
- Final visual QA removed the arrowhead from a zero Bloch vector so mixed reduced states show only the center point.
