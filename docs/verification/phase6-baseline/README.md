# Phase 6 baseline verification

- Full command: `QF_REGRESSION_ARTIFACTS=docs/verification/phase6-baseline bash scripts/check-regression.sh`
- Exit status: 0.
- Python: 343 passed, 1 warning, 12.53s.
- Browser: 35 passed, 1.6m.
- TypeScript / Vite production build passed, 3.74s.
- Python dependency check: no broken requirements. npm top-level dependency inventory succeeded.
- Isolated temporary-database startup: v0.5.0, ready; server shut down at suite completion.
- Live localhost:8777 health read separately: v0.5.0, ready; no live runs submitted or live server stopped.
- All explicitly requested source paths exist; 16 core/main-lab file hashes are recorded in source-tree.json.
- No genuine baseline failures found. Existing non-fatal warnings: Starlette/httpx deprecation; >500 kB Vite chunk (LabScene ~1,039 kB uncompressed); THREE.Clock deprecation; NO_COLOR/FORCE_COLOR environment notice.
- No product source edits. The standard browser suite refreshes its generated screenshot/evidence files.
