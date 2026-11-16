# M1 circuit-reference verification — 2026-11-15

Base: `0eb18ac`. Branch: `codex/m1-independent-reference`.

## Acceptance

- `reference-final.log`: `.venv/bin/python -m pytest -m reference -q` exited 0; 248 passed, 393 deselected, 1 warning in 12.37s.
- `full-pytest.log`: full suite exited 0; 641 passed, 1 warning in 24.86s. macOS time: 25.38s wall, 294,043,648 bytes maximum RSS, 239,289,400 bytes peak footprint. These are whole pytest-process measurements including imports, not per-model allocations or aggregate worker memory.
- `mutation-guards.log`: explicit RY-sign and readout-oracle mutations detected; 2 passed in 0.71s.
- `reference-results.json`: complete 300 ideal / 30 noisy case configurations, fixed seeds, exact gate coverage, error/norm deviations, probabilities/counts, chi-square/Holm statistics and measured times. No family rejects at alpha 0.001.
- `differential-report.json`: earlier implementation-stage run with the same fixed cases and outcomes. It is separate evidence, not extra independent cases.
- `command-results.json`: commands, return codes, environment and applicability of prior build/browser evidence.
- `preservation-{before,after}.json`: 102 historical artifacts unchanged; user databases compared only by file metadata; original production/frontend/dependency/script/workflow files unchanged.

## Test-first and instrumentation records

`statevector-red.log`, `density-red.log` and `differential-red.log` record failures before the new APIs existed. Density RED includes initial fixture setup errors and then proper missing-module assertion failures. Corresponding GREEN logs record the implementations passing. These are development evidence, not unresolved scientific failures.

`reference-pytest.log` records an initial instrumented run where all 248 tests passed in 10.60s, but `/usr/bin/time -l` exited 1 after a sandbox-denied `sysctl kern.clockrate` query. The plain reference run and scoped full-suite measurement above completed successfully. The existing Starlette/httpx deprecation warning was not suppressed.

The full local browser/build suite was not rerun in M1 because no API, job, store or UI code changed. M0's separately dated 40-browser-test/build evidence remains under `../codex-m0-baseline/`. Any GitHub CI run triggered by publication is a separate execution, not inferred from local results.

Methods and primary sources are in `../../VALIDATION-PLAN.md`. No hardware calibration or exhaustive correctness claim is made. Publication is verified after the M1 commit; inspect the remote branch and final chat report for its exact SHA/CI result.
