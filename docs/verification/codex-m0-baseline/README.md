# M0 baseline evidence — 2026-11-15

Snapshot: `701f87a` on `feat/main-quantum-lab`. Documentation branch: `codex/m0-agents-baseline`.

- `standalone-pytest.log` and `standalone-build.log`: exact commands in the original checkout.
- `sandbox-attempt/`: failed first full-regression attempt; loopback bind was denied after tests/build passed.
- `command-results.json`: commands, working directories, real exit codes and summaries.
- `preservation-before.json`: approved snapshot file hashes plus metadata-only database inventory.
- `scratch-source-parity.json`: copied-file hashes, source commit, working directory and dependency links.
- `environment.json`: actual local runtime versions and platform.

The full regression uses the unchanged snapshot in `.venv/codex-m0-validation`, a task-owned scratch workspace inside this repository. Existing tests use hardcoded evidence paths. This workspace prevents those writes from overwriting historical records in the original checkout. It is not another existing project or external repository. It contains no user database. Its dependencies are the existing installations; no packages were installed.

Successful regression: exit 0; Python `393 passed, 1 warning in 17.46s`; build `3.87s`; Playwright `40 passed (2.0m)`. Successful logs are at this directory's top level. Six fresh JSON results are under `results/`, the representative Bell screenshot is under `screenshots/`, and `generated-screenshots.json` inventories all 30 fresh screenshots. Remaining screenshot files stay in the ignored scratch workspace rather than duplicating the full gallery in Git. `preservation-after.json` confirms all original snapshot files and copied sources unchanged, plus unchanged metadata for the three user databases.

These results validate educational software simulations; they do not establish calibrated hardware accuracy. The external report's separate 24 formula checks were not rerun or newly claimed in M0.
