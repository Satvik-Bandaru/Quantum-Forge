# Next session — M2 local-security/storage checkpoint

Repository: `/Users/satvikbandaru/Documents/AI and Database Projects/quantum-forge-lab`.
Branch: `codex/m2-security-storage`, based on M1 `4e893a1`. Read AGENTS.md and docs/codex/MASTER_PROMPT.md first. M0 snapshot remains `701f87a`; no history was rewritten.

## Implemented scope

Exact same-origin mutation checks; production excludes testserver; explicit originless CLI opt-in. SQLite ordered migrations with owner opt-in, WAL-aware backups and rollback; history summary cache with legacy fallback; saved-circuit cap (default 1,000, minimum 100). Worker joins/termination occur outside the lock; cancellation races and transient finalization failures preserve slot ownership/results and retry safely.

No scientific equations, tolerances, dependency versions or application UI changed. Tests' direct API clients were updated for explicit test mode or Origin headers. Application version remains 0.6.0.

## Verification

71 focused security tests passed in 4.58 s. Full suite: 712 passed in 31.04 s. Build passed in 2.90 s. Curl probes: evil/testserver hosts and cross-port Origin 403; fixed/chunked 300 KB 413; second concurrent job 409; cancellation persisted. All 40 browser tests passed in 1.9 minutes and the regression script exited 0. BUILD_STATUS.md records the evidence. Logs include the initial sandbox OpenMP failures and successful permission-scoped rerun; no failing evidence was overwritten.

The browser regression uses a source-matched scratch copy under ignored `.venv/codex-m2-validation` with an independent temporary database/port, preserving historical screenshot/JSON files. Evidence is in `docs/verification/codex-m2/`. The user's live service was not restarted and real databases were not opened or migrated for verification.

## Pending activation

Ask the owner before migrating the actual database, as explicitly required by docs/codex/MASTER_PROMPT.md M2. The upgrade is concrete and tested; see docs/LOCAL_SECURITY.md. After approval, stop the old service cleanly, launch once with `QF_ALLOW_DB_MIGRATION=1`, verify the backup/version/history and run a browser smoke test. Do not silently enable the migration variable or restart port 8777. Starting an old database without opt-in now stops with MigrationRequired; an already-running old process continues its loaded code.

M2 does not refresh downloadable ZIPs, merge main, deploy, enable payments or connect hardware. GitHub publication, if performed, is on this feature branch; verify the remote SHA rather than assuming it is present. Stop after M2 and await user review before M3 readability/refactoring or later scientific milestones. Do not access other repositories or Quantum Forge Downloads.
