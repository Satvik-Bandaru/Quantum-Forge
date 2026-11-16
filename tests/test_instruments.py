"""Independent apparatus constraints and thermodynamic checks."""
import math

import pytest
from pydantic import ValidationError

from backend.instruments import ApparatusConfig, apparatus_status, validate_runnable


def apparatus(**patch):
    data = ApparatusConfig().model_dump()
    for name, value in patch.items():
        if isinstance(value, dict):
            data[name].update(value)
        else:
            data[name] = value
    return ApparatusConfig.model_validate(data)


def test_default_apparatus_ready_and_cooldown_is_explicit():
    status = apparatus_status(ApparatusConfig())
    assert status['ready']
    assert status['derived']['temperature_k'] == pytest.approx(0.02 + 3.98 * math.exp(-10))
    assert status['derived']['rabi_frequency_mhz'] == pytest.approx(10)
    assert len(status['instruments']) == 5
    assert all(item['ports'] and item['limits'] for item in status['instruments'])
    assert apparatus_status(ApparatusConfig()) == status


def test_missing_links_are_saveable_but_nonrunnable():
    config = apparatus(connections=[])
    status = apparatus_status(config)
    assert not status['ready']
    assert len([i for i in status['issues'] if i['code'] == 'missing_connection']) == 5
    with pytest.raises(ValueError, match='connection'):
        validate_runnable(config)


@pytest.mark.parametrize('links', [
    [{'source': 'microwave:rf', 'target': 'readout:input'}],
    [{'source': 'device:drive', 'target': 'microwave:rf'}],
    [{'source': 'unknown:rf', 'target': 'device:drive'}],
    [{'source': 'microwave:rf', 'target': 'device:drive'}] * 2,
])
def test_rejects_unknown_reversed_incompatible_duplicate_connections(links):
    with pytest.raises(ValidationError):
        apparatus(connections=links)


@pytest.mark.parametrize('patch', [
    {'cryostat': {'id': 'device'}}, {'microwave': {'power_dbm': float('nan')}},
    {'controller': {'pi_duration_us': 0}}, {'readout': {'error_0_to_1': .5}},
    {'device': {'t1_us': -1}}, {'cryostat': {'initial_temperature_k': .01}},
    {'microwave': {'invented': 1}},
])
def test_rejects_invalid_configuration(patch):
    with pytest.raises(ValidationError):
        apparatus(**patch)


@pytest.mark.parametrize('name', ['cryostat', 'microwave', 'controller', 'device', 'readout'])
def test_disabled_or_faulted_instrument_prevents_run(name):
    for patch, state in [({'enabled': False}, 'disabled'), ({'fault': 'injected'}, 'fault')]:
        status = apparatus_status(apparatus(**{name: patch}))
        assert not status['ready']
        assert next(i for i in status['instruments'] if i['id'] == name)['state'] == state


def test_temperature_interlock_uses_actual_cooldown_not_elapsed_flag():
    status = apparatus_status(apparatus(cryostat={'elapsed_s': 0}))
    assert not status['ready']
    assert status['derived']['temperature_k'] == 4
    assert any(i['code'] == 'temperature_interlock' for i in status['issues'])
    assert apparatus_status(apparatus(cryostat={'elapsed_s': 604800}))['ready']


def test_gibbs_population_and_bosonic_detailed_balance_use_zero_temperature_t1():
    status = apparatus_status(apparatus(cryostat={'base_temperature_k': .1, 'initial_temperature_k': .1}, device={'max_temperature_k': .1}))
    derived = status['derived']
    x = 6.62607015e-34 * 5e9 / (1.380649e-23 * .1)
    assert derived['thermal_population'] == pytest.approx(1 / (1 + math.exp(x)))
    assert derived['gamma_up_per_us'] / derived['gamma_down_per_us'] == pytest.approx(math.exp(-x))
    assert derived['gamma_down_per_us'] - derived['gamma_up_per_us'] == pytest.approx(1 / 50)
    assert derived['effective_t1_us'] < 50
    assert derived['effective_t2_us'] <= 2 * derived['effective_t1_us']


def test_source_frequency_has_signed_device_minus_source_detuning_and_power_has_sqrt_scaling():
    a = apparatus_status(apparatus(microwave={'frequency_ghz': 4.999, 'power_dbm': -20}))['derived']
    assert a['detuning_mhz'] == pytest.approx(1)
    assert a['rabi_frequency_mhz'] == pytest.approx(1)


def test_outside_rotating_wave_budget_is_saveable_but_not_runnable():
    assert not apparatus_status(apparatus(microwave={'frequency_ghz': 1}))['ready']
    assert not apparatus_status(apparatus(microwave={'power_dbm': 10, 'line_attenuation_db': 0}, device={'coupling_mhz_per_sqrt_mw': 1000}))['ready']
