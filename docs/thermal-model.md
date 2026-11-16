# Connected thermal instrument model

This is a functional educational thermal circuit. It is **not** a calibrated dilution refrigerator, helium-mixture thermodynamic model, manufacturer performance curve or live instrument feed. The three dynamic nodes represent an intermediate shield, cold plate and mixing chamber; a fourth node is a fixed room-temperature boundary.

## Equations and units

Each dynamic node has temperature `T_i` (K), constant heat capacity `C_i` (J/K), declared heat load `L_i` (W), cooler conductance `G_i` (W/K), cooler bath setting `B_i` (K) and maximum cooling power `P_i` (W):

```
Q_cool_i = min(P_i, max(0, G_i (T_i - B_i)))
C_i dT_i/dt = L_i + sum_j K_ij (T_j - T_i) - Q_cool_i
```

`K_ij` is a symmetric thermal conductance in W/K. Each internal link contributes equal and opposite heat flows, so it does not create energy. The room-to-shield link exchanges energy with a fixed external reservoir. The coolers are ideal active sinks: they remove heat above their bath settings, saturate at their power limits, and do not heat a colder node. The reservoir temperature is a cooler parameter, not a hard temperature clamp.

This follows the standard lumped-node heat-balance framework described in [NASA's thermal network report](https://ntrs.nasa.gov/api/citations/19700019696/downloads/19700019696.pdf). The capped cooler law and all parameter values are deliberate educational model choices; that reference does not validate this refrigerator's fidelity.

The current defaults are:

| Node | Initial K | Bath K | C (J/K) | Load W | Cooler G (W/K) | Cooling limit W |
|---|---:|---:|---:|---:|---:|---:|
| Shield | 60 | 50 | 500 | 0.2 | 0.5 | 50 |
| Cold plate | 5 | 4 | 5 | 0.001 | 0.1 | 1 |
| Mixing chamber | 0.1 | 0.02 | 0.002 | 0.000001 | 0.002 | 0.0002 |

The fixed room is 300 K. Link conductances are 0.002 W/K (room→shield), 0.00002 W/K (shield↔cold plate), and 0.0000002 W/K (cold plate↔mixing chamber). These values describe a demonstration already near cryogenic operating conditions, not a realistic room-temperature cooldown procedure. At 1800 simulated seconds the default mixing chamber is approximately 0.02089988644 K.

## Numerical method and conservation

`backend/thermal.py` uses SciPy `solve_ivp(method='Radau')` because stage time scales can be stiff. The [SciPy solver documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) describes this implicit integration method. Public configuration does not control numerical tolerances: relative tolerance is `2e-8`, absolute tolerance `1e-10`, and RHS evaluations are bounded at 20,000. An inspection recomputes a deterministic elapsed-time snapshot; opening a panel never advances time.

Two extra ODE states integrate room-boundary input and total cooler removal. The diagnostic ledger checks:

```
stored_change = sum_i C_i (T_i(final) - T_i(initial))
stored_change = total_declared_load * elapsed + boundary_heat - cooling_removed
```

The absolute residual threshold is `1e-6 J + 2e-7 * max(|stored_change|, |load_energy|, |boundary_heat|, |cooling_removed|)`. This ledger is a conservation diagnostic, not independent solver validation or physical uncertainty. Independent analytical and DOP853 tests provide separate numerical checks.

Supported finite capacities are 0.001–100,000 J/K; conductances and load/cooling ranges are explicitly bounded in the Pydantic schema. Temperatures are 0.005–350 K and time is 0–604,800 s. An outward crossing of the 350 K domain boundary (0.1 microkelvin event tolerance) truncates the trace and blocks quantum acquisition. A state initially at 350 K that stays constant or cools is valid. Nonfinite states, failed integration, evaluation-budget exhaustion or failed energy balance raise an explicit numerical error, never fabricated output. The device's separate operating-temperature interlock normally blocks acquisition well before this thermal domain boundary.

## Connection to the quantum experiment

Select `cryostat.thermal_model = 'thermal_network'`. Its `network` object stores every stage and link setting; `cryostat.elapsed_s` determines the evaluated snapshot. The calculated mixing-chamber temperature becomes `apparatus_status.derived.temperature_k`. Existing quantum dynamics then use:

```
p_thermal = 1 / (1 + exp(h f / (k_B T)))
nbar = 1 / expm1(h f / (k_B T))
gamma_down = (nbar + 1) / T1_zero
gamma_up = nbar / T1_zero
1 / T2_effective = (gamma_down + gamma_up) / 2 + 1 / Tphi
```

Changing a heat load, cooling capacity, conductance, initial condition or elapsed time therefore changes the actual thermal state and, when relevant, the computed population and decoherence rates. All temperatures are frozen during one quantum sweep; every sweep point is reset to this thermal state. The model excludes microwave heating feedback, helium flow, latent heat, radiation laws and temperature-dependent material properties. Setting microwave attenuation does not silently create a thermal load.

The legacy exponential mode remains the default for existing configurations: `T = Tb + (Ti-Tb) exp(-elapsed/tau)`. Its prior fields and numerical behavior remain unchanged. Old History snapshots without the new keys receive that compatible default.

## Instrument state and uncertainty

Each instrument exposes its category, operating state, typed physical-state quantities, typed ports, input/output signal snapshots, calibration state and physical-parameter uncertainty metadata. RF power is reported after the configured line attenuation. A failed, disabled or missing upstream path propagates an unavailable signal and a disconnected downstream state. Warm but otherwise operational cryostats can predict their temperature while the quantum device remains interlocked.

The quantum-device readout port is `pending_acquisition` until an experiment is executed. Instrument inspection never invents counts. All physical parameters begin `declared_uncalibrated`, with `standard_uncertainty: null` and `basis: not_estimated`. Saved calibration results provide evidence; they do not silently certify or overwrite the apparatus. Numerical solver tolerance is separate from calibration uncertainty, and finite-shot intervals belong to acquired measurement results.

## Verification

`tests/test_thermal.py` checks zero time, independent exponential cooling, linear heating with zero cooling, saturated cooling, isolated coupled-node energy conservation and weighted equilibrium, heat-load sensitivity, an independently written DOP853 RHS, tolerance refinement, boundary heat signs, the upper-domain stationary/cooling/heating cases, downstream bath-rate changes, legacy compatibility, invalid inputs and injected solver failure. `tests/test_instrument_signals.py` checks attenuated signals, upstream failure propagation and honest calibration/uncertainty labels.

A local Apple Silicon diagnostic exercised 40 seeded random parameter combinations within the declared ranges: median runtime 0.013 s, maximum 0.073 s; 11 correctly terminated at the temperature domain boundary. The default apparatus inspection took about 0.026 s with an energy residual of approximately `-1.1e-11 J`. These are observed timings, not performance guarantees or hardware-accuracy claims.
