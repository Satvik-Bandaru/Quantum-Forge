# Driven two-level physics lab

The physics lab simulates one abstract qubit under a constant square pulse. It compares a coherent reference, a density-matrix solution with relaxation and dephasing, and finite-shot samples of that noisy solution. Everything runs locally on the CPU with NumPy and SciPy; this is not hardware execution or device calibration.

## Model and units

The ordered basis is `|0> = ground`, `|1> = excited`. The Pauli convention is `Z = diag(1, -1)`, so ground lies at Bloch `z = +1`. Initial states are ground, excited, or `|+> = (|0> + |1>)/sqrt(2)`.

Time is in microseconds. `drive_mhz = Omega` and `detuning_mhz = Delta` are **cycles per microsecond**, equivalent to MHz. They are converted to angular frequency inside the Hamiltonian:

```text
H / hbar = (2*pi*Delta*Z + 2*pi*Omega*(cos(phi)*X + sin(phi)*Y)) / 2
```

This is an effective rotating-frame model with a constant pulse envelope. Signed detuning is explicitly the coefficient of `+Z`; no laboratory carrier frequency or absolute energy splitting is supplied. `phi` is `pulse_phase_rad`. At resonance, a positive X pulse rotates ground toward negative Bloch Y. A positive Y pulse rotates ground toward positive Bloch X.

The density matrix obeys the Lindblad equation:

```text
d(rho)/dt = -i[H/hbar, rho]
            + sum_C (C*rho*C† - (C†*C*rho + rho*C†*C)/2)

C_relaxation = sqrt(1/T1) * |0><1|
C_dephasing  = sqrt(1/(2*Tphi)) * Z
1/T2         = 1/(2*T1) + 1/Tphi
```

`null` disables the corresponding channel. With both channels disabled, `t2_us` is `null`, meaning unbounded coherence time within this model. The `1/(2*Tphi)` factor in the dephasing operator ensures off-diagonal elements decay at `1/Tphi`; it is not a second independent definition of T2. Relaxation is zero-temperature amplitude damping to ground.

The ideal reference uses the same pulse and initial state with both dissipative channels disabled. It is never replaced by an idealized damped sine wave.

## Numerical method and independent checks

For a constant generator, the engine constructs a 4-by-4 complex128 Liouvillian by its action on matrix units, using column-major vectorization. Each requested time is evaluated directly from the common initial state:

```text
vec(rho(t)) = scipy.linalg.expm(L*t) @ vec(rho(0))
psi_ideal(t) = scipy.linalg.expm(-i*H*t/hbar) @ psi(0)
```

There is no time integration step whose size must converge. Floating-point matrix exponential errors still exist. Before returning, the engine checks finiteness, trace preservation, Hermiticity and the minimum eigenvalue across the whole trace against `1e-9`. It rejects results that fail these checks. It does not renormalize the density matrices or project their eigenvalues. Probabilities are clipped only to remove roundoff excursions beyond `[0, 1]` before binomial sampling. Diagnostics retain the original matrix errors.

Independent analytic tests in `tests/test_physics.py` include:

- Ground at resonance: `P1(t) = sin²(pi*Omega*t)`.
- Ground with detuning: `P1(t) = Omega²/(Omega²+Delta²) * sin²(pi*sqrt(Omega²+Delta²)*t)`.
- Undriven excited state: `P1(t) = exp(-t/T1)`.
- Undriven plus state: transverse coherence decays as `exp(-t/T2)`.
- Pulse phase and detuning signs, final purity and pure-reference fidelity, density-matrix invariants, bounded requests, finite JSON, and seeded shot reproducibility.

These are tests of the implemented mathematical model. They do not establish that the model describes a particular laboratory device.

## Scope and measurement interpretation

Each scope time represents **fresh preparation, evolution for that duration, and final measurement**, repeated `shots` times. The engine draws independent `Binomial(shots, noisy_p1)` counts at every point. There is no intermediate collapse, continuous detector measurement, or measurement feedback. The total number of simulated shots is `points * shots`.

`stderr = sqrt(p*(1-p)/shots)` uses the predicted noisy probability. It is a theoretical standard error, not a confidence interval or a sample-derived uncertainty estimate. It can be zero at deterministic endpoints. Readout error is not included. The random seed reproduces the sampled trace within the recorded NumPy version; it does not alter the underlying evolution.

The time grid includes both endpoints and must contain at least 12 intervals per generalized Rabi cycle. For example, a 3 MHz drive and 4 MHz detuning give a 5 MHz generalized frequency; a 1 microsecond run requires at least 61 points. Requests that exceed this bound are rejected rather than silently aliased. Zero generalized frequency has no cycle-sampling metric (`null`). Short relaxation times may still fall between displayed points; each reported point remains a direct matrix exponential evaluation.

## Request and result contract

`backend.physics.PhysicsRequest` extends the shared strict model, rejecting unknown fields and non-finite numbers.

| Parameter | Default | Bounds |
| --- | --- | --- |
| `drive_mhz` | 1 | 0 to 20 |
| `detuning_mhz` | 0 | −20 to 20 |
| `duration_us` | 3 | 0.001 to 50 |
| `pulse_phase_rad` | 0 | −2π to 2π |
| `t1_us`, `tphi_us` | 8, 5 | `null` or 0.05 to 10000 |
| `initial_state` | ground | ground, excited, plus |
| `points` | 301 | integer 51 to 1001, plus cycle-resolution check |
| `shots` | 1024 | integer 128 to 8192 per time point |
| `seed` | 42 | integer 0 to 2³¹−1 |

`run_physics(config)` returns JSON-compatible values:

- Identification: `kind = physics`, `backend`, `runtime_s`, `qubits = 1`, `seed`, `shots`, and `versions` for NumPy/SciPy.
- `series`: rows with `time_us`, `drive_mhz`, `ideal_p1`, `noisy_p1`, `sampled_p1`, `stderr`, `bloch_x`, `bloch_y`, and `bloch_z`. Bloch coordinates describe the noisy ensemble density matrix in the rotating frame. `drive_mhz` is the constant pulse envelope, not a rendered carrier oscillation.
- `final_density_matrix`: 2-by-2 matrix in the declared basis; every entry is `[real, imaginary]`.
- `metrics`: final ideal/noisy P1, purity `Tr(rho²)`, squared Uhlmann fidelity to the pure ideal state `<psi_ideal|rho|psi_ideal>`, T2, generalized Rabi frequency, maximum trace/Hermiticity errors, minimum eigenvalue across time, time step, samples per cycle, experiment count and total shots.
- `checks`: `passed`, `finite`, `trace_preserved`, `hermitian`, `positive_semidefinite`, and numeric `tolerance`.
- `model` and `limitations`: explicit scientific conventions, solver provenance and interpretive limits.

The owning job/API layer saves the executed configuration and this result. The engine itself does not write to storage.

## Limits and sources

This model excludes multilevel leakage, counter-rotating terms, pulse distortion, thermal excitation, correlated noise, bath memory and crosstalk. It should not be used to infer behavior outside an effective two-level rotating-wave description. The numerical diagnostics establish internal consistency, not hardware accuracy or quantum advantage.

The implementation uses the existing SciPy dependency. [SciPy's matrix exponential documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html) describes its numerical method. The [Qiskit Dynamics Rabi tutorial](https://qiskit-community.github.io/qiskit-dynamics/stable/tutorials/Rabi_oscillations.html) provides a primary project reference for driven-qubit Hamiltonians and Markovian relaxation/dephasing. Its dephasing rate notation differs; this project's operator and Tphi convention are defined explicitly above. No Qiskit Dynamics or QuTiP solver dependency is required.
