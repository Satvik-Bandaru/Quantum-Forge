# Bounded quantum research models

`backend/research.py` implements two local CPU experiments through `ResearchRequest` and `run_research`. They add no dependencies or hardware access. Inputs are finite, unknown fields are rejected, and execution revalidates copied request models. Each run allows 128–8192 shots and a seed from 0 through 2³¹−1. All transmissions, efficiencies, coherence factors and probabilities are dimensionless fractions in [0,1]; angles are radians.

The result contains `kind: research`, the experiment name, backend description, runtime, seed, shots, NumPy version, labeled probabilities/counts, numeric metrics, an exact reference series, the actual final density matrix, checks and limitations. Complex matrices serialize each entry as `[real, imaginary]`. Numerical checks inspect the unprojected computed states for finite entries, trace one, Hermiticity and nonnegative eigenvalues within 10⁻¹⁰. They check the specified mathematics, not a real device.

## Three-qubit repetition code

`experiment: repetition_code` prepares

\[
|\psi\rangle=\cos(\theta/2)|0\rangle+e^{i\phi}\sin(\theta/2)|1\rangle,
\quad 0\le\theta\le\pi,\;-2\pi\le\phi\le2\pi.
\]

`theta_rad` and `relative_phase_rad` specify this arbitrary pure state. Encoding maps its two amplitudes to `|000>` and `|111>`; it does not clone the state. The implementation explicitly constructs the eight-dimensional encoded density matrix and sums all eight independent Pauli-X error patterns with probabilities `p^weight (1-p)^(3-weight)`, where `p = bit_flip_probability`.

Ideal parity projectors measure `Z0Z1` and `Z1Z2` without reading the logical bit. Basis ordering is `|q0 q1 q2>` with q0 most significant. Syndrome `1` means odd parity (eigenvalue −1). Recovery maps `00 → I`, `10 → X0`, `11 → X1`, `01 → X2`. The recovered state is inverse-encoded with two CNOTs and the two work qubits are traced out. This follows the repetition-code encoding and stabilizer interpretation described in [IBM's error correction lesson](https://quantum.cloud.ibm.com/learning/en/courses/foundations-of-quantum-error-correction/correcting-quantum-errors/repetition-codes) and [IBM's repetition-code tutorial](https://quantum.cloud.ibm.com/docs/en/tutorials/repetition-codes).

An independent reference is

\[
p_L=3p^2(1-p)+p^3=3p^2-2p^3,\qquad
\rho_L=(1-p_L)\rho+p_LX\rho X.
\]

The implementation compares this formula with the recovered density, rather than substituting it for recovery. Fidelity means the pure-input overlap `F = <ψ|ρL|ψ>`. Thus `F = 1 − pL(1 − |<ψ|X|ψ>|²)`. The unencoded comparison uses the same input and one physical X channel with probability p. An X eigenstate has fidelity one even when the logical-X probability is large. For p>0.5 this fixed decoder increases logical error; no hardware threshold or fault-tolerance claim follows.

`counts` and `probabilities` label logical channel branches `logical_I` and `logical_X`, not measurement outcomes. The same seeded trials sample three independent physical errors, their syndrome and final logical Z measurement. `pattern_counts`, `syndrome_counts` and `measurement_counts` retain their separate meanings. `trial_preview` contains at most the first 32 trajectories. Aggregate counts include every shot. `encoded_density_matrix`, `corrected_density_matrix` and `final_density_matrix` expose the state evolution. The 101-row `series` is the exact reference pL versus physical p and does not consume additional shots.

This is one correction round with three data qubits. Ideal syndrome projectors eliminate measurement ancillas from the simulated state; the reported three qubits are not a claim that a complete physical syndrome circuit needs only three qubits. Encoding, measurement, correction and decoding are perfect. Only independent X errors are included: phase errors, correlated errors, gate/readout error, leakage and amplitude damping are outside the model. Protection against one X error is not protection against general quantum noise.

## One-photon Mach–Zehnder interferometer

`experiment: single_photon_mzi` injects exactly one photon in input mode zero per trial. Its optical state space is `|vacuum>`, `|1,0>`, `|0,1>`. This is separate from the existing classical photonics module, whose readings are noisy optical powers.

Each splitter uses the unitary amplitude matrix

\[
B(T)=\begin{pmatrix}\sqrt T&i\sqrt{1-T}\\i\sqrt{1-T}&\sqrt T\end{pmatrix}.
\]

`splitter1` and `splitter2` are photon transmission probabilities. Between the splitters,

\[
A=\operatorname{diag}(\sqrt{u}e^{i\varphi},\sqrt\ell),
\]

where `u = upper_transmission`, `ℓ = lower_transmission` and `phase_rad = φ` is bounded to ±4π. Attenuation acts on amplitudes through square roots. Lost population transfers to vacuum after tracing out the environment; it is not renormalized away. `path_coherence = γ` multiplies the arm density's off-diagonal entries before the second splitter. This is a valid phase-damping channel: γ=1 retains path coherence and γ=0 completely removes it while retaining the populations.

For an independent analytic reference, define `a=T1 T2 u`, `b=(1−T1)(1−T2)ℓ`, `c=T1(1−T2)u`, `d=(1−T1)T2ℓ`. Then

\[
P_0=a+b-2\gamma\sqrt{ab}\cos\varphi,\qquad
P_1=c+d+2\gamma\sqrt{cd}\cos\varphi.
\]

Optical survival is `S = T1 u + (1−T1)ℓ`, and `P(vacuum)=1−S`. Ideal balanced lossless splitters give `P0=sin²(φ/2)` and `P1=cos²(φ/2)`. Fully dephased balanced paths instead give phase-independent half probabilities. Port labels depend on the explicitly stated splitter phase convention.

Detector efficiency is applied after optical evolution: `P(Dj)=ηj Pj`. `P(no_click) = P(vacuum) + (1−η0)P0 + (1−η1)P1`. Metrics separate optical loss from missed detection. The reported density is the optical output before detector absorption, including vacuum; it does not replace lost photons with postselected surviving photons. Tiny floating-point excursions are bounded only when constructing the normalized sampling probabilities.

Counts are one seeded multinomial experiment with mutually exclusive outcomes `detector0`, `detector1`, `no_click`. They sum to `shots`, and this ideal one-photon model has zero double-click probability. The single-photon occupancy and exclusive detection events distinguish this model from power sampling; the shape of its interference fringe alone does not prove nonclassical light. This interpretation is consistent with the photon anticorrelation and one-photon interference distinction in [Grangier, Roger and Aspect (1986)](https://doi.org/10.1209/0295-5075/1/4/004), whose [paper is available here](https://courses.physics.illinois.edu/phys513/sp2019/reading/week1/GrangierSinglePhoton1986.pdf).

The 101-row `series` varies phase from 0 through 2π at fixed remaining settings and contains exact detector probabilities, not additional observations. Visibility is the exact `(maximum−minimum)/(maximum+minimum)` for each detector; it is null when that detector has no signal, including zero efficiency.

The source, two spatial modes, polarization and frequency are ideal. There are no dark counts, source vacuum trials, multiphoton contamination, diffraction, timing, detector dead time, afterpulsing or saturation. The phase-damping coefficient is a specified channel, not an empirically fitted decoherence source. Two-photon Hong–Ou–Mandel interference and arbitrary optical networks remain outside this experiment.

## Verification

`tests/test_research.py` uses independent polynomial, complex-state and interference fixtures. Coverage includes arbitrary phase-bearing states; code-space recovery; syndrome/error-pattern consistency; the distinction between logical errors and infidelity; balanced and unbalanced interferometers; complete loss and disabled detectors; coherence removal; exact probability conservation; density positivity and trace; seeded sampling at the shot limit; finite JSON serialization; and invalid requests. Run `.venv/bin/python -m pytest tests/test_research.py -q`. Endpoint checks include p=0/1, zero/one splitter transmission, zero/one detection efficiency, and complete arm loss.
