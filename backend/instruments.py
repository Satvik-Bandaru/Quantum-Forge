"""A bounded, explicitly simulated one-device instrument graph.

All rates are per microsecond; frequencies used by callers are cycles/us (MHz).
Configuration validity is separate from operational readiness.
"""
from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from .models import StrictModel
from .thermal import ThermalNetwork, simulate_thermal


class Instrument(StrictModel):
    enabled: bool = True
    fault: Literal['none', 'injected'] = 'none'


class Cryostat(Instrument):
    id: Literal['cryostat'] = 'cryostat'
    base_temperature_k: float = Field(default=.02, ge=.005, le=1)
    initial_temperature_k: float = Field(default=4, ge=.005, le=300)
    cooldown_time_constant_s: float = Field(default=180, ge=1, le=86400)
    elapsed_s: float = Field(default=1800, ge=0, le=604800)
    thermal_model: Literal['legacy_exponential', 'thermal_network'] = 'legacy_exponential'
    network: ThermalNetwork = Field(default_factory=ThermalNetwork)

    @model_validator(mode='after')
    def valid_temperatures(self):
        if self.initial_temperature_k < self.base_temperature_k:
            raise ValueError('Initial temperature must be at least the base temperature.')
        return self


class Microwave(Instrument):
    id: Literal['microwave'] = 'microwave'
    frequency_ghz: float = Field(default=5, ge=1, le=10)
    power_dbm: float = Field(default=0, ge=-100, le=10)
    line_attenuation_db: float = Field(default=20, ge=0, le=120)
    phase_deg: float = Field(default=0, ge=-360, le=360)


class PulseController(Instrument):
    id: Literal['controller'] = 'controller'
    pi_duration_us: float = Field(default=.05, ge=.001, le=10)
    analysis_phase_deg: float = Field(default=0, ge=-360, le=360)


class TwoLevelDevice(Instrument):
    id: Literal['device'] = 'device'
    frequency_ghz: float = Field(default=5, ge=1, le=10)
    t1_us: float = Field(default=50, ge=1, le=1000)
    tphi_us: float = Field(default=80, ge=1, le=10000)
    coupling_mhz_per_sqrt_mw: float = Field(default=100, ge=.1, le=1000)
    max_temperature_k: float = Field(default=.1, ge=.005, le=1)


class Readout(Instrument):
    id: Literal['readout'] = 'readout'
    error_0_to_1: float = Field(default=.02, ge=0, le=.49)
    error_1_to_0: float = Field(default=.04, ge=0, le=.49)


class SignalState(StrictModel):
    """Typed predicted/configured port signal; measurements require an acquisition."""
    port_id: str
    direction: Literal['input', 'output']
    kind: Literal['thermal', 'rf', 'iq', 'trigger', 'readout']
    status: Literal['predicted', 'pending_acquisition', 'unavailable']
    source_port: str | None = None
    values: dict[str, float] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    provenance: str


class CalibrationState(StrictModel):
    status: Literal['declared_uncalibrated'] = 'declared_uncalibrated'
    evidence_run_id: str | None = None
    description: str = 'Declared educational model settings. Calibration run estimates are evidence in History; they do not automatically certify or overwrite instrument settings.'


class MeasurementUncertainty(StrictModel):
    quantity: str
    standard_uncertainty: float | None = None
    unit: str
    basis: Literal['not_estimated'] = 'not_estimated'
    description: str = 'Physical parameter uncertainty is not calibrated. Numerical solver tolerance is not measurement uncertainty; finite-shot intervals are reported with acquired results.'


class PhysicalState(StrictModel):
    operating_state: Literal['ready', 'disabled', 'fault', 'cooling', 'disconnected']
    quantities: dict[str, float] = Field(default_factory=dict)
    units: dict[str, str] = Field(default_factory=dict)
    provenance: str = 'Deterministic educational model or declared setting; not live instrument telemetry.'


PORTS = {
    'cryostat': [('thermal', 'output', 'thermal')],
    'microwave': [('rf', 'output', 'rf'), ('iq', 'input', 'iq')],
    'controller': [('iq', 'output', 'iq'), ('trigger', 'output', 'trigger')],
    'device': [('thermal', 'input', 'thermal'), ('drive', 'input', 'rf'), ('readout', 'output', 'readout')],
    'readout': [('input', 'input', 'readout'), ('trigger', 'input', 'trigger')],
}
PORT_LOOKUP = {f'{instrument}:{port}': (direction, signal)
               for instrument, ports in PORTS.items() for port, direction, signal in ports}
REQUIRED_CONNECTIONS = (
    ('cryostat:thermal', 'device:thermal'),
    ('microwave:rf', 'device:drive'),
    ('controller:iq', 'microwave:iq'),
    ('controller:trigger', 'readout:trigger'),
    ('device:readout', 'readout:input'),
)
LABELS = {'cryostat': 'Dilution refrigerator', 'microwave': 'Microwave source',
          'controller': 'Pulse controller', 'device': 'Two-level device', 'readout': 'Binary readout'}
CATEGORIES = {'cryostat': 'cryogenics', 'microwave': 'microwave_source',
              'controller': 'pulse_control', 'device': 'quantum_device', 'readout': 'measurement'}


class Connection(StrictModel):
    source: str = Field(max_length=40)
    target: str = Field(max_length=40)


class ApparatusConfig(StrictModel):
    cryostat: Cryostat = Field(default_factory=Cryostat)
    microwave: Microwave = Field(default_factory=Microwave)
    controller: PulseController = Field(default_factory=PulseController)
    device: TwoLevelDevice = Field(default_factory=TwoLevelDevice)
    readout: Readout = Field(default_factory=Readout)
    connections: list[Connection] = Field(default_factory=lambda: [Connection(source=s, target=t) for s, t in REQUIRED_CONNECTIONS], max_length=5)

    @model_validator(mode='after')
    def valid_connections(self):
        seen = set()
        occupied = set()
        for link in self.connections:
            pair = (link.source, link.target)
            if pair in seen:
                raise ValueError('Duplicate connection is not allowed.')
            if link.source not in PORT_LOOKUP or link.target not in PORT_LOOKUP:
                raise ValueError('Connection references an unknown instrument port.')
            source_direction, source_signal = PORT_LOOKUP[link.source]
            target_direction, target_signal = PORT_LOOKUP[link.target]
            if source_direction != 'output' or target_direction != 'input' or source_signal != target_signal:
                raise ValueError('Connection requires compatible output and input signal ports.')
            if link.target in occupied:
                raise ValueError('An input port can have only one connection.')
            seen.add(pair)
            occupied.add(link.target)
        return self


def apparatus_status(config: ApparatusConfig) -> dict:
    """Inspect without advancing simulated time, mutating state or acquiring data."""
    c, m, d = config.cryostat, config.microwave, config.device
    thermal = simulate_thermal(c.network, c.elapsed_s) if c.thermal_model == 'thermal_network' else None
    temperature = (thermal['stages'][-1]['temperature_k'] if thermal is not None else
                   c.base_temperature_k + (c.initial_temperature_k - c.base_temperature_k) * math.exp(-c.elapsed_s / c.cooldown_time_constant_s))
    exponent = 6.62607015e-34 * d.frequency_ghz * 1e9 / (1.380649e-23 * temperature)
    boltzmann = math.exp(-exponent)
    thermal_population = boltzmann / (1 + boltzmann)
    nbar = 0.0 if exponent > 700 else 1 / math.expm1(exponent)
    down, up = (nbar + 1) / d.t1_us, nbar / d.t1_us
    drive = d.coupling_mhz_per_sqrt_mw * 10 ** ((m.power_dbm - m.line_attenuation_db) / 20)
    detuning = (d.frequency_ghz - m.frequency_ghz) * 1000
    derived = {'temperature_k': temperature, 'thermal_population': thermal_population,
               'detuning_mhz': detuning, 'rabi_frequency_mhz': drive,
               'gamma_up_per_us': up, 'gamma_down_per_us': down,
               'effective_t1_us': 1 / (up + down),
               'effective_t2_us': 1 / ((up + down) / 2 + 1 / d.tphi_us)}
    issues = []

    def issue(code, name, message):
        issues.append({'code': code, 'instrument_id': name, 'message': message})

    for name in PORTS:
        instrument = getattr(config, name)
        if not instrument.enabled:
            issue('disabled', name, f'{LABELS[name]} is disabled.')
        if instrument.fault != 'none':
            issue('injected_fault', name, f'{LABELS[name]} has an explicitly injected simulated fault.')
    if thermal is not None and not thermal['valid']:
        issue('thermal_model_limit', 'cryostat', 'Thermal trajectory reached the 350 K model limit before the requested elapsed time. Reduce heat loads or increase cooling; this truncated state cannot run an experiment.')
    if temperature > d.max_temperature_k:
        issue('temperature_interlock', 'cryostat', f'Temperature {temperature:.6g} K exceeds device interlock {d.max_temperature_k:.6g} K; advance simulated cooldown or change the declared interlock.')
    if abs(detuning) > 100 + 1e-9:
        issue('detuning_out_of_model', 'microwave', 'Source detuning exceeds the bounded ±100 MHz rotating-frame model.')
    if drive > min(200, 50 * d.frequency_ghz):
        issue('drive_out_of_model', 'microwave', 'Drive exceeds 200 MHz or 5% of the device frequency; reduce source power or coupling.')
    connected = {(link.source, link.target) for link in config.connections}
    for source, target in REQUIRED_CONNECTIONS:
        if (source, target) not in connected:
            issue('missing_connection', target.split(':')[0], f'Missing required connection {source} → {target}.')
    instruments = []
    for name, ports in PORTS.items():
        instrument = getattr(config, name)
        own_issues = [i for i in issues if i['instrument_id'] == name]
        if instrument.fault != 'none':
            state = 'fault'
        elif not instrument.enabled:
            state = 'disabled'
        elif any(i['code'] == 'thermal_model_limit' for i in own_issues):
            state = 'fault'
        elif any(i['code'] == 'temperature_interlock' for i in own_issues):
            state = 'cooling'
        elif any(i['code'] == 'missing_connection' for i in own_issues):
            state = 'disconnected'
        elif own_issues:
            state = 'fault'
        else:
            state = 'ready'
        instruments.append({'id': name, 'type': name, 'category': CATEGORIES[name], 'label': LABELS[name], 'state': state,
                            'config': instrument.model_dump(),
                            'ports': [{'id': port, 'direction': direction, 'signal': signal} for port, direction, signal in ports],
                            'limits': type(instrument).model_json_schema()['properties'], 'issues': own_issues})
    _add_instrument_signals(config, instruments, derived, thermal, issues)
    result = {'ready': not issues, 'instruments': instruments, 'connections': [c.model_dump() for c in config.connections], 'issues': issues, 'derived': derived}
    if thermal is not None:
        result['thermal'] = thermal
    return result


def _add_instrument_signals(config, instruments, derived, thermal, issues):
    """Resolve this acyclic, fixed instrument graph in physical dependency order."""
    by_id = {row['id']: row for row in instruments}
    incoming = {link.target: link.source for link in config.connections}
    outputs = {}
    uncertainties = {'cryostat': ('temperature', 'K'), 'microwave': ('frequency and delivered power', 'GHz / dBm'),
                     'controller': ('pulse duration', 'µs'), 'device': ('coherence parameters', 'µs'),
                     'readout': ('assignment probabilities', 'probability')}

    for name in ('cryostat', 'controller', 'microwave', 'device', 'readout'):
        row = by_id[name]
        configured = getattr(config, name)
        own_valid = configured.enabled and configured.fault == 'none'
        # A warm cryostat can predict its temperature, but the device is
        # interlocked. Invalid thermal traces are not emitted as usable signals.
        if name == 'cryostat' and thermal is not None and not thermal['valid']:
            own_valid = False
        if name == 'microwave' and row['issues']:
            own_valid = False
        if name == 'device' and derived['temperature_k'] > configured.max_temperature_k:
            own_valid = False
        inputs = []
        for port, direction, kind in PORTS[name]:
            if direction != 'input':
                continue
            source = incoming.get(f'{name}:{port}')
            upstream = outputs.get(source)
            available = own_valid and upstream is not None and upstream.status != 'unavailable'
            inputs.append(SignalState(port_id=port, direction='input', kind=kind,
                                      status=upstream.status if available else 'unavailable',
                                      source_port=source, values=upstream.values if available else {},
                                      units=upstream.units if available else {},
                                      provenance='Derived from the connected source model; not hardware telemetry.' if available else 'Missing, faulted, disabled or interlocked signal path.'))
        chain_valid = own_valid and all(signal.status != 'unavailable' for signal in inputs)
        if own_valid and not chain_valid and row['state'] == 'ready':
            row['state'] = 'disconnected'
            issue = {'code': 'upstream_unavailable', 'instrument_id': name,
                     'message': f'{LABELS[name]} has an unavailable upstream signal; inspect its connected source.'}
            row['issues'].append(issue)
            issues.append(issue)
        declared = {
            ('cryostat', 'thermal'): ({'temperature_k': derived['temperature_k']}, {'temperature_k': 'K'}),
            ('controller', 'iq'): ({'pi_duration_us': config.controller.pi_duration_us,
                                   'analysis_phase_deg': config.controller.analysis_phase_deg}, {'pi_duration_us': 'µs', 'analysis_phase_deg': 'degree'}),
            ('controller', 'trigger'): ({}, {}),
            ('microwave', 'rf'): ({'frequency_ghz': config.microwave.frequency_ghz,
                                  'power_dbm': config.microwave.power_dbm - config.microwave.line_attenuation_db,
                                  'phase_deg': config.microwave.phase_deg},
                                 {'frequency_ghz': 'GHz', 'power_dbm': 'dBm', 'phase_deg': 'degree'}),
            ('device', 'readout'): ({}, {}),
        }
        own_outputs = []
        for port, direction, kind in PORTS[name]:
            if direction != 'output':
                continue
            values, units = declared[(name, port)]
            status = ('pending_acquisition' if name == 'device' else 'predicted') if chain_valid else 'unavailable'
            signal = SignalState(port_id=port, direction='output', kind=kind, status=status,
                                 values=values if chain_valid else {}, units=units if chain_valid else {},
                                 provenance=('No acquired readout yet; execute a sequence to obtain state probabilities and sampled counts.' if name == 'device' and chain_valid else
                                             'Declared control or deterministic model prediction; not a measured signal or live hardware.' if chain_valid else
                                             'Instrument or upstream signal path is not operational.'))
            outputs[f'{name}:{port}'] = signal
            own_outputs.append(signal)
        row['input_signals'] = [signal.model_dump() for signal in inputs]
        row['output_signals'] = [signal.model_dump() for signal in own_outputs]
        row['calibration_state'] = CalibrationState().model_dump()
        quantity, unit = uncertainties[name]
        row['measurement_uncertainties'] = [MeasurementUncertainty(quantity=quantity, unit=unit).model_dump()]
        quantities, units = {
            'cryostat': ({'temperature_k': derived['temperature_k']}, {'temperature_k': 'K'}),
            'microwave': ({'frequency_ghz': config.microwave.frequency_ghz, 'delivered_power_dbm': config.microwave.power_dbm - config.microwave.line_attenuation_db}, {'frequency_ghz': 'GHz', 'delivered_power_dbm': 'dBm'}),
            'controller': ({'pi_duration_us': config.controller.pi_duration_us}, {'pi_duration_us': 'µs'}),
            'device': ({'thermal_population': derived['thermal_population'], 'effective_t1_us': derived['effective_t1_us'], 'effective_t2_us': derived['effective_t2_us']}, {'thermal_population': 'probability', 'effective_t1_us': 'µs', 'effective_t2_us': 'µs'}),
            'readout': ({'error_0_to_1': config.readout.error_0_to_1, 'error_1_to_0': config.readout.error_1_to_0}, {'error_0_to_1': 'probability', 'error_1_to_0': 'probability'}),
        }[name]
        row['physical_state'] = PhysicalState(operating_state=row['state'], quantities=quantities, units=units).model_dump()


def validate_runnable(config: ApparatusConfig) -> dict:
    status = apparatus_status(config)
    if not status['ready']:
        raise ValueError('Apparatus is not ready: ' + ' '.join(i['message'] for i in status['issues']))
    return status
