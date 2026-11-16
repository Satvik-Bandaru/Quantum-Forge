import type {ApparatusStatus,InstrumentSignal} from './types';

function Signal({signal}:{signal:InstrumentSignal}){
 return <div className="connected-signal"><div><code>{signal.port_id}</code><span>{signal.direction} · {signal.kind} · {signal.status.replaceAll('_',' ')}</span></div>{signal.source_port&&<p>Source: <code>{signal.source_port}</code></p>}{Object.entries(signal.values).map(([key,value])=><p key={key}><span>{key.replaceAll('_',' ')}</span><b>{Number.isFinite(value)?Number(value.toPrecision(6)).toString():'Unavailable'} {signal.units[key]??''}</b></p>)}<p>{signal.provenance}</p></div>;
}
export function InstrumentEvidence({instrument}:{instrument:ApparatusStatus['instruments'][number]|undefined}){
 if(!instrument?.input_signals&&!instrument?.output_signals)return null;
 return <section className="connected-instrument-evidence" aria-label="Instrument signal evidence" data-testid="instrument-signal-evidence"><h3>Signals and calibration state</h3><p className="connected-help">{instrument.category?.replaceAll('_',' ')} · {instrument.calibration_state?.status.replaceAll('_',' ')}. {instrument.calibration_state?.description}</p><details className="connected-record-details"><summary>Inspect input and output signals</summary>{[...instrument.input_signals??[],...instrument.output_signals??[]].map(signal=><Signal key={signal.direction+signal.port_id} signal={signal}/>)}</details><details className="connected-record-details"><summary>Declared uncertainty limitations</summary>{instrument.measurement_uncertainties?.map(item=><p key={item.quantity} className="connected-help"><b>{item.quantity.replaceAll('_',' ')}</b>: {item.standard_uncertainty===null?'Not estimated':`${item.standard_uncertainty} ${item.unit}`}. {item.description}</p>)}</details></section>;
}
