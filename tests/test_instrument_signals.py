"""Signal state is derived from compatible connected controls, never telemetry."""
import pytest

from backend.instruments import ApparatusConfig, apparatus_status


def instrument(status, name):
    return next(row for row in status['instruments'] if row['id'] == name)


def test_signal_state_exposes_actual_attenuated_source_and_device_inputs():
    status = apparatus_status(ApparatusConfig())
    source = instrument(status, 'microwave')['output_signals'][0]
    assert source['status'] == 'predicted'
    assert source['values']['power_dbm'] == -20
    assert source['values']['frequency_ghz'] == 5
    device_inputs = instrument(status, 'device')['input_signals']
    drive = next(row for row in device_inputs if row['port_id'] == 'drive')
    assert drive['source_port'] == 'microwave:rf'
    assert drive['values'] == source['values']
    readout = instrument(status, 'device')['output_signals'][0]
    assert readout['status'] == 'pending_acquisition'
    assert readout['values'] == {}


@pytest.mark.parametrize('patch', [
    {'controller': {'enabled': False}}, {'microwave': {'fault': 'injected'}},
    {'connections': []},
])
def test_unavailable_upstream_controls_do_not_emit_fake_live_signals(patch):
    config = ApparatusConfig.model_validate(patch)
    status = apparatus_status(config)
    drive = next(row for row in instrument(status, 'device')['input_signals'] if row['port_id'] == 'drive')
    assert drive['status'] == 'unavailable'
    assert drive['values'] == {}
    assert instrument(status, 'device')['output_signals'][0]['status'] == 'unavailable'
    assert instrument(status, 'device')['state'] == 'disconnected'


def test_declared_parameters_are_not_mislabeled_as_calibrated_measurements():
    status = apparatus_status(ApparatusConfig())
    for row in status['instruments']:
        assert row['category']
        assert row['calibration_state']['status'] == 'declared_uncalibrated'
        assert row['calibration_state']['evidence_run_id'] is None
        assert all(item['standard_uncertainty'] is None for item in row['measurement_uncertainties'])
        assert all(item['basis'] == 'not_estimated' for item in row['measurement_uncertainties'])
