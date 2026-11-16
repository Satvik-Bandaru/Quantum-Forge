import {CartesianGrid,Legend,Line,LineChart,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
import {Field} from '../Optimization';
import type {CryostatConfig,ThermalEvidence,ThermalNetworkConfig,ThermalStageConfig} from './types';
import {initialThermalNetwork} from './types';

const stages=[['shield','Radiation shield'],['cold_plate','Cold plate'],['mixing_chamber','Mixing chamber']] as const;
const fields:{key:keyof ThermalStageConfig;label:string;min:number;max:number;step:number}[]=[
 {key:'initial_temperature_k',label:'Initial temperature (K)',min:.005,max:350,step:.005},
 {key:'bath_temperature_k',label:'Cooling bath temperature (K)',min:.005,max:350,step:.005},
 {key:'heat_capacity_j_per_k',label:'Heat capacity (J/K)',min:.001,max:100000,step:.001},
 {key:'heat_load_w',label:'Heat load (W)',min:0,max:100,step:.000001},
 {key:'cooling_conductance_w_per_k',label:'Cooling conductance (W/K)',min:0,max:10,step:.000001},
 {key:'cooling_capacity_w',label:'Maximum cooling power (W)',min:0,max:100,step:.000001},
];
function Numeric({label,value,min,max,step,onChange}:{label:string;value:number;min:number;max:number;step:number;onChange:(value:number)=>void}){
 return <Field label={label}><input aria-label={label} type="number" min={min} max={max} step={step} value={value} onChange={event=>onChange(Number(event.target.value))}/></Field>;
}
export function ThermalControls({cryostat,change}:{cryostat:CryostatConfig;change:(patch:Partial<CryostatConfig>)=>void}){
 const network=cryostat.network??initialThermalNetwork;
 function update(patch:Partial<ThermalNetworkConfig>){change({network:{...network,...patch}})}
 return <div className="connected-thermal-controls">
  <p className="connected-help">Three finite heat-capacity stages exchange heat with one another and a fixed room boundary. Each cooler has a declared bath temperature and maximum power. This thermal circuit is educational; it does not simulate a helium dilution cycle.</p>
  <div className="connected-field-grid">
   <Numeric label="Room boundary temperature (K)" value={network.room_temperature_k} min={200} max={350} step={1} onChange={value=>update({room_temperature_k:value})}/>
   <Numeric label="Room → shield coupling (W/K)" value={network.room_to_shield_w_per_k} min={0} max={1} step={.000001} onChange={value=>update({room_to_shield_w_per_k:value})}/>
   <Numeric label="Shield → cold plate coupling (W/K)" value={network.shield_to_cold_plate_w_per_k} min={0} max={1} step={.000001} onChange={value=>update({shield_to_cold_plate_w_per_k:value})}/>
   <Numeric label="Cold plate → mixing coupling (W/K)" value={network.cold_plate_to_mixing_w_per_k} min={0} max={1} step={.0000001} onChange={value=>update({cold_plate_to_mixing_w_per_k:value})}/>
  </div>
  {stages.map(([id,label])=><details className="connected-thermal-stage" key={id} open={id==='mixing_chamber'?true:undefined}><summary>{label} controls</summary><div className="connected-field-grid">{fields.map(field=><Numeric key={field.key} label={`${label}: ${field.label}`} value={network[id][field.key]} min={field.min} max={field.max} step={field.step} onChange={value=>update({[id]:{...network[id],[field.key]:value}})}/>)}</div></details>)}
  <p className="connected-equation">Cᵢ dTᵢ/dt = heat load + conducted heat − cooling power</p>
  <p className="connected-help">The computed mixing-chamber temperature sets the device's thermal population and upward/downward transition rates. Temperature is frozen during a microsecond-scale acquisition. Advance elapsed time explicitly to recompute thermal evolution.</p>
 </div>;
}
const valueText=(value:number)=>Math.abs(value)>0&&Math.abs(value)<.001?value.toExponential(3):value.toFixed(5);
export function ThermalState({thermal}:{thermal:ThermalEvidence}){
 return <section className="connected-thermal-evidence" aria-label="Computed thermal state" data-testid="thermal-state">
  <h3>Computed thermal state</h3><p className="connected-help">Model predictions at {thermal.elapsed_s.toFixed(1)} simulated seconds. No thermometer is connected. {thermal.valid?'Within declared model limits.':'Thermal model limit reached; acquisition is blocked.'}</p>
  <div className="table-scroll"><table><thead><tr><th>Stage</th><th>Temperature (K)</th><th>Cooling (W)</th><th>Net power (W)</th></tr></thead><tbody>{thermal.stages.map(stage=><tr key={stage.id}><td>{stage.label}</td><td data-testid={`thermal-temperature-${stage.id}`}>{valueText(stage.temperature_k)}</td><td>{stage.id==='room'?'Fixed boundary':valueText(stage.cooling_power_w)}</td><td>{stage.id==='room'?'Reservoir':valueText(stage.net_power_w)}</td></tr>)}</tbody></table></div>
  <div className="connected-thermal-chart" role="img" aria-label="Thermal stage temperatures over simulated time, logarithmic temperature scale"><ResponsiveContainer width="100%" height={230}><LineChart data={thermal.trajectory} margin={{top:10,right:10,bottom:22,left:0}}><CartesianGrid stroke="#263c4e" strokeDasharray="3 6"/><XAxis dataKey="time_s" type="number" domain={['dataMin','dataMax']} stroke="#8aa0b7" fontSize={9} tickFormatter={value=>Number(value).toFixed(0)} label={{value:'Simulated time (s)',position:'insideBottom',offset:-15,fill:'#91a9bc',fontSize:10}}/><YAxis scale="log" domain={['auto','auto']} width={45} stroke="#8aa0b7" fontSize={9} tickFormatter={value=>Number(value).toPrecision(2)}/><Tooltip formatter={(value,name)=>[`${Number(value).toPrecision(5)} K`,name]} labelFormatter={value=>`${Number(value).toFixed(1)} s`} contentStyle={{background:'#101f2b',border:'1px solid #3a5669',fontSize:10}}/><Legend wrapperStyle={{fontSize:9}} verticalAlign="top"/><Line dataKey="shield_k" name="Shield (K)" stroke="#e0b778" dot={false} isAnimationActive={false}/><Line dataKey="cold_plate_k" name="Cold plate (K)" stroke="#95b8ef" dot={false} isAnimationActive={false}/><Line dataKey="mixing_chamber_k" name="Mixing chamber (K)" stroke="#6ed6cf" dot={false} isAnimationActive={false}/></LineChart></ResponsiveContainer></div>
  <details className="connected-record-details"><summary>Energy balance and thermal solver evidence</summary><dl className="connected-runtime"><div><dt>Stored energy change</dt><dd>{valueText(thermal.energy.stored_change_j)} J</dd></div><div><dt>Applied heat</dt><dd>{valueText(thermal.energy.heat_input_j)} J</dd></div><div><dt>Room-boundary heat</dt><dd>{valueText(thermal.energy.boundary_heat_j)} J</dd></div><div><dt>Removed heat</dt><dd>{valueText(thermal.energy.cooling_removed_j)} J</dd></div><div><dt>Balance residual</dt><dd>{valueText(thermal.energy.residual_j)} J</dd></div><div><dt>Solver</dt><dd>{thermal.solver}</dd></div></dl>{thermal.checks.map(check=><p className="connected-help" key={check.name}>{check.passed?'Passed':'Failed'} · {check.name}: {check.value.toExponential(3)} (tolerance {check.tolerance})</p>)}{thermal.limitations.map(item=><p className="connected-help" key={item}>{item}</p>)}</details>
 </section>;
}
