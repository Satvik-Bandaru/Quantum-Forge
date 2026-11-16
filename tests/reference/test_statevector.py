"""Analytic component checks, independent of production simulators."""

import copy
import math

import numpy as np
import pytest


pytestmark = pytest.mark.reference


def simulate(qubits, gates):
    # Import in the test body so the initial missing implementation is a failure.
    from backend.reference.statevector import simulate_statevector

    return simulate_statevector(qubits, gates)


def basis_gates(bits):
    return [{"name": "X", "target": index} for index, bit in enumerate(bits) if bit == "1"]


ROOT_HALF = math.sqrt(0.5)
ROOT_THREE_HALF = math.sqrt(3) / 2


# Each pair is the literal action on |0> and |1>, including global phase.
@pytest.mark.parametrize(
    ("name", "angle", "zero", "one"),
    [
        ("X", None, [0, 1], [1, 0]),
        ("Y", None, [0, 1j], [-1j, 0]),
        ("Z", None, [1, 0], [0, -1]),
        ("H", None, [ROOT_HALF, ROOT_HALF], [ROOT_HALF, -ROOT_HALF]),
        ("S", None, [1, 0], [0, 1j]),
        ("SDG", None, [1, 0], [0, -1j]),
        ("T", None, [1, 0], [0, complex(ROOT_HALF, ROOT_HALF)]),
        ("TDG", None, [1, 0], [0, complex(ROOT_HALF, -ROOT_HALF)]),
        ("P", math.pi / 3, [1, 0], [0, complex(0.5, ROOT_THREE_HALF)]),
        ("RX", math.pi / 3, [ROOT_THREE_HALF, -0.5j], [-0.5j, ROOT_THREE_HALF]),
        ("RY", math.pi / 3, [ROOT_THREE_HALF, 0.5], [-0.5, ROOT_THREE_HALF]),
        ("RZ", math.pi / 3, [complex(ROOT_THREE_HALF, -0.5), 0], [0, complex(ROOT_THREE_HALF, 0.5)]),
    ],
)
@pytest.mark.parametrize("initial", [0, 1])
def test_single_qubit_basis_columns(name, angle, zero, one, initial):
    gate = {"name": name, "target": 0}
    if angle is not None:
        gate["angle"] = angle
    actual = simulate(1, basis_gates(str(initial)) + [gate])
    np.testing.assert_allclose(actual, (zero, one)[initial], rtol=0, atol=1e-15)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("P", [ROOT_HALF, 1j * ROOT_HALF]),
        ("RX", [complex(0.5, -0.5), complex(0.5, -0.5)]),
        ("RY", [0, 1]),
        ("RZ", [complex(0.5, -0.5), complex(0.5, 0.5)]),
    ],
)
def test_rotation_default_angle_is_pi_over_two(name, expected):
    actual = simulate(1, [{"name": "H", "target": 0}, {"name": name, "target": 0}])
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-15)


@pytest.mark.parametrize(
    ("name", "destinations", "phases"),
    [
        ("CNOT", [0, 5, 2, 7, 4, 1, 6, 3], [1] * 8),
        ("CZ", list(range(8)), [1, 1, 1, 1, 1, -1, 1, -1]),
        ("CP", list(range(8)), [1, 1, 1, 1, 1, 1j, 1, 1j]),
        ("SWAP", [0, 4, 2, 6, 1, 5, 3, 7], [1] * 8),
    ],
)
@pytest.mark.parametrize("initial", range(8))
def test_two_qubit_truth_table_with_reversed_nonadjacent_axes(name, destinations, phases, initial):
    gates = basis_gates(f"{initial:03b}") + [{"name": name, "control": 2, "target": 0}]
    expected = np.zeros(8, dtype=complex)
    expected[destinations[initial]] = phases[initial]
    np.testing.assert_allclose(simulate(3, gates), expected, rtol=0, atol=1e-15)


@pytest.mark.parametrize("initial", range(8))
def test_ccx_truth_table_controls_precede_target(initial):
    # q2 and q0 control q1; only |101> and |111> exchange.
    gates = basis_gates(f"{initial:03b}") + [
        {"name": "CCX", "control": 2, "control2": 0, "target": 1}
    ]
    expected = np.zeros(8, dtype=complex)
    expected[[0, 1, 2, 3, 4, 7, 6, 5][initial]] = 1
    np.testing.assert_allclose(simulate(3, gates), expected, rtol=0, atol=1e-15)


def test_complex_entanglement_uses_q0_leftmost():
    actual = simulate(3, [
        {"name": "H", "target": 0},
        {"name": "S", "target": 0},
        {"name": "CNOT", "control": 0, "target": 2},
        {"name": "X", "target": 1},
    ])
    np.testing.assert_allclose(actual, [0, 0, ROOT_HALF, 0, 0, 0, 0, 1j * ROOT_HALF], rtol=0, atol=1e-15)


def test_eight_qubits_and_128_gates_are_supported():
    gates = [{"name": "X", "target": 0}] * 127 + [{"name": "X", "target": 7}]
    actual = simulate(8, gates)
    expected = np.zeros(256, dtype=complex)
    expected[129] = 1
    assert actual.dtype == np.complex128
    np.testing.assert_array_equal(actual, expected)


def test_empty_circuit_starts_in_zero_state():
    np.testing.assert_array_equal(simulate(2, ()), [1, 0, 0, 0])


def test_terminal_measurements_leave_coherent_amplitudes():
    gates = [{"name": "H", "target": 0}, {"name": "M", "target": 0}, {"name": "M", "target": 1}]
    np.testing.assert_allclose(simulate(2, gates), [ROOT_HALF, 0, ROOT_HALF, 0], rtol=0, atol=1e-15)


def test_input_and_compiled_operations_are_not_shared_or_mutated():
    from backend.reference.statevector import compile_operations

    gates = [{"name": "Y", "target": 0, "control": None, "control2": None, "angle": math.pi / 2}]
    original = copy.deepcopy(gates)
    compiled = compile_operations(1, gates)
    compiled[0][1][:] = 0
    np.testing.assert_array_equal(simulate(1, gates), [0, 1j])
    assert gates == original


def test_compile_operations_preserves_order_and_local_axis_convention():
    from backend.reference.statevector import compile_operations

    operations = compile_operations(4, [
        {"name": "S", "target": 1},
        {"name": "SWAP", "control": 3, "target": 0},
        {"name": "CCX", "control": 2, "control2": 0, "target": 3},
        {"name": "M", "target": 0},
    ], max_qubits=6)
    assert [axes for axes, _ in operations] == [(1,), (3, 0), (2, 0, 3)]
    assert [matrix.shape for _, matrix in operations] == [(2, 2), (4, 4), (8, 8)]
    np.testing.assert_array_equal(operations[0][1], [[1, 0], [0, 1j]])


@pytest.mark.parametrize("qubits", [0, -1, 9, 1000000, 1.5, True, "2", None])
def test_invalid_qubit_counts_are_rejected(qubits):
    with pytest.raises(ValueError):
        simulate(qubits, [])


@pytest.mark.parametrize("gates", [None, {}, "X", 1, [{"name": "X", "target": 0}] * 129])
def test_invalid_gate_sequence_or_gate_cap_is_rejected(gates):
    with pytest.raises(ValueError):
        simulate(1, gates)


@pytest.mark.parametrize(
    "gate",
    [
        None, "X", {}, {"name": "X"}, {"target": 0},
        {"name": "UNKNOWN", "target": 0}, {"name": ["X"], "target": 0},
        {"name": "X", "target": -1}, {"name": "X", "target": 3},
        {"name": "X", "target": 0.0}, {"name": "X", "target": True},
        {"name": "X", "target": "0"}, {"name": "X", "target": None},
        {"name": "X", "target": 0, "extra": 1},
        {"name": "X", "target": 0, "control": 1},
        {"name": "X", "target": 0, "control2": 1},
        {"name": "CNOT", "target": 0},
        {"name": "CNOT", "target": 0, "control": None},
        {"name": "CNOT", "target": 0, "control": 0},
        {"name": "CNOT", "target": 0, "control": -1},
        {"name": "CNOT", "target": 0, "control": 3},
        {"name": "CNOT", "target": 0, "control": 1.0},
        {"name": "CNOT", "target": 0, "control": True},
        {"name": "CNOT", "target": 0, "control": 1, "control2": 2},
        {"name": "CCX", "target": 0, "control": 1},
        {"name": "CCX", "target": 0, "control": 1, "control2": None},
        {"name": "CCX", "target": 0, "control": 1, "control2": 0},
        {"name": "CCX", "target": 0, "control": 1, "control2": 1},
        {"name": "CCX", "target": 0, "control": 1, "control2": 3},
        {"name": "CCX", "target": 0, "control": 1, "control2": 2.0},
        {"name": "CCX", "target": 0, "control": 1, "control2": True},
        {"name": "M", "target": 3},
        {"name": "M", "target": 0, "control": 1},
    ],
)
def test_malformed_gate_is_rejected(gate):
    with pytest.raises(ValueError):
        simulate(3, [gate])


@pytest.mark.parametrize("angle", [math.nan, math.inf, -math.inf, 100 * math.pi + 1, -100 * math.pi - 1, None, "0.5", True, 1j])
@pytest.mark.parametrize("name", ["RY", "X", "M"])
def test_invalid_angles_are_rejected_even_when_irrelevant(name, angle):
    with pytest.raises(ValueError):
        simulate(1, [{"name": name, "target": 0, "angle": angle}])


@pytest.mark.parametrize("angle", [-100 * math.pi, 0, 100 * math.pi])
def test_angle_bounds_are_inclusive(angle):
    actual = simulate(1, [{"name": "RY", "target": 0, "angle": angle}])
    np.testing.assert_allclose(actual, [1, 0], rtol=0, atol=1e-13)


def test_measurements_must_be_terminal():
    with pytest.raises(ValueError, match="terminal"):
        simulate(2, [{"name": "M", "target": 0}, {"name": "X", "target": 1}])


def test_compile_can_apply_stricter_qubit_limit():
    from backend.reference.statevector import compile_operations

    with pytest.raises(ValueError):
        compile_operations(7, [], max_qubits=6)


@pytest.mark.parametrize("max_qubits", [0, 9, True, 6.0])
def test_compile_cannot_bypass_global_qubit_cap(max_qubits):
    from backend.reference.statevector import compile_operations

    with pytest.raises(ValueError):
        compile_operations(1, [], max_qubits=max_qubits)


def test_all_input_is_validated_before_numpy_allocation(monkeypatch):
    from backend.reference import statevector

    def unexpected_allocation(*args, **kwargs):
        raise AssertionError("NumPy allocation occurred before invalid input was rejected")

    # A valid first gate must not allocate its matrix before a malformed later gate.
    monkeypatch.setattr(statevector.np, "array", unexpected_allocation)
    monkeypatch.setattr(statevector.np, "zeros", unexpected_allocation)
    monkeypatch.setattr(statevector.np, "eye", unexpected_allocation)
    with pytest.raises(ValueError):
        statevector.simulate_statevector(2, [{"name": "H", "target": 0}, {"name": "X", "target": 2}])
