"""Independent small density-matrix reference in q0-leftmost basis order.

After each unitary on axes S, the local depolarizing channel is
``(1-lambda)*rho + lambda*(I_S / 2**len(S)) tensor Tr_S(rho)``.
The tensor factors are placed back on their original qubits, so the other
qubits retain both their marginal state and their mutual correlations.
This is the Aer depolarizing-parameter convention documented at
https://qiskit.github.io/qiskit-aer/stubs/qiskit_aer.noise.depolarizing_error.html
but the implementation uses only NumPy and the independent local gate matrices.

Terminal measurement annotations are omitted from coherent evolution; readout
errors are independent symmetric classical bit flips of the final diagonal.
These references are bounded educational calculations, not calibrated devices.
"""

from collections.abc import Mapping, Sequence
import math
from numbers import Real

import numpy as np

from .statevector import compile_operations


_PHYSICAL_ATOL = 1e-10


def _noise_probability(value: object, label: str) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not 0 <= value <= 1
        or not math.isfinite(value)
    ):
        raise ValueError(f"{label} must be a finite real number from 0 through 1.")
    return float(value)


def _evolve_operation(
    rho: np.ndarray,
    qubits: int,
    axes: tuple[int, ...],
    unitary: np.ndarray,
    gate_error: float,
) -> np.ndarray:
    # Group the acted-on and spectator ket/bra axes separately. No full-system
    # unitary is constructed, and the bra contraction conjugates the unitary.
    order = axes + tuple(axis for axis in range(qubits) if axis not in axes)
    permutation = order + tuple(axis + qubits for axis in order)
    inverse = tuple(permutation.index(axis) for axis in range(2 * qubits))
    local_size = 1 << len(axes)
    rest_size = 1 << (qubits - len(axes))
    tensor_shape = (2,) * (2 * qubits)
    blocks = rho.reshape(tensor_shape).transpose(permutation).reshape(
        local_size, rest_size, local_size, rest_size
    )
    evolved = np.einsum("ai,irjs,bj->arbs", unitary, blocks, unitary.conj(), optimize=True)
    if gate_error:
        reduced_rest = np.einsum("iris->rs", evolved)
        replacement = np.einsum(
            "ij,rs->irjs", np.eye(local_size) / local_size, reduced_rest
        )
        evolved = (1 - gate_error) * evolved + gate_error * replacement
    return evolved.reshape(tensor_shape).transpose(inverse).reshape(rho.shape)


def _check_density(rho: np.ndarray) -> None:
    """Reject genuine physicality failures; never repair or normalize output."""
    if not np.isfinite(rho).all():
        raise ValueError("Reference density matrix contains nonfinite values.")
    if not np.allclose(rho, rho.conj().T, rtol=0, atol=_PHYSICAL_ATOL):
        raise ValueError("Reference density matrix is not Hermitian.")
    if abs(np.trace(rho) - 1) > _PHYSICAL_ATOL:
        raise ValueError("Reference density matrix does not have unit trace.")
    if np.linalg.eigvalsh(rho).min() < -_PHYSICAL_ATOL:
        raise ValueError("Reference density matrix is not positive semidefinite.")


def simulate_density(
    qubits: int,
    gates: Sequence[Mapping[str, object]],
    gate_error: float = 0.0,
) -> np.ndarray:
    """Evolve |0...0><0...0| with local depolarization for 1 through 6 qubits.

    All inputs are validated before state allocation. Up to 128 gate entries
    are accepted, with the gate schema and terminal-measurement convention of
    ``compile_operations``. Noise probabilities may range from zero to one.
    Physicality checks allow only floating-point roundoff (absolute 1e-10);
    no clipping, symmetrization, or trace renormalization is performed.
    """
    gate_error = _noise_probability(gate_error, "gate_error")
    operations = compile_operations(qubits, gates, max_qubits=6)
    qubits = int(qubits)
    dimension = 1 << qubits
    rho = np.zeros((dimension, dimension), dtype=np.complex128)
    rho[0, 0] = 1
    for axes, unitary in operations:
        rho = _evolve_operation(rho, qubits, axes, unitary, gate_error)
    _check_density(rho)
    return rho


def simulate_probabilities(
    qubits: int,
    gates: Sequence[Mapping[str, object]],
    gate_error: float = 0.0,
    readout_error: float = 0.0,
) -> np.ndarray:
    """Return exact final probabilities after independent flips on every bit.

    Index bit strings have q0 on the left. Readout is classical and does not
    modify the density matrix returned by ``simulate_density``. Noise bounds
    are validated before evolving or allocating the density matrix.
    """
    readout_error = _noise_probability(readout_error, "readout_error")
    rho = simulate_density(qubits, gates, gate_error=gate_error)
    probabilities = np.diag(rho).real.copy().reshape((2,) * int(qubits))
    for axis in range(int(qubits)):
        probabilities = (
            (1 - readout_error) * probabilities
            + readout_error * np.flip(probabilities, axis=axis)
        )
    probabilities = probabilities.reshape(-1)
    if (
        not np.isfinite(probabilities).all()
        or probabilities.min() < -_PHYSICAL_ATOL
        or probabilities.max() > 1 + _PHYSICAL_ATOL
        or abs(probabilities.sum() - 1) > _PHYSICAL_ATOL
    ):
        raise ValueError("Reference output probabilities are not physical.")
    return probabilities
