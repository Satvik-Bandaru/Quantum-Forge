# Classical Mach–Zehnder model

This experiment calculates steady-state **classical optical fields and powers**
for one coherent source, two beam splitters, two mirror paths, one phase
shifter, and two power meters. It uses NumPy and does not call a quantum
simulator. The two modes are optical paths. The shared run metadata reports
`qubits: 0`; no qubits or quantum density matrices are modeled.

The bench has a fixed topology:

```text
                          upper mirror → phase shifter
coherent source → BS1  <                                > BS2 → meter 0
                          lower mirror                       → meter 1
```

`bench_components` records the eight placed components. All must be present
exactly once before a request can run. Their order in the list does not alter
the fixed optical topology. An interface can retain an incomplete bench while
the user assembles it, but execution rejects incomplete or duplicate inventories.

## Field convention and units

Input power `power_mw` is in mW. Complex field amplitudes have units
√mW, so their squared magnitudes are powers. For each lossless beam splitter,
`splitter1` or `splitter2` is the **power transmission** fraction T:

```text
       [ √T       i√(1−T) ]
B(T) = [                   ]
       [ i√(1−T)  √T      ]

Ein  = [√P, 0]ᵀ
D    = diag(√ηU exp(iθ), √ηL)
Eout = B(T2) D B(T1) Ein
θ    = phase_rad + 2π × path_difference_um × 1000 / wavelength_nm
```

`upper_transmission` and `lower_transmission` are power transmission fractions
ηU and ηL; fields are attenuated by their square roots. The path difference is
an **optical** path difference in μm. Multiplication by 1000 converts μm to nm
before division by the wavelength. Refractive-index dispersion is not modeled.
For example, .25 μm at 500 nm adds π radians; at 1000 nm it adds π/2.

Mirrors redirect ideal path modes. Any fixed relative phase from the mirrors
is absorbed into `phase_rad` or the optical path difference. The reflection
amplitude +i√(1−T) fixes the port convention: with balanced splitters and no
loss, phase zero makes meter 0 dark and meter 1 bright.

Define the dimensionless real amplitudes

```text
a = √(T1 T2 ηU)                 b = √((1−T1)(1−T2)ηL)
c = √(T1(1−T2)ηU)             d = √((1−T1)T2 ηL)

E0 = √P (a exp(iθ) − b)        E1 = i√P (c exp(iθ) + d)
P0 = P(a² + b² − 2ab cos θ)   P1 = P(c² + d² + 2cd cos θ)
```

In the balanced ideal case this gives
`P0 = P sin²(θ/2)` and `P1 = P cos²(θ/2)`.

The total transmitted power and arm loss are

```text
Pout  = P [T1 ηU + (1−T1)ηL]
Ploss = P [1 − T1 ηU − (1−T1)ηL].
```

Both are independent of phase and of the second beam splitter. The returned
`power_balance_error_mw = P − Ploss − (P0 + P1)` exposes floating-point residuals.
Loss is optical arm loss; electronic meter noise does not change this balance.

## Visibility and sweep

The displayed sweep changes the **phase-shifter setting** from 0 through 2π
inclusive while holding wavelength, path difference, splitters, and arm
transmissions fixed. It replaces the selected `phase_rad` for sweep rows. The
row's `phase_rad` and `phase_pi` describe that setting; the optical path offset
is still added internally. Metrics, complex fields, and repeated meter readings
use the request's selected `phase_rad`.

Visibility uses exact noiseless extrema over a full phase cycle:

```text
P0,min/max = P(a ∓ b)²         V0 = 2ab / (a²+b²)
P1,min/max = P(c ∓ d)²         V1 = 2cd / (c²+d²).
```

This avoids dependence on the number of plotted points or whether a grid
point lands exactly on an extremum. A nonzero constant signal has visibility
zero. A port with no signal at any phase has undefined visibility, returned as
JSON `null`. Blocking either arm removes interference. Blocking both arms
gives zero output and loss equal to input power.

## Meter statistics

`shots` is the number of repeated power-meter readings per port, **not photon
shots or photon counts**. At the selected phase each reading is

```text
meter j = predicted Pj + εj,    εj ~ Normal(0, meter_noise_mw²).
```

Noise is independent across ports and readings. NumPy's seeded default random
generator makes raw readings reproducible for the same request and NumPy
environment. Samples are retained without clipping: negative readings at a dark
port represent electronic noise, while predicted physical powers remain
nonnegative.

For each meter, metrics report the measured sample mean, sample standard
deviation `meter{j}_std_mw` with N−1 degrees of freedom, and sample standard
error `meter{j}_stderr_mw = s/√N`. The separate
`meter{j}_expected_stderr_mw = meter_noise_mw/√N` is the prediction from the
known calibrated noise. These quantify uncertainty of a mean under this
independent Gaussian model. They do not include systematic uncertainty or
uncertainty in the optical parameters.

## Request and result contract

`backend.photonics.PhotonicsRequest` extends the common strict model: unknown
fields and nonfinite numbers are rejected. Execution revalidates the request
before calculation, including mutable component inventories.

| Field | Default | Accepted range |
| --- | --- | --- |
| `power_mw` | 1 | >0 to 100 |
| `wavelength_nm` | 633 | 400 to 1600 |
| `phase_rad` | 0 | −4π to +4π |
| `path_difference_um` | 0 | −100 to +100 |
| `splitter1`, `splitter2` | .5 | 0 to 1 |
| `upper_transmission`, `lower_transmission` | 1 | 0 to 1 |
| `meter_noise_mw` | .01 | 0 to 1 |
| `shots` | 256 | 16 to 4096, integer |
| `seed` | 42 | 0 to 2³¹−1, integer |
| `points` | 181 | 51 to 721, integer |
| `bench_components` | all eight | `source`, `bs1`, `upper_mirror`, `lower_mirror`, `phase`, `bs2`, `detector0`, `detector1`, each once |

`run_photonics(config)` returns JSON-compatible values:

- Common metadata: `kind: "photonics"`, `backend`, `runtime_s`, `qubits: 0`,
  `seed`, `shots`, and `versions.numpy`.
- `series`: rows with `phase_rad`, `phase_pi`, `port0_mw`, `port1_mw`,
  `total_output_mw`.
- `metrics`: selected `port0_mw`, `port1_mw`, `total_output_mw`, `loss_mw`,
  `effective_phase_rad`, `power_balance_error_mw`; exact `visibility0`,
  `visibility1`; `port0_min_mw`, `port0_max_mw`, `port1_min_mw`,
  `port1_max_mw`; and both meters' `mean_mw`, `std_mw`, `stderr_mw`, and
  `expected_stderr_mw` fields prefixed with `meter0_` or `meter1_`.
- `output_fields`: two `[real, imaginary]` pairs in √mW, one per output port.
- `meter_readings`: raw numeric arrays `port0` and `port1`, each length `shots`.
- `model`, `assumptions`, `limitations`: explicit scientific scope.

## Scientific scope and validation

The model assumes narrowband light, a single spatial mode per path, matched
polarization, full mutual coherence, ideal lossless splitters, lumped arm
transmissions, and steady-state propagation. Large path differences are
treated as coherent regardless of the physical source's coherence length;
finite bandwidth and coherence loss would require a source spectrum or
coherence model, which this milestone does not include.

It does not perform ray tracing, FDTD, diffraction, alignment or spatial-overlap
calculations, polarization evolution, transient propagation, photon counting,
quantum shot-noise sampling, quantum-state simulation, or quantum tomography.
Detector saturation, drift, correlated noise, and systematic calibration errors
are also outside the current model. Optical power fringes alone make no claim
about single-photon quantum behavior.

`tests/test_photonics.py` checks independent analytic phase limits, complex
field signs, μm/nm conversion, asymmetric lossy fixtures, exact visibility,
blocked arms, extreme splitter settings, energy conservation across random
and boundary configurations, reproducible raw meter data, sample uncertainty,
negative electronic readings, and invalid or incomplete requests.
