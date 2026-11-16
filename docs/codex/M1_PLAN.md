# M1 — Independent reference and differential validation

Base: `0eb18ac` (verified M0 checkpoint). Branch: `codex/m1-independent-reference`.

The user explicitly instructed “do it. and add to github” after M0. This authorizes the next milestone and publication of its verified feature branch, including the preserved v0.6/M0 commits. M2 and later milestones are excluded. The repository's existing clean checkout and installed dependencies are reused; no additional worktree, dependency, external service or database change is needed.

## Design

Add a bounded, independent reference package. Gate matrices and q0-leftmost tensor application use NumPy and standard-library validation. Ideal statevectors are capped at 8 qubits; density matrices at 6. The density implementation shares only reference gate definitions and validation, never production science functions. Local depolarization preserves the spectator subsystem by taking a partial trace; independent readout flips are applied after coherent/noisy evolution.

The reference accepts plain gate dictionaries, including validated model dumps, and returns NumPy arrays. Terminal measurement markers represent the application's final-readout convention; they do not simulate intermediate collapse. Invalid qubits, gate fields, angles, noise probabilities and nonterminal measurement sequences must fail before large allocations.

## Work and verification

1. Register `reference` and `sbc` pytest markers; add this plan and the statistical validation plan.
2. Write and observe failing analytical component tests, then implement `backend/reference/statevector.py` and `density.py`. Validate basis truth tables, phases, entanglement, local noise, spectators, physicality and bounds.
3. Add 300 seeded ideal comparisons with production `inspect_state`, 30 noisy Aer comparisons with fixed family-wise testing, identity/commutation/relabeling invariants, mutation detection and import-boundary checks. Test-only comparison/statistics helpers remain outside production code.
4. Run `pytest -m reference -q`, the explicit mutation guard and the full `pytest -q`; retain new logs and detailed numerical evidence. Do not rerun browser/build checks unless an API, job, store or UI file changes. M0's full browser/build verification remains separately dated evidence.
5. Review the complete change, update status/validation/handoff documents, and commit only the M1 files and fresh evidence.
6. Inspect outgoing Git contents, push the feature branch without force, verify the remote commit, and report any triggered CI result separately from local tests. No merge into `main` is authorized by this publication step.

## Review focus

- Complex amplitudes and global phase, including RY sign and q0 ordering.
- Three-qubit controls and nonadjacent subsystem partial traces.
- Noise after each native gate, with no correlated readout or intermediate measurement claim.
- Fixed statistical seeds/thresholds, valid expected counts, no post-result tuning or retries.
- Independent reference imports, unchanged production execution/limits, preserved user data and historical evidence.

No optional Stim or QuTiP dependency will be added. This milestone tests mathematical/software agreement, not physical hardware calibration or quantum advantage.
