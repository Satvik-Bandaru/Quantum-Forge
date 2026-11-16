"""Small independent statevector reference with q0 as the leftmost bit.

This module does not call production circuit builders or simulator libraries.
Gate matrices act on at most three axes; no full-circuit operator is built.
Terminal measurement annotations are ignored so the returned state remains the
coherent, premeasurement state. Mid-circuit measurement is not supported.
"""

from collections.abc import Mapping, Sequence
import math
from numbers import Integral, Real

import numpy as np


_GATE_NAMES = frozenset({
    "X", "Y", "Z", "H", "S", "SDG", "T", "TDG", "P", "RX", "RY", "RZ",
    "CNOT", "CZ", "CP", "SWAP", "CCX", "M",
})
_CONTROLLED = frozenset({"CNOT", "CZ", "CP", "SWAP", "CCX"})
_FIELDS = frozenset({"name", "target", "control", "control2", "angle"})


def _axis(value: object, qubits: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral) or not 0 <= value < qubits:
        raise ValueError(f"{label} must be an integer qubit index in [0, {qubits}).")
    return int(value)


def _validated_gates(
    qubits: int, gates: Sequence[Mapping[str, object]], max_qubits: int
) -> list[tuple[str, tuple[int, ...], float]]:
    """Validate the whole input before any NumPy allocation or matrix work."""
    if isinstance(max_qubits, bool) or not isinstance(max_qubits, Integral) or not 1 <= max_qubits <= 8:
        raise ValueError("max_qubits must be an integer from 1 through 8.")
    if isinstance(qubits, bool) or not isinstance(qubits, Integral) or not 1 <= qubits <= max_qubits:
        raise ValueError(f"qubits must be an integer from 1 through {max_qubits}.")
    if isinstance(gates, (str, bytes)) or not isinstance(gates, Sequence):
        raise ValueError("gates must be a sequence of gate mappings.")
    if len(gates) > 128:
        raise ValueError("A reference circuit may contain at most 128 gates.")

    validated = []
    measured = False
    for gate in gates:
        if not isinstance(gate, Mapping):
            raise ValueError("Each gate must be a mapping.")
        if set(gate) - _FIELDS:
            raise ValueError("Gate contains unexpected fields.")
        name = gate.get("name")
        if not isinstance(name, str) or name not in _GATE_NAMES:
            raise ValueError("Unknown gate name.")
        target = _axis(gate.get("target"), qubits, "target")
        control = gate.get("control")
        control2 = gate.get("control2")
        axes = (target,)
        if name in _CONTROLLED:
            control = _axis(control, qubits, "control")
            if control == target:
                raise ValueError("Control and target must be distinct.")
            axes = (control, target)
        elif control is not None:
            raise ValueError("Only controlled gates and SWAP accept a control.")
        if name == "CCX":
            control2 = _axis(control2, qubits, "control2")
            if control2 in axes:
                raise ValueError("CCX requires three distinct qubits.")
            axes = (control, control2, target)
        elif control2 is not None:
            raise ValueError("Only CCX accepts control2.")

        angle = gate.get("angle", math.pi / 2)
        if (
            isinstance(angle, bool)
            or not isinstance(angle, Real)
            or not -100 * math.pi <= angle <= 100 * math.pi
            or not math.isfinite(angle)
        ):
            raise ValueError("angle must be finite real radians within [-100*pi, 100*pi].")
        if measured and name != "M":
            raise ValueError("Measurements must be terminal.")
        if name == "M":
            measured = True
        else:
            validated.append((name, axes, float(angle)))
    return validated


def _local_unitary(name: str, angle: float) -> np.ndarray:
    """Literal local matrices in the ordered computational basis."""
    root_half = math.sqrt(0.5)
    fixed = {
        "X": [[0, 1], [1, 0]],
        "Y": [[0, -1j], [1j, 0]],
        "Z": [[1, 0], [0, -1]],
        "H": [[root_half, root_half], [root_half, -root_half]],
        "S": [[1, 0], [0, 1j]],
        "SDG": [[1, 0], [0, -1j]],
        "T": [[1, 0], [0, complex(root_half, root_half)]],
        "TDG": [[1, 0], [0, complex(root_half, -root_half)]],
        "CNOT": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        "CZ": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]],
        "SWAP": [[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]],
        "CCX": [
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 1, 0],
        ],
    }
    if name in fixed:
        return np.array(fixed[name], dtype=np.complex128)

    phase = complex(math.cos(angle), math.sin(angle))
    cosine, sine = math.cos(angle / 2), math.sin(angle / 2)
    if name == "P":
        matrix = [[1, 0], [0, phase]]
    elif name == "RX":
        matrix = [[cosine, -1j * sine], [-1j * sine, cosine]]
    elif name == "RY":
        matrix = [[cosine, -sine], [sine, cosine]]
    elif name == "RZ":
        matrix = [[complex(cosine, -sine), 0], [0, complex(cosine, sine)]]
    elif name == "CP":
        matrix = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, phase]]
    else:
        raise ValueError("Unknown unitary gate.")
    return np.array(matrix, dtype=np.complex128)


def compile_operations(
    qubits: int,
    gates: Sequence[Mapping[str, object]],
    *,
    max_qubits: int = 8,
) -> list[tuple[tuple[int, ...], np.ndarray]]:
    """Return validated local operations; controls precede the target axis.

    SWAP uses ``(control, target)`` and CCX uses ``(control, control2, target)``.
    At most 128 gate entries and 8 qubits are accepted. A caller may lower the
    qubit cap, as the density reference does. Invalid inputs raise ValueError.
    All gates are validated before any matrix is allocated. Input mappings are
    never modified, and the returned matrices are newly allocated each call.
    """
    validated = _validated_gates(qubits, gates, max_qubits)
    return [(axes, _local_unitary(name, angle)) for name, axes, angle in validated]


def simulate_statevector(qubits: int, gates: Sequence[Mapping[str, object]]) -> np.ndarray:
    """Evolve |0...0> and return complex amplitudes in q0-leftmost order."""
    operations = compile_operations(qubits, gates)
    qubits = int(qubits)
    state = np.zeros(1 << qubits, dtype=np.complex128)
    state[0] = 1
    shape = (2,) * qubits
    for axes, unitary in operations:
        # Move the gate axes first, treating all other qubits as batch columns.
        permutation = axes + tuple(axis for axis in range(qubits) if axis not in axes)
        inverse = tuple(permutation.index(axis) for axis in range(qubits))
        columns = state.reshape(shape).transpose(permutation).reshape(1 << len(axes), -1)
        evolved = unitary @ columns
        state = evolved.reshape(shape).transpose(inverse).reshape(-1)
    return state
