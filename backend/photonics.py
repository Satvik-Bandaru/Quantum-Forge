"""Classical, coherent two-mode Mach–Zehnder transfer-matrix model.

Fields have units sqrt(mW). ``shots`` counts repeated power-meter readings;
there is no photon sampling or quantum-state simulation in this module.
"""

import math
from time import perf_counter
from typing import Literal

import numpy as np
from pydantic import Field, model_validator

from .models import StrictModel


BenchComponent = Literal[
    'source', 'bs1', 'upper_mirror', 'lower_mirror', 'phase', 'bs2', 'detector0', 'detector1',
]
BENCH_COMPONENTS: tuple[BenchComponent, ...] = (
    'source', 'bs1', 'upper_mirror', 'lower_mirror', 'phase', 'bs2', 'detector0', 'detector1',
)


class PhotonicsRequest(StrictModel):
    power_mw: float = Field(default=1, gt=0, le=100)
    wavelength_nm: float = Field(default=633, ge=400, le=1600)
    phase_rad: float = Field(default=0, ge=-4 * math.pi, le=4 * math.pi)
    path_difference_um: float = Field(default=0, ge=-100, le=100)
    splitter1: float = Field(default=.5, ge=0, le=1)
    splitter2: float = Field(default=.5, ge=0, le=1)
    upper_transmission: float = Field(default=1, ge=0, le=1)
    lower_transmission: float = Field(default=1, ge=0, le=1)
    meter_noise_mw: float = Field(default=.01, ge=0, le=1)
    shots: int = Field(default=256, ge=16, le=4096)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)
    points: int = Field(default=181, ge=51, le=721)
    bench_components: list[BenchComponent] = Field(default_factory=lambda: list(BENCH_COMPONENTS), max_length=8)

    @model_validator(mode='after')
    def complete_bench(self):
        if len(set(self.bench_components)) != len(self.bench_components):
            raise ValueError('Each optical bench component must be placed exactly once; duplicates are not allowed.')
        missing = set(BENCH_COMPONENTS) - set(self.bench_components)
        if missing:
            raise ValueError('Complete the optical bench before running. Missing: ' + ', '.join(sorted(missing)) + '.')
        return self


def run_photonics(config: PhotonicsRequest) -> dict:
    """Return deterministic optical powers and seeded, noisy meter readings.

    Sweep rows vary the phase-shifter setting from 0 through 2π at the fixed
    wavelength/path difference. Metrics and meter samples use ``phase_rad``.
    """
    started = perf_counter()
    # Revalidate mutable lists and model_copy updates before numerical work.
    config = PhotonicsRequest.model_validate(config.model_dump())
    power = config.power_mw
    t1, t2 = config.splitter1, config.splitter2
    upper, lower = config.upper_transmission, config.lower_transmission
    path_phase = 2 * math.pi * config.path_difference_um * 1000 / config.wavelength_nm
    effective_phase = config.phase_rad + path_phase
    sweep = np.linspace(0, 2 * math.pi, config.points)
    phases = np.concatenate(([effective_phase], sweep + path_phase))

    # B(T) = [[sqrt(T), i sqrt(1-T)], [i sqrt(1-T), sqrt(T)]].
    # Expanding B2 D B1 [sqrt(P), 0] keeps the same complex-field convention.
    a = math.sqrt(t1) * math.sqrt(t2) * math.sqrt(upper)
    b = math.sqrt(1 - t1) * math.sqrt(1 - t2) * math.sqrt(lower)
    c = math.sqrt(t1) * math.sqrt(1 - t2) * math.sqrt(upper)
    d = math.sqrt(1 - t1) * math.sqrt(t2) * math.sqrt(lower)
    phasor = np.exp(1j * phases)
    fields = math.sqrt(power) * np.column_stack((a * phasor - b, 1j * (c * phasor + d)))
    powers = np.abs(fields) ** 2
    selected_powers = powers[0]
    output_power = float(selected_powers.sum())
    transmitted_fraction = t1 * upper + (1 - t1) * lower
    loss = power * (1 - transmitted_fraction)

    metrics = {
        'port0_mw': float(selected_powers[0]),
        'port1_mw': float(selected_powers[1]),
        'total_output_mw': output_power,
        'loss_mw': loss,
        'effective_phase_rad': effective_phase,
        'power_balance_error_mw': power - loss - output_power,
    }
    for port, first, second in [(0, a, b), (1, c, d)]:
        # Exact extrema do not depend on whether the display grid hits a peak.
        mean_fraction = first * first + second * second
        metrics[f'port{port}_min_mw'] = power * (first - second) ** 2
        metrics[f'port{port}_max_mw'] = power * (first + second) ** 2
        metrics[f'visibility{port}'] = 2 * first * second / mean_fraction if mean_fraction else None

    rng = np.random.default_rng(config.seed)
    # Independent electronic noise at each meter. Negative readings are kept.
    meter_samples = rng.normal(loc=selected_powers, scale=config.meter_noise_mw, size=(config.shots, 2))
    for port in (0, 1):
        samples = meter_samples[:, port]
        sample_std = float(np.std(samples, ddof=1)) if np.ptp(samples) else 0.0
        metrics[f'meter{port}_mean_mw'] = float(np.mean(samples))
        metrics[f'meter{port}_std_mw'] = sample_std
        metrics[f'meter{port}_stderr_mw'] = sample_std / math.sqrt(config.shots)
        metrics[f'meter{port}_expected_stderr_mw'] = config.meter_noise_mw / math.sqrt(config.shots)

    series = [
        {
            'phase_rad': float(phase),
            'phase_pi': float(phase / math.pi),
            'port0_mw': float(values[0]),
            'port1_mw': float(values[1]),
            'total_output_mw': float(values.sum()),
        }
        for phase, values in zip(sweep, powers[1:])
    ]
    return {
        'kind': 'photonics',
        'backend': 'NumPy classical coherent-field transfer matrices',
        'runtime_s': perf_counter() - started,
        'qubits': 0,
        'seed': config.seed,
        'shots': config.shots,
        'versions': {'numpy': np.__version__},
        'series': series,
        'metrics': metrics,
        'output_fields': [[float(value.real), float(value.imag)] for value in fields[0]],
        'meter_readings': {'port0': meter_samples[:, 0].tolist(), 'port1': meter_samples[:, 1].tolist()},
        'model': 'Classical two-mode Mach–Zehnder interferometer: Eout = B2 D B1 [sqrt(P), 0].',
        'assumptions': [
            'Narrowband, single-spatial-mode, same-polarization coherent light in a steady state.',
            'Beam splitters are lossless with reflection amplitude +i sqrt(1-T).',
            'Arm transmissions are power fractions; their square roots attenuate the fields.',
            'Mirrors redirect the two ideal modes; fixed relative mirror phases are included in phase_rad.',
            'Path difference is an optical path difference: phase = 2π × path_difference_um × 1000 / wavelength_nm.',
            'shots counts power-meter readings, with independent calibrated Gaussian electronic noise per meter.',
            'meter*_stderr_mw uses sample standard deviation / sqrt(shots); expected_stderr uses calibrated noise.',
        ],
        'limitations': [
            'No ray tracing, diffraction, FDTD, spatial alignment, polarization dynamics, or finite coherence-length model.',
            'No photon counting, shot noise, quantum state, quantum density matrix, or entanglement simulation.',
            'No detector saturation, drift, correlated noise, or time-dependent optical dynamics.',
            'Negative noisy meter readings represent electronic noise; predicted physical powers remain nonnegative.',
            'Visibility is computed from exact noiseless extrema; zero-signal visibility is undefined (null).',
        ],
    }
