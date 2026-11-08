"""One driven two-level system in a rotating frame, with Lindblad decoherence.

All times are microseconds and all user frequencies are cycles/microsecond
(MHz). Constant square-pulse dynamics use a complex128 matrix exponential;
no numerical integration step or phenomenological damping envelope is used.
"""
import math
import time
from typing import Literal

import numpy as np
import scipy
from pydantic import Field, model_validator
from scipy.linalg import expm

from .models import StrictModel


class PhysicsRequest(StrictModel):
    drive_mhz: float = Field(default=1, ge=0, le=20)
    detuning_mhz: float = Field(default=0, ge=-20, le=20)
    duration_us: float = Field(default=3, ge=0.001, le=50)
    pulse_phase_rad: float = Field(default=0, ge=-2 * math.pi, le=2 * math.pi)
    t1_us: float | None = Field(default=8, ge=0.05, le=10000)
    tphi_us: float | None = Field(default=5, ge=0.05, le=10000)
    initial_state: Literal['ground', 'excited', 'plus'] = 'ground'
    points: int = Field(default=301, ge=51, le=1001)
    shots: int = Field(default=1024, ge=128, le=8192)
    seed: int = Field(default=42, ge=0, le=2**31 - 1)

    @model_validator(mode='after')
    def resolved_time_grid(self):
        cycles = math.hypot(self.drive_mhz, self.detuning_mhz) * self.duration_us
        required = math.ceil(12 * cycles - 1e-12) + 1
        if self.points < required:
            raise ValueError(
                f'Time grid needs at least {required} points for 12 samples per '
                'generalized Rabi cycle; increase points or reduce drive, detuning, or duration.'
            )
        return self


def _liouvillian(hamiltonian, collapse_operators):
    """Matrix representation of -i[H/hbar, rho] + sum D[C](rho).

    Constructing each column by acting on a matrix unit makes column-major
    vectorization explicit, including all conjugations of collapse operators.
    """
    generator = np.empty((4, 4), dtype=np.complex128)
    basis = np.eye(4, dtype=np.complex128)
    for column in range(4):
        rho = basis[:, column].reshape((2, 2), order='F')
        derivative = -1j * (hamiltonian @ rho - rho @ hamiltonian)
        for operator in collapse_operators:
            product = operator.conj().T @ operator
            derivative += operator @ rho @ operator.conj().T - (product @ rho + rho @ product) / 2
        generator[:, column] = derivative.reshape(4, order='F')
    return generator


def run_physics(config: PhysicsRequest):
    """Return ideal, noisy and repeated-experiment shot traces for one pulse."""
    started = time.perf_counter()
    sigma_x = np.array([[0, 1], [1, 0]], dtype=np.complex128)
    sigma_y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
    sigma_z = np.diag([1, -1]).astype(np.complex128)
    transverse = math.cos(config.pulse_phase_rad) * sigma_x + math.sin(config.pulse_phase_rad) * sigma_y
    # H/hbar is in radians/us; user Omega and Delta are cycles/us.
    hamiltonian = math.pi * (config.detuning_mhz * sigma_z + config.drive_mhz * transverse)
    ket = {
        'ground': np.array([1, 0], dtype=np.complex128),
        'excited': np.array([0, 1], dtype=np.complex128),
        'plus': np.array([1, 1], dtype=np.complex128) / math.sqrt(2),
    }[config.initial_state]
    initial_density = np.outer(ket, ket.conj())
    collapse_operators = []
    if config.t1_us is not None:
        collapse_operators.append(np.array([[0, 1], [0, 0]], dtype=np.complex128) / math.sqrt(config.t1_us))
    if config.tphi_us is not None:
        collapse_operators.append(sigma_z / math.sqrt(2 * config.tphi_us))
    generator = _liouvillian(hamiltonian, collapse_operators)
    times = np.linspace(0, config.duration_us, config.points)
    initial_vector = initial_density.reshape(4, order='F')
    # Each time is evaluated from the same initial condition. No accumulation
    # of integration-step error and no intermediate projective measurement.
    density = np.array([
        (expm(generator * t) @ initial_vector).reshape((2, 2), order='F')
        for t in times
    ])
    ideal_states = np.array([expm(-1j * hamiltonian * t) @ ket for t in times])

    trace_error = float(np.max(np.abs(np.trace(density, axis1=1, axis2=2) - 1)))
    hermiticity_error = float(np.max(np.abs(density - density.conj().transpose(0, 2, 1))))
    # eigvalsh is applied to the Hermitian part for a roundoff-stable diagnostic;
    # no eigenvalue projection or renormalization changes the simulated state.
    eigenvalues = np.linalg.eigvalsh((density + density.conj().transpose(0, 2, 1)) / 2)
    minimum_eigenvalue = float(np.min(eigenvalues))
    finite = bool(np.isfinite(density).all() and np.isfinite(ideal_states).all())
    tolerance = 1e-9
    checks = {
        'passed': finite and trace_error <= tolerance and hermiticity_error <= tolerance and minimum_eigenvalue >= -tolerance,
        'finite': finite,
        'trace_preserved': trace_error <= tolerance,
        'hermitian': hermiticity_error <= tolerance,
        'positive_semidefinite': minimum_eigenvalue >= -tolerance,
        'tolerance': tolerance,
    }
    if not checks['passed']:
        raise RuntimeError('Density-matrix numerical checks failed; no physics result was saved.')

    # Bound tiny floating-point excursions for probabilities and binomial input;
    # diagnostics above retain the unmodified density matrices.
    noisy_p1 = np.clip(density[:, 1, 1].real, 0, 1)
    ideal_p1 = np.clip(np.abs(ideal_states[:, 1]) ** 2, 0, 1)
    rng = np.random.default_rng(config.seed)
    counts = rng.binomial(config.shots, noisy_p1)
    stderr = np.sqrt(noisy_p1 * (1 - noisy_p1) / config.shots)
    series = [
        {
            'time_us': float(t),
            'drive_mhz': float(config.drive_mhz),
            'ideal_p1': float(ideal_p1[index]),
            'noisy_p1': float(noisy_p1[index]),
            'sampled_p1': int(counts[index]) / config.shots,
            'stderr': float(stderr[index]),
            'bloch_x': float(2 * density[index, 0, 1].real),
            'bloch_y': float(-2 * density[index, 0, 1].imag),
            'bloch_z': float((density[index, 0, 0] - density[index, 1, 1]).real),
        }
        for index, t in enumerate(times)
    ]
    final_density = density[-1]
    final_ideal = ideal_states[-1]
    coherence_rate = (0 if config.t1_us is None else 1 / (2 * config.t1_us)) + (0 if config.tphi_us is None else 1 / config.tphi_us)
    frequency = math.hypot(config.drive_mhz, config.detuning_mhz)
    fidelity = float(np.vdot(final_ideal, final_density @ final_ideal).real)
    return {
        'kind': 'physics',
        'backend': 'SciPy complex128 constant-Liouvillian matrix exponential / local CPU',
        'runtime_s': time.perf_counter() - started,
        'qubits': 1,
        'seed': config.seed,
        'shots': config.shots,
        'versions': {'numpy': np.__version__, 'scipy': scipy.__version__},
        'series': series,
        'final_density_matrix': [[[float(entry.real), float(entry.imag)] for entry in row] for row in final_density],
        'metrics': {
            'final_ideal_p1': float(ideal_p1[-1]),
            'final_noisy_p1': float(noisy_p1[-1]),
            'purity': float(np.trace(final_density @ final_density).real),
            'fidelity_to_ideal': float(np.clip(fidelity, 0, 1)),
            't2_us': 1 / coherence_rate if coherence_rate else None,
            'rabi_frequency_mhz': frequency,
            'max_trace_error': trace_error,
            'max_hermiticity_error': hermiticity_error,
            'min_eigenvalue': minimum_eigenvalue,
            'time_step_us': float(times[1] - times[0]),
            'samples_per_rabi_cycle': (config.points - 1) / (frequency * config.duration_us) if frequency else None,
            'measurement_experiments': config.points,
            'total_shots': config.points * config.shots,
        },
        'checks': checks,
        'model': {
            'name': 'Driven two-level Lindblad model',
            'basis': ['|0> ground', '|1> excited'],
            'frame': 'Rotating frame with constant effective square pulse (rotating-wave model)',
            'units': {'time': 'us', 'frequency': 'MHz = cycles/us', 'phase': 'rad'},
            'hamiltonian': 'H/hbar = pi * [Delta*Z + Omega*(cos(phi)*X + sin(phi)*Y)]',
            'sigma_z': 'diag(1, -1)',
            'detuning_convention': 'Delta is the signed coefficient of +Z in the rotating-frame Hamiltonian; no laboratory carrier frequency is modeled.',
            'relaxation_operator': 'sqrt(1/T1) * |0><1|',
            'dephasing_operator': 'sqrt(1/(2*Tphi)) * Z',
            'coherence_relation': '1/T2 = 1/(2*T1) + 1/Tphi; null times disable that channel',
            'ideal_reference': 'Same initial state and Hamiltonian, with both decoherence channels disabled',
            'solver': 'rho(t) = expm(L*t) rho(0); ideal psi(t) = expm(-i*H*t/hbar) psi(0)',
            'measurement': 'Independent binomial(shots, noisy_p1) experiment at every time; no intermediate state collapse',
            'stderr': 'Theoretical binomial standard error sqrt(p*(1-p)/shots) using noisy_p1, not a confidence interval',
            'fidelity': 'Squared Uhlmann fidelity to the pure ideal final state: <psi_ideal|rho_noisy|psi_ideal>',
        },
        'limitations': [
            'This is a local CPU simulation of one abstract two-level system, not quantum hardware or a calibrated device.',
            'The constant rotating-frame square-pulse model omits counter-rotating terms, pulse distortion, leakage, crosstalk, and multilevel dynamics.',
            'Decoherence is time-independent, Markovian, zero-temperature relaxation plus pure dephasing; there is no thermal excitation or non-Markovian bath.',
            'Each displayed time point represents independent repeated preparation, evolution, and final measurement. Samples are not a continuous measurement record.',
            'Sampling adds finite-shot projective measurement noise only; it does not change the density-matrix evolution or add readout error.',
            'The trace has at least 12 samples per generalized Rabi cycle; very fast relaxation can occur between displayed points.',
            'Density invariants check numerical consistency of the specified model; they do not validate a real device or establish quantum advantage.',
        ],
    }
