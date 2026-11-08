# Generic QUBO model and solver comparison

The editable QUBO lab minimizes a user-supplied binary polynomial, in arbitrary
energy units. It runs every method on the local classical CPU. PennyLane
simulates the quantum circuit; Ocean runs classical simulated annealing. These
timings cannot demonstrate quantum advantage.

## Input and bit order

`QuboRequest` accepts a square `matrix`, `offset`, `layers`, `iterations`, `shots`
and `seed`. There is no expression parser, executable input or constraint DSL.
The number of variables is inferred from the matrix: 2 through 8, additionally
bounded by the service's configured `QF_MAX_QUBITS`. Unknown fields are rejected.

The matrix must be canonical upper triangular, including its diagonal. Entries
below the diagonal must be zero. Every coefficient must be a finite number in
[-100, 100]; the finite offset is in [-1000, 1000]. Numeric strings and booleans
are rejected. The objective is

```text
E(x) = offset + sum_i Q[i,i] x[i] + sum_(i<j) Q[i,j] x[i] x[j], x[i] in {0,1}.
```

Each off-diagonal entry contributes **once**. Do not copy it into the lower half
of the matrix. This convention is equivalent to `offset + x.T @ Q @ x` for the
accepted upper-triangular matrix. Changing a coefficient changes the actual
objective consumed by all five methods.

The first displayed bit is q0, the most significant bit. Probability arrays and
the energy table use ascending binary order: `00, 01, 10, 11` for two variables.
For example, `[[-3,4],[0,-2]]`, offset 1, has energies `[1,-1,-2,0]`; its unique
minimum is x=`10`, energy -2.

Defaults are p=`layers`=1, `iterations`=35, `shots`=512 and `seed`=42. Bounds are
p in [1,3], iterations in [2p+2,80], shots in [128,4096], and integer seed in
[0,2^31-1]. The minimum optimizer budget initializes the 2p variational angles.

## Constraints are coefficients supplied by the user

The engine does not impose, infer or validate feasibility constraints. A supplied
matrix may already contain a penalty. To encode `sum_i a[i] x[i] = b`, add
`lambda * (sum_i a[i] x[i] - b)^2` to the objective, with positive lambda:

```text
offset += lambda * b^2
Q[i,i] += lambda * (a[i]^2 - 2*b*a[i])
Q[i,j] += 2 * lambda * a[i] * a[j], for i<j.
```

For a concrete editable example, minimize `-3*x0 - 2*x1` with an encoded
`x0+x1=1` penalty of lambda=4. Submit `matrix=[[-7,8],[0,-6]]`, `offset=4`.
Its four energies are `[4,-2,-3,-1]`, with minimum `10`. Reducing lambda to 1
makes the violating assignment `11` best: the penalty weight matters. The lab
reports energies of the supplied polynomial and does not label an assignment
feasible. Encoded coefficients must still satisfy the input bounds.

## Complete Ising mapping

Use `x[i]=(1-z[i])/2`, where `z[i]` is +1 for bit 0 and -1 for bit 1. The exported
mapping retains the full constant, field vector `h`, and upper-triangular `J`:

```text
E(z) = c + sum_i h[i] z[i] + sum_(i<j) J[i,j] z[i] z[j]
J[i,j] = Q[i,j] / 4
h[i] = -Q[i,i]/2 - (sum_(j<i) Q[j,i] + sum_(j>i) Q[i,j])/4
c = offset + sum_i Q[i,i]/2 + sum_(i<j) Q[i,j]/4.
```

The signs follow this explicitly stated spin convention. Other libraries may
choose a different binary-to-spin convention. The test suite independently
evaluates both polynomials for every state of a hand-derived coupled example.

## Actual solver methods

| Result key | Method and budget | Reported energy |
| --- | --- | --- |
| `exact` | Enumerate every one of the at most 256 bitstrings. | Smallest enumerated energy; all degenerate minimizing assignments are exported. |
| `greedy` | Start at zeros, visit variables in q0-first order once and accept strictly improving flips. | Energy of the resulting assignment. |
| `local_search` | `min(16,2*n)` seeded random starts; steepest improving one-bit descent until no improvement. | Best assignment actually evaluated. |
| `annealing` | D-Wave Ocean `SimulatedAnnealingSampler`, requested `shots` reads, 200 sweeps per read. | Best energy among actual returned samples. |
| `qaoa` | PennyLane p-layer QAOA, exact expectation training with SciPy COBYLA and requested evaluation budget; then requested finite-shot sampling. | Best energy among actual sampled bitstrings, separate from `expected_energy`. |

The exact optimum is a separate reference. No heuristic solution or sample is
replaced by an exact answer. Every row reports an absolute optimality gap
`energy - exact_energy`; QAOA also reports `expected_gap`. Relative quality ratios
are unsuitable here because optimum energies can be zero or negative.

Each method has its own `runtime_s` measured by a local wall clock. Enumeration
includes construction of the full energy table. QAOA and annealing separately
report `initialization_s`: QAOA includes SciPy/PennyLane imports, device/circuit
construction and optimizer setup; annealing includes Ocean imports, BQM and
sampler construction. Their `runtime_s` starts immediately before optimization
or sampling and includes reduction of the returned samples. Initialization is
excluded from these two solver work times. Lazy library initialization during
the first circuit evaluation remains part of QAOA work time.

The top-level `runtime_s` includes both initialization phases, every solver,
metadata/version collection and result assembly. It starts after input
validation and ends before JSON serialization. Warmed versus cold processes can
differ. No timing is a QPU time, and the work times do not measure equal budgets.

Evaluation counts have explicit units: exhaustive, greedy and local-search rows
count scored bitstrings; QAOA counts optimizer expectation calls. Annealing's
`evaluations` counts returned reads whose sample energies are reported, **not**
internal objective calls; its separate `spin_update_budget` is reads × sweeps ×
variables. These units and budgets differ. A single seeded run is an illustration,
not a statistical performance study.

## QAOA circuit and measurement

The circuit starts in `|+>^n` and repeats cost evolution followed by the X mixer:

```text
U_cost(gamma) = exp[-i * gamma * (sum h[i] Z[i] + sum J[i,j] Z[i] Z[j]) / scale]
U_mix(beta)   = exp[-i * beta * sum X[i]]
scale = max(1, sum abs(h[i]) + sum_(i<j) abs(J[i,j])).
```

The commuting cost terms are implemented directly with
`RZ(2*gamma*h[i]/scale)` and `IsingZZ(2*gamma*J[i,j]/scale)`. The mixer uses
`RX(2*beta)` on every wire, matching the
[PennyLane cost/mixer evolution conventions](https://docs.pennylane.ai/en/stable/_modules/pennylane/qaoa/layers.html).
The constant contributes only a global phase. It is retained in every reported
energy but omitted from circuit evolution and normalization. Adding a constant
therefore leaves fixed-angle probabilities unchanged.

Parameters are exported in the order `gamma[0:p], beta[0:p]`. Initial angles are
drawn uniformly in [0,pi) from the configured seeded NumPy generator. COBYLA
minimizes `(expectation - c)/scale`; the unscaled expectation is recorded at each
evaluation. The best evaluated parameters supply the final ideal probability
vector. The same seeded generator then draws a multinomial histogram with the
requested shot count. Finite-shot sampling can miss the ideal minimum even when
its probability is nonzero. Neither shot noise during optimization nor hardware
noise is modeled.

Reported `depth`/`logical_depth` is the critical-path depth of the exact logical
gate sequence in H, RZ, IsingZZ and RX operations. It excludes gate decomposition,
hardware topology, routing, measurement scheduling and calibration. The scalar
`p` counts cost/mixer layer pairs and is not the same quantity as gate depth.

The annealing backend uses Ocean's
[binary quadratic model](https://docs.dwavequantum.com/en/latest/ocean/api_ref_dimod/models.html)
and [classical simulated-annealing sampler](https://docs.dwavequantum.com/en/latest/ocean/api_ref_samplers/index.html).
No remote solver or quantum hardware is contacted.
For an entirely constant QUBO, an explicit inverse-temperature range [0.1,1]
avoids Ocean's automatic schedule heuristic warning; seeded uniform random
initial states still produce valid, uninformative samples of this flat cost.

## Result and reproducibility

The JSON result contains the accepted matrix and offset, all state energies,
complete Ising coefficients, exact reference, actual solver rows, method-specific
traces, QAOA parameters/probabilities, annealing and QAOA histograms, seed, limits,
library versions and interpretation limits. All calculations use floating-point
arithmetic. The bounded enumeration is exhaustive for the supplied model, with
the usual floating-point precision limit for nearly equal energies.

Tests cover strict finite validation and boundaries, all-state Ising equality,
an analytically solvable QAOA single-bit cost, independent complex-state evolution
with couplings and multiple layers, offset-invariant fixed-angle evolution,
actual sample minima, a greedy counterexample, a fully degenerate constant cost,
the optimizer budget, deterministic seeded sampling, and finite JSON export.
