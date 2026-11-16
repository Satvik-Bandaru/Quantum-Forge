# M1 validation plan — independent circuit references

Plan fixed before numerical results on 2026-11-15. No optional dependency is introduced. The reference package may import only standard-library modules, NumPy, SciPy, Pydantic and its own reference modules; it may not import production execution code, Qiskit or PennyLane.

## Numerical conventions and bounds

q0 is the leftmost basis bit. Angles are radians. Pure states start at `|0...0>`; density matrices start at its projector. The local unitary gate set is X, Y, Z, H, S, SDG, T, TDG, P, RX, RY, RZ, CNOT, CZ, CP, SWAP and CCX. Gate dictionaries use `target`, `control`, `control2` and `angle` as in the application. Terminal M markers are ignored during pre-readout evolution, matching the production convention; gates after measurement are rejected. No intermediate measurement collapse is modeled.

Statevector references accept 1–8 qubits, density references 1–6, and at most 128 gates. Complex128 arithmetic is used. The reference noise API accepts finite probabilities from 0 to 1, a safe convex-mixture range containing the application's narrower configuration range. It does not expose the larger arity-dependent range accepted by Aer.

After a gate on subsystem S, the density channel is

`rho -> (1-lambda) rho + lambda (I_S / 2**|S|) tensor Tr_S(rho)`,

with axes restored to their original positions. This is subsystem depolarization, not replacement of the entire state. The coherent part is `U rho U†`. Final assignment noise independently flips each output bit with probability e. Ideal amplitudes and noisy sampled counts are checked separately.

## Component and invariance checks

Hand-derived tests cover gate truth tables and complex phases, Bell coherences, local depolarization of entangled states, unaffected spectator states, nonadjacent controls, trace/Hermiticity/positive semidefiniteness, readout endpoints and invalid inputs. These expected values do not come from production execution or another call to the function being tested.

Metamorphic tests use fixed seed `2026111503 + qubits`, insert H/H, X/X, S/SDG and T/TDG pairs, commute disjoint gates, and relabel qubits with output axes permuted accordingly. Both the reference and production outputs are checked. A deliberate RY-sign mutation must be detected by an amplitude-level comparison even when probabilities alone could agree. Import guards enforce the reference boundary statically and in an isolated process.

## Ideal differential family

- 300 cases, generator seed `2026111501`, cycling through 1–8 qubits.
- H/RY/P preparation and 8–32 random native gates, with valid randomly ordered controls and terminal measurement markers.
- Compare reference amplitudes with the actual `circuit_from_config` → Qiskit Statevector → `inspect_state` path.
- Align a single global phase; absolute tolerance `1e-10`, relative tolerance zero. Check normalization separately so arbitrary scale is not accepted as phase equivalence.
- Record each actual case, qubit count, maximum aligned error and elapsed time. This bounded set is regression evidence, not exhaustive proof for all circuits.

## Noisy differential family

- 30 cases, generator seed `2026111502`; Aer seeds `1618033 + i`, i=0..29.
- 8,192 shots per circuit; 2–4 qubits.
- Gate noise `0.06 + 0.02*(i % 4)` and readout noise `0.20 + 0.02*(i % 3)`.
- Use the actual `execute_circuit` path with unchanged native basis/transpilation settings, and reference exact outcome probabilities in the same q0-leftmost order.
- Pearson chi-square goodness-of-fit, df=`2**n - 1`, with no parameters estimated from the counts. Assert matching count totals and each expected/observed bin at least 5; reject an invalid test rather than silently merging bins or replacing seeds.
- Holm step-down correction for the fixed 30-test family at family alpha `0.001`: sort p-values, multiply ordered p-value i by `(30-i)`, take the running maximum and cap at 1; restore original ordering. Any adjusted p-value at or below alpha fails the family.
- Preserve raw p-values, adjusted values, chi-square statistics, minimum expected counts, inputs, seeds and timings in an explicitly requested new report path. Normal test runs do not rewrite historical evidence.

The p-value test is asymptotic and has a nonzero false-rejection risk. Fixed seeds make regressions repeatable, not statistically certain. Thresholds, seeds, noise strengths and case selection must not be changed in response to a failing result. Investigate numerical or implementation discrepancies and report legitimate statistical failures. Passing does not establish correctness outside the cases tested.

## Evidence and acceptance

Run `.venv/bin/python -m pytest -m reference -q`, the explicit mutation-guard case, and `.venv/bin/python -m pytest -q`. Register `reference` and `sbc` markers now; no SBC experiments are implemented in M1. Retain new logs under `docs/verification/codex-m1-reference/`, including test-first failures, final counts, measured runtimes and detailed numerical results. Aim for the ordinary full suite to remain below about 60 seconds on the local machine; report measured time rather than assume it.

No UI/API/job/store path is changed, so M0's full 40-test browser/build result remains prior evidence rather than a fresh M1 claim. GitHub CI, if triggered by the authorized push, is reported separately with its actual result.

## Primary references

- [Qiskit Aer depolarizing-error definition](https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html): channel parameterization and the completely depolarizing limit. Local subsystem extension follows from applying that channel while preserving the spectator partial trace.
- [SciPy Pearson chi-square documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chisquare.html): goodness-of-fit interpretation, fixed-probability degrees of freedom, count-total equality and small-bin restrictions.
- [R statistical documentation for p-value adjustment](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html): Holm's family-wise adjustment and its primary reference, Holm, S. (1979), “A Simple Sequentially Rejective Multiple Test Procedure,” Scandinavian Journal of Statistics 6(2), 65–70. The implementation also has independent hand-calculated regression fixtures. An attempted university-hosted copy of the original paper returned HTTP 403; no claim is made to have fetched that full text.

These are mathematical/software checks. No hardware calibration, quantum advantage, new uncertainty inference or physical-device fidelity claim follows from M1.
