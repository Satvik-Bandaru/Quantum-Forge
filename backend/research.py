"""Bounded density-matrix research: ideal bit-flip QEC and one-photon MZI.

These are local CPU models with explicit state spaces, not hardware controls.
All probabilities/transmissions are dimensionless; phase angles are radians.
"""
import math
from time import perf_counter
from typing import Literal

import numpy as np
from pydantic import Field

from .models import StrictModel


class ResearchRequest(StrictModel):
    experiment: Literal['repetition_code', 'single_photon_mzi'] = 'repetition_code'
    shots: int = Field(default=1024, ge=128, le=8192)
    seed: int = Field(default=42, ge=0, le=2**31-1)
    bit_flip_probability: float = Field(default=.1, ge=0, le=1)
    theta_rad: float = Field(default=0, ge=0, le=math.pi)
    relative_phase_rad: float = Field(default=0, ge=-2*math.pi, le=2*math.pi)
    splitter1: float = Field(default=.5, ge=0, le=1)
    splitter2: float = Field(default=.5, ge=0, le=1)
    phase_rad: float = Field(default=0, ge=-4*math.pi, le=4*math.pi)
    upper_transmission: float = Field(default=1, ge=0, le=1)
    lower_transmission: float = Field(default=1, ge=0, le=1)
    detector0_efficiency: float = Field(default=1, ge=0, le=1)
    detector1_efficiency: float = Field(default=1, ge=0, le=1)
    path_coherence: float = Field(default=1, ge=0, le=1)


def _pack(matrix):
    return [[[float(value.real), float(value.imag)] for value in row] for row in matrix]


def _physical_checks(*states):
    tolerance = 1e-10
    trace_error = max(float(abs(np.trace(rho)-1)) for rho in states)
    hermiticity_error = max(float(np.max(np.abs(rho-rho.conj().T))) for rho in states)
    minimum_eigenvalue = min(float(np.linalg.eigvalsh((rho+rho.conj().T)/2).min()) for rho in states)
    finite = all(bool(np.isfinite(rho).all()) for rho in states)
    checks = {
        'finite': finite,
        'trace_preserved': trace_error <= tolerance,
        'hermitian': hermiticity_error <= tolerance,
        'positive_semidefinite': minimum_eigenvalue >= -tolerance,
        'tolerance': tolerance,
        'max_trace_error': trace_error,
        'max_hermiticity_error': hermiticity_error,
        'min_eigenvalue': minimum_eigenvalue,
    }
    checks['passed'] = all(checks[key] for key in ['finite', 'trace_preserved', 'hermitian', 'positive_semidefinite'])
    return checks


def _syndrome(index):
    q0, q1, q2 = (index >> 2) & 1, (index >> 1) & 1, index & 1
    return f'{q0 ^ q1}{q1 ^ q2}'


def _flip_density(rho, mask):
    indices = np.arange(8) ^ mask
    return rho[np.ix_(indices, indices)]


def _repetition(config):
    ket = np.array([math.cos(config.theta_rad/2),
                    np.exp(1j*config.relative_phase_rad)*math.sin(config.theta_rad/2)])
    initial = np.outer(ket, ket.conj())
    # CNOT(0,1), CNOT(0,2) acting on |psi> |00>, basis |q0 q1 q2>.
    encoded_ket = np.zeros(8, dtype=np.complex128)
    encoded_ket[0], encoded_ket[7] = ket
    encoded = np.outer(encoded_ket, encoded_ket.conj())
    p = config.bit_flip_probability
    pattern_probabilities = np.array([p**mask.bit_count() * (1-p)**(3-mask.bit_count()) for mask in range(8)])
    noisy = sum(weight*_flip_density(encoded, mask) for mask, weight in enumerate(pattern_probabilities))

    # Ideal projective measurement of Z0Z1 and Z1Z2. Outcomes 1 mean odd
    # parity (-1 eigenvalue), not a measurement of the encoded logical bit.
    corrections = {'00': 0, '10': 4, '11': 2, '01': 1}
    corrected = np.zeros((8, 8), dtype=np.complex128)
    syndrome_probabilities = {}
    for syndrome, mask in corrections.items():
        projector = np.diag([float(_syndrome(index) == syndrome) for index in range(8)])
        branch = projector @ noisy @ projector
        syndrome_probabilities[syndrome] = float(np.trace(branch).real)
        corrected += _flip_density(branch, mask)

    # Inverse encoding followed by the partial trace of the two work qubits.
    decode = np.array([index ^ (3 if index & 4 else 0) for index in range(8)])
    decoded = corrected[np.ix_(decode, decode)]
    logical = np.trace(decoded.reshape(2, 4, 2, 4), axis1=1, axis2=3)
    logical_error = float(sum(weight for mask, weight in enumerate(pattern_probabilities)
                              if (mask ^ corrections[_syndrome(mask)]) == 7))
    analytic_error = 3*p*p-2*p*p*p
    reference = (1-analytic_error)*initial + analytic_error*initial[::-1, ::-1]
    uncorrected = (1-p)*initial + p*initial[::-1, ::-1]
    fidelity = float(np.vdot(ket, logical @ ket).real)
    uncorrected_fidelity = float(np.vdot(ket, uncorrected @ ket).real)
    checks = _physical_checks(initial, encoded, noisy, corrected, logical)
    checks['logical_channel_matches_analytic'] = bool(np.max(np.abs(logical-reference)) < 1e-10)
    checks['syndrome_probability_conserved'] = abs(sum(syndrome_probabilities.values())-1) < 1e-10
    checks['passed'] = checks['passed'] and checks['logical_channel_matches_analytic'] and checks['syndrome_probability_conserved']

    rng = np.random.default_rng(config.seed)
    physical_errors = rng.binomial(1, p, size=(config.shots, 3))
    masks = physical_errors @ np.array([4, 2, 1])
    logical_errors = physical_errors.sum(axis=1) >= 2
    # Measurements belong to the same sampled error trial, so computational
    # basis inputs agree exactly with the logical branch counts.
    trial_p1 = np.where(logical_errors, abs(ket[0])**2, abs(ket[1])**2)
    measured = rng.random(config.shots) < trial_p1
    pattern_counts = {f'{mask:03b}': int(np.sum(masks == mask)) for mask in range(8)}
    syndrome_counts = {syndrome: sum(count for pattern, count in pattern_counts.items()
                                    if _syndrome(int(pattern, 2)) == syndrome) for syndrome in corrections}
    errors = int(logical_errors.sum())
    return {
        'backend': 'NumPy complex128 three-qubit Pauli channel, parity projections and ideal recovery / local CPU',
        'qubits': 3,
        'probabilities': {'logical_I': 1-logical_error, 'logical_X': logical_error},
        'counts': {'logical_I': config.shots-errors, 'logical_X': errors},
        'measurement_probabilities': {'0': float(logical[0, 0].real), '1': float(logical[1, 1].real)},
        'measurement_counts': {'0': config.shots-int(measured.sum()), '1': int(measured.sum())},
        'pattern_counts': pattern_counts,
        'syndrome_counts': syndrome_counts,
        'syndrome_probabilities': syndrome_probabilities,
        'trial_preview': [
            {'error_pattern': f'{int(mask):03b}', 'syndrome': _syndrome(int(mask)),
             'correction_qubit': {0: None, 4: 0, 2: 1, 1: 2}[corrections[_syndrome(int(mask))]],
             'logical_error': bool(logical_errors[index]), 'measurement': str(int(measured[index]))}
            for index, mask in enumerate(masks[:32])
        ],
        'initial_density_matrix': _pack(initial),
        'encoded_density_matrix': _pack(encoded),
        'corrected_density_matrix': _pack(corrected),
        'final_density_matrix': _pack(logical),
        'metrics': {
            'physical_error_probability': p,
            'logical_error_probability': logical_error,
            'analytic_logical_error_probability': analytic_error,
            'sampled_logical_error_probability': errors/config.shots,
            'corrected_fidelity': fidelity,
            'uncorrected_fidelity': uncorrected_fidelity,
            'fidelity_gain': fidelity-uncorrected_fidelity,
            'purity': float(np.trace(logical @ logical).real),
        },
        'series': [
            {'physical_error_probability': float(value),
             'logical_error_probability': float(3*value**2-2*value**3)}
            for value in np.linspace(0, 1, 101)
        ],
        'checks': checks,
        'model': {
            'name': 'Three-qubit repetition code under independent Pauli-X errors',
            'basis': ['|0>', '|1>'], 'physical_basis': '|q0 q1 q2>, q0 is most significant',
            'input': 'cos(theta/2)|0> + exp(i*relative_phase)*sin(theta/2)|1>',
            'encoding': 'alpha|0>+beta|1> -> alpha|000>+beta|111>',
            'noise': 'Independent (1-p)rho+p X rho X on each of three data qubits, once',
            'syndromes': 'Z0Z1, Z1Z2; 1 denotes odd parity / -1 eigenvalue',
            'recovery': '00:I, 10:X0, 11:X1, 01:X2, then inverse encoding and trace of work qubits',
            'logical_channel': '(1-pL)rho+pL X rho X; pL=3p^2-2p^3',
            'counts': 'Error-channel trajectories, logical_I or logical_X; these are not state-measurement frequencies',
            'measurement_counts': 'Final logical Z-basis measurements from the same error trials',
            'trial_preview': 'First min(shots,32) trials; all shots contribute to aggregate counts',
            'series': 'Exact analytic pL reference versus physical p; no extra shot experiments',
            'fidelity': 'Pure-state overlap <psi|rho_out|psi>, compared with one unencoded qubit under the same p',
            'units': {'angles': 'rad', 'probabilities': 'dimensionless'},
        },
        'limitations': [
            'Ideal encoding, parity measurement, correction and decoding; syndrome ancillas are eliminated by exact projectors, not counted as simulated data qubits.',
            'Protects against one X error only. Phase errors, Y errors, amplitude damping, correlated errors, leakage and imperfect gates/readout are absent.',
            'One correction round, three data qubits, no fault-tolerant circuit or repeated memory-cycle model.',
            'Two or three flips cause a logical X. For p>0.5 this fixed decoder increases logical error probability.',
            'Logical X probability is not generally state infidelity: an X eigenstate is unchanged by a logical X.',
            'Local CPU simulation and internal numerical checks do not establish performance on quantum hardware.',
        ],
    }


def _splitter(transmission):
    return np.array([[math.sqrt(transmission), 1j*math.sqrt(1-transmission)],
                     [1j*math.sqrt(1-transmission), math.sqrt(transmission)]])


def _optical_density(config, phase):
    first = _splitter(config.splitter1) @ np.array([1, 0])
    arms = np.diag([math.sqrt(config.upper_transmission)*np.exp(1j*phase),
                    math.sqrt(config.lower_transmission)]) @ first
    one_photon = np.outer(arms, arms.conj())
    # A phase-damping channel multiplies path coherence, preserving populations.
    one_photon[0, 1] *= config.path_coherence
    one_photon[1, 0] *= config.path_coherence
    second = _splitter(config.splitter2)
    one_photon = second @ one_photon @ second.conj().T
    survival = config.splitter1*config.upper_transmission + (1-config.splitter1)*config.lower_transmission
    full = np.zeros((3, 3), dtype=np.complex128)
    full[0, 0] = 1-survival
    full[1:, 1:] = one_photon
    return full


def _detection_probabilities(config, rho):
    detected = np.array([config.detector0_efficiency*rho[1, 1].real,
                         config.detector1_efficiency*rho[2, 2].real])
    # Only roundoff is bounded here; the unmodified state is checked separately.
    probabilities = np.clip([*detected, 1-detected.sum()], 0, 1)
    return probabilities/probabilities.sum()


def _single_photon(config):
    rho = _optical_density(config, config.phase_rad)
    probabilities = _detection_probabilities(config, rho)
    keys = ['detector0', 'detector1', 'no_click']
    counts = np.random.default_rng(config.seed).multinomial(config.shots, probabilities)
    survival = float(np.trace(rho[1:, 1:]).real)
    loss = float(rho[0, 0].real)
    missed = float((1-config.detector0_efficiency)*rho[1, 1].real
                   + (1-config.detector1_efficiency)*rho[2, 2].real)
    a = config.splitter1*config.splitter2*config.upper_transmission
    b = (1-config.splitter1)*(1-config.splitter2)*config.lower_transmission
    c = config.splitter1*(1-config.splitter2)*config.upper_transmission
    d = (1-config.splitter1)*config.splitter2*config.lower_transmission
    interference = 2*config.path_coherence*math.sqrt(a*b)*math.cos(config.phase_rad)
    analytic = np.array([a+b-interference, c+d+interference])
    checks = _physical_checks(rho)
    checks['optical_probability_conserved'] = abs(loss+survival-1) < 1e-10
    checks['detection_probability_conserved'] = bool(abs(sum(probabilities)-1) < 1e-10)
    checks['interference_matches_analytic'] = bool(np.max(np.abs(np.diag(rho)[1:].real-analytic)) < 1e-10)
    checks['passed'] = checks['passed'] and all(checks[key] for key in [
        'optical_probability_conserved', 'detection_probability_conserved', 'interference_matches_analytic'])
    metrics = {
        'detector0_probability': float(probabilities[0]),
        'detector1_probability': float(probabilities[1]),
        'no_click_probability': float(probabilities[2]),
        'optical_loss_probability': loss,
        'missed_detection_probability': missed,
        'survival_probability': survival,
        'double_click_probability': 0.0,
        'purity': float(np.trace(rho @ rho).real),
    }
    for port, first, second, efficiency in [(0, a, b, config.detector0_efficiency),
                                            (1, c, d, config.detector1_efficiency)]:
        metrics[f'visibility{port}'] = (2*config.path_coherence*math.sqrt(first*second)/(first+second)
                                       if first+second > 0 and efficiency > 0 else None)
    series = []
    for phase in np.linspace(0, 2*math.pi, 101):
        values = _detection_probabilities(config, _optical_density(config, phase))
        series.append({'phase_rad': float(phase), **{key+'_probability': float(value) for key, value in zip(keys, values)}})
    return {
        'backend': 'NumPy complex128 vacuum plus one-photon density matrix and exclusive photon sampling / local CPU',
        'qubits': 0,
        'probabilities': {key: float(value) for key, value in zip(keys, probabilities)},
        'counts': {key: int(value) for key, value in zip(keys, counts)},
        'mode_probabilities': {key: float(value) for key, value in zip(['vacuum', 'port0', 'port1'], np.diag(rho).real)},
        'final_density_matrix': _pack(rho),
        'metrics': metrics,
        'series': series,
        'checks': checks,
        'model': {
            'name': 'One-photon two-mode Mach-Zehnder interferometer with vacuum loss',
            'basis': ['|vacuum>', '|1,0>', '|0,1>'],
            'input': 'Exactly one photon in input mode 0 per trial: |1,0>',
            'splitter': 'B(T)=[[sqrt(T),i sqrt(1-T)],[i sqrt(1-T),sqrt(T)]]',
            'arms': 'A=diag(sqrt(upper_transmission)*exp(i*phase),sqrt(lower_transmission))',
            'evolution': 'B1 input; A attenuation; path dephasing; B2 recombination; lost population transferred to vacuum',
            'path_coherence': 'gamma multiplies the two arm off-diagonal density entries; gamma=1 coherent, gamma=0 fully path-dephased',
            'detection': 'P(Dj)=eta_j*rho[j+1,j+1]; P(no_click)=P(vacuum)+sum_j(1-eta_j)*rho[j+1,j+1]',
            'counts': 'One multinomial experiment of shots independent prepared single photons; exactly one of D0, D1, no_click per trial',
            'density_stage': 'Optical output before detector absorption; missed detections do not alter this reported state',
            'series': 'Exact detector probabilities versus phase at fixed remaining settings; no additional sampled shots',
            'units': {'phase': 'rad', 'transmissions': 'photon survival probabilities', 'probabilities': 'dimensionless'},
        },
        'limitations': [
            'Exactly one incident photon per trial; no source vacuum component, multiphoton contamination, dark counts or double clicks.',
            'Two ideal spatial modes with fixed polarization and frequency; no diffraction, alignment, bandwidth or timing model.',
            'Loss is passive to an unobserved vacuum environment; detector efficiency is independent and has no saturation, dead time or afterpulsing.',
            'path_coherence is a specified phase-damping channel, not a calibrated model of a laboratory decoherence source.',
            'The phase fringes also occur in classical coherent optics; the modeled single-photon occupancy and mutually exclusive trials distinguish these counts from optical power readings.',
            'No two-photon Hong-Ou-Mandel interference, entanglement source or arbitrary optical network is simulated.',
            'Simulation and internal consistency checks are not evidence of measured hardware nonclassicality.',
        ],
    }


def run_research(config: ResearchRequest) -> dict:
    started = perf_counter()
    config = ResearchRequest.model_validate(config.model_dump())
    result = _repetition(config) if config.experiment == 'repetition_code' else _single_photon(config)
    if not result['checks']['passed']:
        raise RuntimeError('Research model numerical checks failed; no result was accepted.')
    return {'kind': 'research', 'experiment': config.experiment,
            'shots': config.shots, 'seed': config.seed, 'versions': {'numpy': np.__version__},
            **result, 'runtime_s': perf_counter()-started}
