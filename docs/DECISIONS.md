# Decisions — M0 baseline

## 2026-11-15 — Scope and approval

The user's latest request and supplied master prompt govern this chat: M0 only, with no feature, science or test-source changes. The broader Phase 7 directive is future context. The research report's Linux results and 24 formula checks are supplied evidence, not measurements reproduced in M0.

The user approved the reviewed local snapshot with “do it”. Commit `701f87a` preserves the existing v0.6 working tree on `feat/main-quantum-lab`, as M0 explicitly requires. This is the one baseline exception to the supplied general `codex/<milestone>-<slug>` branch rule. Subsequent M0 work uses `codex/m0-agents-baseline`. No push, PR, merge or remote operation is authorized by this checkpoint.

## 2026-11-15 — Preserve historical evidence while running regression

Inspection found that `QF_REGRESSION_ARTIFACTS` redirects script logs but does not redirect hardcoded screenshots and JSON written by browser tests. Running the suite in the original checkout would overwrite historical evidence, contrary to the supplied instructions.

Ruling: run standalone Python tests and the frontend build in the original checkout, then run the unchanged full regression script in a task-owned scratch workspace inside the repository's ignored `.venv/codex-m0-validation` directory. Populate it only from the approved local snapshot; omit historical evidence and user databases. Reuse the existing Python and npm installations. Compare source hashes before and after, and copy fresh outputs into `docs/verification/codex-m0-baseline`. Do not access any other existing repository or Quantum Forge copy. This changes the regression working directory, which must be disclosed alongside its results; application and test sources remain identical.

No source/test modification, dependency installation, schema change, deletion of user files, or restart of the user's port-8777 instance is part of M0. Scratch files stay under the existing ignored environment; the regression script's own temporary server/database lifecycle remains unchanged. Existing evidence is checked against the snapshot, and real database files are checked by metadata only, without opening their contents.

## 2026-11-15 — Supplied guidance and local execution

Copy the supplied master prompt unchanged. Correct two factual details in `AGENTS.md`, as M0 allows: use Node 22.12+ rather than 22+ (installed Vite and `@vitejs/plugin-react` declare `^20.19.0 || >=22.12.0`), and document the connected bench's explicitly named `_deg` phase inputs (`backend/instruments.py`) which `backend/connected.py` converts with `math.radians`. All other supplied AGENTS content stays unchanged.

Use this session's actual permission controls; do not claim to have changed desktop sandbox or CLI settings. The user's requested baseline checks authorize the existing local test commands; any sandbox escalation is limited to the command requiring it. No new dependency or internet access is needed for the installed baseline.

Fresh M0 logs are normally ignored by `*.log`; stage only the new M0 evidence directory explicitly rather than weakening `.gitignore`. Keep historical status records intact and document this checkpoint in `docs/AUDIT-2026-11.md`.

## 2026-11-15 — Preserve supplied text and raw log whitespace

The full staged `git diff --check` reports trailing spaces on the supplied master prompt's blank line 58 and a trailing blank line in each raw `npm-ls.log`. Retain those bytes to preserve the supplied prompt and captured command output. Check authored documentation separately; do not describe the full whitespace check as passing. These are provenance artifacts, not changed application code or failing tests.
