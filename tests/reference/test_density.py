"""Hand-derived density and readout checks, independent of production simulators."""

import importlib
import math

import numpy as np
import pytest


pytestmark = pytest.mark.reference


def _density_module():
    # A missing reference is an explicit RED failure rather than a collection error.
    try:
        return importlib.import_module("backend.reference.density")
    except ModuleNotFoundError as exc:
        pytest.fail(f"Density reference is not implemented: {exc}")


def test_initial_density_and_q0_leftmost_basis():
    density = _density_module()
    expected = np.zeros((8, 8), dtype=complex)
    expected[0, 0] = 1
    np.testing.assert_array_equal(density.simulate_density(3, []), expected)
    expected[0, 0], expected[4, 4] = 0, 1
    np.testing.assert_array_equal(
        density.simulate_density(3, [{"name": "X", "target": 0}]), expected
    )


def test_complex_bell_density_keeps_conjugation_sign():
    density = _density_module()
    gates = [
        {"name": "H", "target": 0},
        {"name": "S", "target": 0},
        {"name": "CNOT", "control": 0, "target": 1},
    ]
    expected = np.array(
        [[0.5, 0, 0, -0.5j], [0, 0, 0, 0], [0, 0, 0, 0], [0.5j, 0, 0, 0.5]],
        dtype=complex,
    )
    np.testing.assert_allclose(density.simulate_density(2, gates), expected, rtol=0, atol=1e-14)


@pytest.mark.parametrize(
    "gate,occupied",
    [
        ({"name": "Z", "target": 2}, [0, 2]),
        ({"name": "CNOT", "control": 3, "target": 0}, [0, 1, 8, 9]),
        (
            {"name": "CCX", "control": 3, "control2": 0, "target": 2},
            [0, 1, 2, 3, 8, 9, 10, 11],
        ),
    ],
)
def test_complete_depolarization_is_only_on_gate_qubits(gate, occupied):
    density = _density_module()
    expected = np.zeros((16, 16), dtype=complex)
    expected[occupied, occupied] = 1 / len(occupied)
    np.testing.assert_allclose(
        density.simulate_density(4, [gate], gate_error=1), expected, rtol=0, atol=1e-14
    )


def test_partial_depolarization_preserves_nonadjacent_spectator():
    density = _density_module()
    gates = [
        {"name": "X", "target": 1},
        {"name": "CNOT", "control": 0, "target": 2},
    ]
    # The spectator has probabilities (1/4, 3/4); the pair has (5,1,1,1)/8.
    expected = np.diag(np.array([5, 1, 15, 3, 1, 1, 3, 3]) / 32)
    np.testing.assert_allclose(
        density.simulate_density(3, gates, gate_error=0.5), expected, rtol=0, atol=1e-14
    )


def test_local_depolarization_of_entangled_qubit_preserves_other_marginal():
    density = _density_module()
    gates = [
        {"name": "RY", "target": 0, "angle": math.pi / 3},
        {"name": "CNOT", "control": 0, "target": 1},
        {"name": "S", "target": 0},
    ]
    # After noisy RY and CNOT: diagonal (28,8,8,20)/64, marginal (9,7)/16.
    # The final local channel mixes with I/2 tensor that unchanged marginal.
    expected = np.diag(np.array([23, 11, 13, 17]) / 64).astype(complex)
    expected[0, 3], expected[3, 0] = -1j * math.sqrt(3) / 32, 1j * math.sqrt(3) / 32
    actual = density.simulate_density(2, gates, gate_error=0.5)
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-14)
    np.testing.assert_allclose(
        [actual[0, 0] + actual[2, 2], actual[1, 1] + actual[3, 3]],
        [9 / 16, 7 / 16],
        rtol=0,
        atol=1e-14,
    )


def test_depolarizing_spectator_preserves_rest_correlations():
    density = _density_module()
    gates = [
        {"name": "H", "target": 0},
        {"name": "CNOT", "control": 0, "target": 2},
        {"name": "S", "target": 1},
    ]
    expected = np.diag(np.array([9, 3, 3, 1, 3, 9, 1, 3]) / 32).astype(complex)
    expected[0, 5] = expected[5, 0] = 3 / 32
    expected[2, 7] = expected[7, 2] = 1 / 32
    np.testing.assert_allclose(
        density.simulate_density(3, gates, gate_error=0.5), expected, rtol=0, atol=1e-14
    )


def test_noise_is_applied_after_each_gate():
    density = _density_module()
    gates = [{"name": "X", "target": 0}, {"name": "X", "target": 0}]
    np.testing.assert_allclose(
        density.simulate_density(1, gates, gate_error=0.2),
        [[0.82, 0], [0, 0.18]],
        rtol=0,
        atol=1e-14,
    )


@pytest.mark.parametrize("gate_error", [0.0, 0.15, 1.0])
def test_density_remains_hermitian_normalized_and_positive(gate_error):
    density = _density_module()
    gates = [
        {"name": "H", "target": 2},
        {"name": "RX", "target": 0, "angle": 0.731},
        {"name": "CNOT", "control": 2, "target": 1},
        {"name": "CP", "control": 0, "target": 2, "angle": -1.217},
        {"name": "CCX", "control": 1, "control2": 2, "target": 0},
        {"name": "RY", "target": 2, "angle": -0.411},
        {"name": "SWAP", "control": 1, "target": 0},
    ] * 8
    actual = density.simulate_density(3, gates, gate_error=gate_error)
    assert np.iscomplexobj(actual)
    assert np.isfinite(actual).all()
    np.testing.assert_allclose(actual, actual.conj().T, rtol=0, atol=1e-12)
    assert np.trace(actual) == pytest.approx(1, rel=0, abs=1e-12)
    assert np.linalg.eigvalsh(actual).min() >= -1e-12


def test_terminal_measurements_do_not_apply_gate_noise():
    density = _density_module()
    gates = [{"name": "X", "target": 0}]
    actual = density.simulate_density(2, gates, gate_error=0.5)
    # The single-qubit X channel mixes |10> and |00>, leaving q1 at zero.
    expected = np.diag([0.25, 0.0, 0.75, 0.0])
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-14)
    np.testing.assert_array_equal(
        density.simulate_density(
            2, gates + [{"name": "M", "target": 0}, {"name": "M", "target": 1}],
            gate_error=0.5,
        ),
        actual,
    )


@pytest.mark.parametrize("readout_error,index", [(0, 4), (1, 3)])
def test_readout_endpoints_preserve_or_complement_bits(readout_error, index):
    density = _density_module()
    expected = np.zeros(8)
    expected[index] = 1
    actual = density.simulate_probabilities(
        3, [{"name": "X", "target": 0}], readout_error=readout_error
    )
    np.testing.assert_array_equal(actual, expected)


def test_readout_flips_each_bit_independently_in_q0_leftmost_order():
    density = _density_module()
    expected = np.array([9, 3, 3, 1, 27, 9, 9, 3]) / 64
    actual = density.simulate_probabilities(
        3, [{"name": "X", "target": 0}], readout_error=0.25
    )
    assert np.issubdtype(actual.dtype, np.floating)
    np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-14)


def test_half_readout_error_is_uniform_on_correlated_distribution():
    density = _density_module()
    gates = [{"name": "H", "target": 0}, {"name": "CNOT", "control": 0, "target": 2}]
    np.testing.assert_allclose(
        density.simulate_probabilities(3, gates, gate_error=0.17, readout_error=0.5),
        np.full(8, 1 / 8),
        rtol=0,
        atol=1e-14,
    )


def test_gate_and_readout_flip_probabilities_compose():
    density = _density_module()
    # X then lambda=.4 depolarization gives P(0)=.2. A .3 readout flip
    # gives P(observed 0)=.2*.7+.8*.3=.38, not .2+.3.
    np.testing.assert_allclose(
        density.simulate_probabilities(
            1, [{"name": "X", "target": 0}], gate_error=0.4, readout_error=0.3
        ),
        [0.38, 0.62],
        rtol=0,
        atol=1e-14,
    )


def test_six_qubit_limit_is_supported():
    density = _density_module()
    actual = density.simulate_density(6, [{"name": "X", "target": 5}])
    assert actual.shape == (64, 64)
    assert actual[1, 1] == 1
    assert np.count_nonzero(actual) == 1


@pytest.mark.parametrize("qubits", [0, -1, 7, 1.5, True])
def test_invalid_qubit_counts_raise(qubits):
    density = _density_module()
    with pytest.raises(ValueError):
        density.simulate_density(qubits, [])


@pytest.mark.parametrize("field", ["gate_error", "readout_error"])
@pytest.mark.parametrize("value", [-0.001, 1.001, math.nan, math.inf, -math.inf, "0.1", None, True, 0.1j])
def test_invalid_noise_raises(field, value):
    density = _density_module()
    with pytest.raises(ValueError):
        density.simulate_probabilities(1, [], **{field: value})


@pytest.mark.parametrize(
    "kwargs",
    [
        {"qubits": 7, "gates": []},
        {"qubits": 1, "gates": [], "gate_error": -0.1},
        {"qubits": 1, "gates": [], "readout_error": math.nan},
        {"qubits": 1, "gates": [{"name": "X", "target": 1}]},
        {"qubits": 1, "gates": [{"name": "X", "target": 0}] * 129},
        {"qubits": 1, "gates": [{"name": "M", "target": 0}, {"name": "H", "target": 0}]},
    ],
)
def test_invalid_inputs_rejected_before_state_allocation(monkeypatch, kwargs):
    density = _density_module()

    def unexpected_allocation(*args, **kwargs):
        pytest.fail("Invalid request reached NumPy state allocation")

    monkeypatch.setattr(np, "zeros", unexpected_allocation)
    with pytest.raises(ValueError):
        density.simulate_probabilities(**kwargs)


def test_nonphysical_evolution_is_rejected_instead_of_renormalized(monkeypatch):
    density = _density_module()
    # Inject an invalid compiled unitary to model an internal scientific bug.
    monkeypatch.setattr(
        density, "compile_operations",
        lambda *args, **kwargs: [((0,), np.array([[2, 0], [0, 1]], dtype=complex))],
    )
    with pytest.raises(ValueError, match="trace|normaliz|physical"):
        density.simulate_density(1, [])
