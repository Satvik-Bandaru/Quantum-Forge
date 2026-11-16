# Next session — M1 circuit-reference checkpoint

Repository: `/Users/satvikbandaru/Documents/AI and Database Projects/quantum-forge-lab`.
Branch: `codex/m1-independent-reference`, based on M0 commit `0eb18ac`. The approved v0.6 snapshot is `701f87a`. Read AGENTS.md and docs/codex/MASTER_PROMPT.md before making changes.

## Current scope and verification

The user explicitly authorized M1 and adding the verified work to GitHub. M1 adds NumPy-only independent statevector/density references and 248 reference tests, including 300 ideal circuits and a 30-circuit noisy Holm-corrected family. Both mutation guards pass. Full suite: 641 passed in 24.86 s; whole pytest-process maximum RSS 294,043,648 bytes. Publication outcomes are recorded in the final chat report; verify actual Git status/ref before assuming publication succeeded.

Application version stays 0.6.0. No production API, worker/store, frontend, dependency, database schema or hardware connection is changed. References cap ideal simulations at eight qubits and density matrices at six. They are validation kernels, not new UI laboratories. Read docs/VALIDATION-PLAN.md for fixed seeds, tolerances, statistical assumptions, import boundaries and limitations.

Evidence: docs/verification/codex-m1-reference/. Normal reference tests do not write reports; QF_REFERENCE_REPORT accepts only a new file path. Preserve all historical evidence. M0's application-wide build/browser checks passed separately; M1 does not claim new local browser results unless explicitly recorded.

## Next milestone

Stop after M1. Start M2 only on a new explicit user instruction, using a fresh milestone branch from the verified head. M2 covers localhost security/storage hardening, not new inference features. Ask before applying migrations to the user's actual DB; follow the master prompt's backup and compatibility requirements. M3–M6 remain future work.

## Data, runtime and publication

Do not open, rewrite or migrate data/*.sqlite3* as part of routine verification. Use temporary test databases. Do not stop or restart the user's port-8777 instance. Prior PID/session identifiers are historical and must not be assumed current.

The full browser regression writes fixed historical screenshot/JSON paths. M0 ran it in a hash-verified scratch workspace inside the ignored .venv directory; see docs/DECISIONS.md. Any future browser run must preserve those historical files similarly. Run Python tests and builds sequentially.

Do not access other repositories or Quantum Forge Downloads. This milestone does not refresh the downloadable ZIP. GitHub publication is to the authorized feature branch, without force, merge or rewriting main. Additional PR/merge work requires explicit instruction. No work is promised after this session ends.
