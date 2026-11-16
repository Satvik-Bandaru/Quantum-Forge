# M2 — Localhost security and storage hardening

Base: 4e893a1. Branch: codex/m2-security-storage. User approved M2 after the M1 report.

1. HTTP: separate testserver host support from production; require exact Origin for mutation, with explicit CLI originless opt-in. Preserve body and worker limits.
2. Storage: ordered versioned migrations, pre-migration SQLite backups, summary cache and bounded saved circuits. Existing database upgrades require explicit permission; use only temporary fixtures now.
3. Workers: release manager lock before process termination/join; retain ownership until cleanup/persistence finish; validate concurrent cancellation.
4. Run security tests, full Python suite and unchanged browser/build regression in a source-matched isolated scratch directory to preserve old evidence. Exercise curl host/origin/body/concurrency probes against an isolated temporary backend.
5. Review integration, update status/validation/handoff and commit M2. Do not restart the user's running lab or migrate the real database. Ask approval for the concrete real-database upgrade only after implementation and testing are reviewable.

No dependency additions, inference features, changes to scientific tolerances or other milestones. Historical evidence and real experiment databases stay untouched. Old application process remains on its loaded code until a separately approved restart/upgrade.
