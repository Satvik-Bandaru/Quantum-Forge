# Connected instrument model and contract

Implemented 2026-11-15; extended for v0.6. This is a bounded numerical experiment for one two-level device, with five configurable simulated instruments. It is not a hardware interface, manufacturer digital twin, or experimental calibration of a physical device.

## Authoritative contracts

`backend.instruments.ApparatusConfig` is the saved apparatus model. Unknown properties, nonfinite numbers, out-of-range values, wrong identities and incompatible/reversed/duplicate connections are rejected. There is exactly one of each instrument. Missing links, disabled instruments, injected faults and an unmet temperature interlock are valid saved configurations, but acquisition is blocked. `apparatus_status(config)` is read-only and does not advance time. `validate_runnable(config)` returns that status or raises `ValueError` with its readiness reasons.

All instruments share `enabled: boolean` and `fault: "none" | "injected"`. The latter is an explicit simulated fault injection, not a diagnosis of physical hardware. Their `id` properties have fixed, distinct literal values.

The exact default request is:

```json
{
  "apparatus": {
    "cryostat": {"id":"cryostat","enabled":true,"fault":"none","base_temperature_k":0.02,"initial_temperature_k":4,"cooldown_time_constant_s":180,"elapsed_s":1800},
    "microwave": {"id":"microwave","enabled":true,"fault":"none","frequency_ghz":5,"power_dbm":0,"line_attenuation_db":20,"phase_deg":0},
    "controller": {"id":"controller","enabled":true,"fault":"none","pi_duration_us":0.05,"analysis_phase_deg":0},
    "device": {"id":"device","enabled":true,"fault":"none","frequency_ghz":5,"t1_us":50,"tphi_us":80,"coupling_mhz_per_sqrt_mw":100,"max_temperature_k":0.1},
    "readout": {"id":"readout","enabled":true,"fault":"none","error_0_to_1":0.02,"error_1_to_0":0.04},
    "connections": [
      {"source":"cryostat:thermal","target":"device:thermal"},
      {"source":"microwave:rf","target":"device:drive"},
      {"source":"controller:iq","target":"microwave:iq"},
      {"source":"controller:trigger","target":"readout:trigger"},
      {"source":"device:readout","target":"readout:input"}
    ]
  },
  "sequence":"rabi","points":101,"shots":1024,"seed":42,"sweep_start":0,"sweep_stop":1
}
```

Each connection has a typed, directed output-to-input relationship. These five links are required; the schema accepts zero through five links, and each input can have at most one source. There is no arbitrary network or dynamically created instrument.

Status shape:

```text
{
  ready: boolean,
  instruments: [{id, type, label, state, config, ports, limits, issues}],
  connections: [{source, target}],
  issues: [{code, instrument_id, message}],
  derived: {temperature_k, thermal_population, detuning_mhz,
            rabi_frequency_mhz, gamma_up_per_us, gamma_down_per_us,
            effective_t1_us, effective_t2_us}
}
```

`ports` is `[{id, direction: "input"|"output", signal: "thermal"|"rf"|"iq"|"trigger"|"readout"}]`; `id` here is the local port name. `limits` contains the instrument's Pydantic JSON-schema properties. State is `ready`, `disabled`, `fault`, `cooling` or `disconnected`. Overall readiness always includes all issues, even if a higher-priority individual state masks another issue in the state label.

`backend.connected.ConnectedRequest` accepts the request above, and `run_connected(request)` returns:

```text
{
  kind: "connected", backend: "SciPy finite-segment Lindblad simulator", qubits: 1,
  sequence, seed, shots, apparatus, apparatus_status,
  series: [{x, probability, observed_probability, measured_probability, count_1, shots,
            confidence_low, confidence_high}],
  axes: {x_label, x_unit, y_label},
  metrics: [{label, value, unit}],
  checks: [{name, passed, value, tolerance}],
  model: {name, basis, hamiltonian, detuning_convention, thermal_rates,
          pulse_convention, initial_state,
          sampling: {spacing, unit, estimated_cycles_per_step, warning},
          sources: [{title, url}]},
  limitations: string[],
  versions: {python, numpy, scipy, model},
  runtime_s: number,
  runtime: {wall_seconds, process_rss_bytes, memory_measurement,
            points, shots_per_point, solver: "scipy.linalg.expm", matrix_dimension: 4},
  calibration?: {preparation_assumption, estimated_error_0_to_1,
                 estimated_error_1_to_0, estimated_assignment_fidelity,
                 standard_error_0_to_1, standard_error_1_to_0,
                 confidence_interval_error_0_to_1, confidence_interval_error_1_to_0},
  amplitude_calibration?: {status: "estimated"|"inconclusive", method,
                 estimated_pi_factor, confidence_interval_95, reference_pi_factor,
                 estimated_drive_mhz, negative_log_likelihood, fit_bounds,
                 assumptions, warnings},
  reference?: {label, assumptions, max_absolute_error, series: [{x, probability}]}
}
```

`probability` is the physical density-matrix excited population. `observed_probability` includes the configured assignment channel. `measured_probability` is the independently sampled count divided by shots. Model-derived metrics are labeled as such; they are not fitted estimates. Calibration estimates are derived from actual seeded counts.

## Thermal and drive physics

The backward-compatible `legacy_exponential` refrigerator approximation is

```text
T(t) = T_base + (T_initial - T_base) exp(-elapsed_s / cooldown_time_constant_s).
```

Elapsed time is explicitly simulated time supplied in the configuration, never wall-clock time. Temperature remains fixed during a request. The device temperature threshold is a configurable protective interlock, not a claim that warmer states are mathematically invalid. Each sequence point starts from an independent thermal equilibrium state; repeated-shot reset dynamics are not simulated.

The optional `thermal_network` mode supplies the computed mixing-chamber temperature from the multistage energy-balance model described in [thermal-model.md](thermal-model.md). The same equations below use that temperature. Old configurations without a mode retain the exponential behavior; the result snapshot names the selected model. Temperature evolution occurs in the explicit cryostat elapsed-time domain, not during the microsecond acquisition.

For transition frequency `f` in Hz, use the Gibbs population `p_thermal = 1/(1+exp(h*f/(k*T)))`. The implementation evaluates this in a stable equivalent form. Constants are `h = 6.62607015e-34 J s` and `k = 1.380649e-23 J/K`. The bosonic bath has `nbar = 1/expm1(h*f/(k*T))`. The declared device `t1_us` is the **zero-temperature** lifetime:

```text
gamma_down = (nbar + 1) / t1_us
gamma_up   = nbar / t1_us
gamma_phi  = 1 / tphi_us
T1_effective = 1 / (gamma_down + gamma_up)
T2_effective = 1 / ((gamma_down + gamma_up)/2 + gamma_phi)
```

Thus `gamma_up/gamma_down = exp(-h*f/(k*T))`, and `gamma_up/(gamma_up+gamma_down)` equals the Gibbs population. Thermal T1 shortens with increasing occupation for this stated bath model. The choice of bosonic bath and fixed zero-temperature coupling is a model assumption. The collapse operators follow the standard Lindblad equation and thermal creation/annihilation-rate construction described by [QuTiP's master-equation guide](https://qutip.readthedocs.io/en/stable/guide/dynamics/dynamics-master.html) and [thermal-bath example](https://qutip.readthedocs.io/en/stable/guide/guide-steady.html#example-harmonic-oscillator-in-thermal-bath); applying that bath construction to two device states is this implementation's explicit modeling choice.

Attenuated power in mW is `10**((power_dbm-line_attenuation_db)/10)`. The source produces the cyclic Rabi frequency

```text
Omega_MHz = coupling_mhz_per_sqrt_mw * sqrt(power_at_device_mW).
```

The coupling is a user-declared model parameter, not inferred or calibrated hardware gain. An amplitude sweep multiplies this field amplitude, hence its squared value multiplies delivered drive power.

## Basis, phase, and finite-pulse conventions

`|0>` is the ground state and `Z = diag(1,-1)`, so the physical undriven Hamiltonian is `-hbar*omega_device*Z/2`. Define `delta = f_device - f_source`. In the source rotating frame the diagonal term is `-hbar*2*pi*delta*Z/2`, not its opposite. With time in microseconds, cyclic frequencies in MHz, and phase in radians:

```text
H/hbar = pi * (-delta_MHz * Z + Omega_MHz * (cos(phase)*X + sin(phase)*Y)).
```

For example, a state initially along +X precesses toward -Y when `delta>0`. For ideal instantaneous +X half pulses with final analysis phase `phi`, Ramsey gives `p1 = (1 + cos(2*pi*delta*t + phi))/2` in the ground-state, noiseless limit. The tests distinguish the sign using a +90-degree analysis pulse and both positive and negative absolute source-frequency offsets.

The collapse matrices are `sqrt(gamma_down)|0><1|`, `sqrt(gamma_up)|1><0|`, and `sqrt(gamma_phi/2) Z`. Vectorization uses column order and a 4×4 Liouvillian. Every finite square segment is propagated with `expm(L*duration)`, including damping and detuning **during pulses**, as supported by [SciPy's matrix-exponential implementation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.expm.html). The fixed configured `pi_duration_us` is only a nominal pulse duration: changes to power, detuning or coupling can produce underrotation or overrotation. Half pulses use half that duration. No hidden pulse recalibration occurs.

| Sequence | Sweep x and segments |
| --- | --- |
| `rabi` | Pulse duration in µs; one square drive pulse |
| `ramsey` | Total free delay in µs; +half pulse, free delay, +half pulse with analysis phase |
| `echo` | Total free delay in µs; +half, delay/2, +pi, delay/2, -half with analysis phase |
| `t1` | Free delay in µs after the actual finite nominal pi pulse |
| `frequency_sweep` | Source offset **from device resonance** in MHz; one fixed-duration pulse with `delta=-x` |
| `amplitude_sweep` | Dimensionless field factor; one fixed-duration pulse at `Omega*x` |
| `amplitude_calibration` | Same finite-pulse acquisition as `amplitude_sweep`; add sample-derived conditional gain calibration |
| `dephasing` | Same finite-pulse sequence as `ramsey`; show a labeled instantaneous-pulse T2 reference |
| `readout_calibration` | Two ideal input states, x=0 and x=1; no pulses, sweep bounds and requested point count unused |

The echo final-pulse convention yields an excited state after ideal refocusing. Finite off-resonant pulses introduce residual errors, so static-detuning refocusing is approximate. Markovian pure dephasing is not reversed by echo. Frequency sweeps center on device resonance rather than adding an offset to the source's saved frequency; this is explicit in the plot axis and model provenance.

The dephasing protocol does **not** force resonance, recalibrate pulses, or override the configured source/analysis phases. At resonance with zero analysis phase it measures a coherence-decay envelope; detuning produces Ramsey fringes. Its analytical comparison is `p1(t) = [1 + (1-2*p_thermal) exp(-t/T2_effective) cos(2*pi*delta*t+analysis_phase)]/2`. That expression assumes ideal instantaneous calibrated half pulses. The actual trace still uses finite, possibly miscalibrated pulses. Therefore `reference.max_absolute_error` is a reported approximation discrepancy, not a failed numerical validation. T2 includes relaxation and pure dephasing; it is not an inferred Tphi. Absolute common source phase rotates both pulses together and cancels for this phase-covariant initial state and bath; the relative analysis phase remains observable.

## Readout and calibration

The assignment model is `P(observed 1) = error_0_to_1 + (1-error_0_to_1-error_1_to_0)*p1`. NumPy's seeded generator samples independent binomial counts at each point. Same configuration and seed reproduce all series values; runtime and RSS naturally vary.

Every row also reports a 95% **pointwise Wilson score interval** (`confidence_low`, `confidence_high`) for the probability after the assignment channel. These use the actual count and shot total, following the [NIST score-interval construction](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm). They are not simultaneous bands or uncertainty bounds on the physical model. They retain nonzero width even at zero/all-success counts.

Readout calibration assumes ideal independent preparation of `|0>` and `|1>`. Its two rows have true populations exactly zero and one. Estimates are `count_1(prepared 0)/shots` and `1-count_1(prepared 1)/shots`; assignment fidelity is one minus their mean. Legacy standard-error fields remain binomial plug-in estimates and can be zero at endpoints. New `confidence_interval_error_0_to_1` and `confidence_interval_error_1_to_0` fields provide the Wilson intervals (the second uses the complement of the prepared-one interval). This experiment identifies only the synthetic confusion channel under the ideal-preparation assumption. It does not estimate pulse preparation errors or calibrate the device's declared parameters.

## Conditional pulse-amplitude calibration

This protocol executes the same Lindblad finite-pulse acquisition as an amplitude sweep, then fits only the drive gain to `count_1` and `shots`. It does not fit to `probability`, `observed_probability` or the rounded displayed fraction. Temperature, thermal/dephasing rates and readout error settings are held fixed. The inference is conditional on these declared values being exact; their uncertainty and physical-model discrepancy are excluded.

At resonance, the independent Bloch equation gives

```text
z'' + (Gamma1+Gamma2) z' + (Gamma1*Gamma2+w^2) z = Gamma1*Gamma2*z_eq
z_eq = 1-2*p_thermal, w = 2*pi*Omega*x, z(0)=z_eq, z'(0)=0
z_ss = z_eq*Gamma1*Gamma2/(Gamma1*Gamma2+w^2)
k = (Gamma1+Gamma2)/2, v = sqrt(w^2-((Gamma1-Gamma2)/2)^2)
z(t) = z_ss + (z_eq-z_ss)*exp(-k*t)*(cos(v*t)+k*t*sinc(v*t/pi))
p1 = (1-z)/2.
```

Complex square roots express underdamped, overdamped and critical cases without a singular division at `v=0`. This expression does not call the production Liouvillian or matrix exponential. It supplies both an independent analytical check of the acquired resonant predictions (absolute tolerance `1e-8`) and the conditional likelihood model. Declared-gain analytical reference curves are labeled separately from the fitted gain.

The fitted variable is cyclic pulse area `q = Omega*pi_duration`. Its bounds are `q_min=1/(4*sweep_stop)` and `q_max=min(1/(10*spacing), drive_limit*pi_duration/sweep_stop)`, where `drive_limit=min(200 MHz, 5% of transition frequency)`. Thus the search respects the declared rotating-wave bound and at least ten samples per candidate oscillation. A 2,049-point scalar scan locates modes; bounded [SciPy minimization](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize_scalar.html) refines each candidate. The binomial negative log likelihood omits parameter-independent combinatorial terms and uses stable `xlogy`/`xlog1py` evaluation. The inferred pi field factor is `1/(2*q)`, a pulse-area convention; damping can shift the precise population maximum.

The interval solves `2*(NLL(q)-NLL_min)=3.841458820694124`, the one-parameter asymptotic 95% likelihood-ratio threshold described in the [PDG statistics review](https://pdg.lbl.gov/2025/reviews/rpp2025-rev-statistics.pdf). It is a conditional one-parameter interval, **not** a profile over uncertain nuisance parameters and not guaranteed to have exact finite-sample coverage. `fit_bounds` are reported in pi-factor units. Reference pi factor is independently labeled from the declared gain; it is not a fitted observation.

The acquisition remains saved but calibration is `inconclusive`, with null estimates/interval, if the declared acquisition has fewer than ten samples per drive oscillation, the field-factor range is below 1e-12, the source is detuned, the scan does not start at zero, contrast is unresolved, multiple likelihood modes are plausible, an interval reaches search bounds, the measured range fails to bracket its pi-factor interval, or optimization fails. The contrast precheck uses conservative Bonferroni-adjusted score intervals; it is a guard against reporting a fit to unresolved data, not a claim of exact simultaneous coverage. The declared-resolution guard prevents a high-frequency acquisition from aliasing into a confident low-frequency gain estimate. Subnormal sweep ranges retain their acquired samples without attempting unstable reciprocal bounds. No fit silently changes microwave power, coupling or pulse duration. A user may inspect the evidence and deliberately change the controls.

A deterministic coverage probe on the default apparatus, 101 points from factors 0 to 2, seeds 0–29, returned 30 estimates at each shot count. At 128, 1024 and 8192 shots per point, respectively, the reported intervals included the generating pi factor in 30/30, 30/30 and 28/30 cases; mean interval widths were 0.0118086071, 0.00417564655 and 0.00147604659. Maximum absolute estimate errors were 0.00571104073, 0.00172535179 and 0.00103982988. This small reproducible probe checks recovery and shot-count scaling; it does not establish universal 95% coverage.

## Limits, measurement, and verification

Requests allow 51–201 points, 128–8192 shots per point and seeds 0–2147483647. Time-sweep bounds are 0–100 µs for Rabi and 0–500 µs for free delays. Frequency sweeps stay within ±100 MHz and the 1–10 GHz source range. Amplitude sweeps stay within factors 0–2. Source detuning above 100 MHz, drive above 200 MHz, or drive above 5% of the device transition frequency prevents acquisition; amplitude sweep endpoints obey the same drive restriction. These are declared local model limits, not accuracy guarantees for every real device.

Every returned point and intermediate segment is checked for finite entries, trace one, Hermiticity and positive semidefiniteness. Probabilities must be physical to a `1e-8` numerical tolerance before clipping roundoff for binomial sampling. No density normalization or positivity projection conceals errors. The maximum difference between complete-segment exponentials and two half-segment exponentials is reported. This is **same-method floating-point consistency**, not independent validation or a physical-model uncertainty bound.

The independent tests solve the complex density-matrix differential equation using direct commutators and collapse products with [SciPy DOP853](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html), rather than reusing the production Liouvillian. Other tests use analytic detuned Rabi, thermal relaxation, coherence decay, instantaneous Ramsey/echo, finite-pulse limits, readout and binomial references. Tests cover maximum point/shot and long/hot/strong-drive bounds, invalid inputs, missing links, simulated faults, seeded repeatability, source and pulse sensitivity, phase sign, and nonfinite solver failure.

Returned samples are exact numerical predictions only at their specified x values. A conservative warning appears below ten samples per estimated oscillation. Narrowing a sweep or increasing points changes plotting resolution; interpolation does not create new simulated points.

`runtime.wall_seconds` is measured with `time.perf_counter()` from entry through result construction; `runtime_s` is the same value for history compatibility. `process_rss_bytes` comes from `psutil.Process().memory_info().rss` after computation: current whole-process resident memory, including the interpreter and imported libraries. It is not incremental per-job memory, peak RSS, hardware acquisition time or a benchmark promise. One physical qubit and a 4×4 matrix do not imply that total process memory is only a few matrix entries.

This version excludes multilevel transmons, leakage, resonator and amplifier waveforms, microwave line electromagnetics, refrigerator thermodynamics from first principles, bath backaction, non-Markovian noise, crosstalk and real equipment. Ports represent causal model dependencies and readiness, not simulated cable wave propagation.

## Reproduction

```bash
.venv/bin/python -m pytest tests/test_instruments.py tests/test_connected.py tests/test_connected_calibration.py -q
.venv/bin/python -c 'import json; from backend.connected import ConnectedRequest, run_connected; print(json.dumps(run_connected(ConnectedRequest()), indent=2, allow_nan=False))'
```

Sources were checked on 2026-11-15. NumPy/SciPy/Python versions are recorded per acquisition; new acquisitions use model identifier `connected-lindblad-2`. Existing saved v1 evidence remains unchanged. The quantum evolution and seeded counts for the original seven protocols retain their earlier behavior; v2 adds metadata, intervals and the two additional protocols.
