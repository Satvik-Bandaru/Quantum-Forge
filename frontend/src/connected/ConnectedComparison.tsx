import {CartesianGrid,Legend,Line,LineChart,ResponsiveContainer,Tooltip,XAxis,YAxis} from 'recharts';
import type {Run} from '../types';
import type {ConnectedResult} from './types';

function flattened(value:unknown,path=''):Record<string,string>{
 if(value===null||typeof value!=='object')return {[path]:String(value)};
 return Object.fromEntries(Object.entries(value).flatMap(([key,item])=>Object.entries(flattened(item,path?`${path}.${key}`:key))));
}
export function ConnectedComparison({pinned,current,clear}:{pinned:Run;current:Run|null;clear:()=>void}){
 const a=pinned.result as unknown as ConnectedResult;
 const b=current?.status==='completed'&&current.result?current.result as unknown as ConnectedResult:null;
 const sameRun=current?.id===pinned.id;
 const compatible=!!b&&a.sequence===b.sequence&&a.axes.x_unit===b.axes.x_unit&&a.axes.x_label===b.axes.x_label&&a.series.length===b.series.length&&a.series.every((point,index)=>Math.abs(point.x-b.series[index].x)<1e-10);
 const overlay=compatible&&b?a.series.map((point,index)=>({x:point.x,pinned:point.probability,current:b.series[index].probability})):[];
 const maxDifference=compatible&&b?Math.max(...a.series.map((point,index)=>Math.abs(point.probability-b.series[index].probability))):null;
 const left=flattened(pinned.config),right=flattened(current?.config);
 const changes=b?Array.from(new Set([...Object.keys(left),...Object.keys(right)])).filter(key=>left[key]!==right[key]):[];
 return <section className="panel connected-comparison" data-testid="connected-comparison" aria-label="Saved run comparison">
  <div className="panel-title"><div><span className="eyebrow">COMPARE SAVED EVIDENCE</span><h2>Pinned experiment comparison</h2></div><button className="button small" onClick={clear} aria-label="Clear pinned comparison">Clear pin</button></div>
  <p className="connected-help">Pinned <code>{pinned.id.slice(0,8)}</code> · {a.sequence} · {new Date(pinned.created_at).toLocaleString()}{b&&<>. Current <code>{current!.id.slice(0,8)}</code> · {b.sequence}.</>} Pinning keeps an immutable snapshot in this open session; both runs remain in History.</p>
  {!b||sameRun?<p className="connected-help">Change a control and acquire another experiment to compare its returned evidence with the pinned run.</p>:<>
   {compatible?<><p className="connected-help" data-testid="comparison-difference">Maximum density difference: <strong>{maxDifference!.toFixed(6)}</strong>. Both traces share the same protocol and sample coordinates. This difference is between deterministic model predictions, not a significance test of sampled counts.</p><div className="connected-chart" data-testid="comparison-overlay" role="img" aria-label="Pinned and current density predictions"><ResponsiveContainer width="100%" height={230}><LineChart data={overlay} margin={{top:10,right:10,bottom:22,left:0}}><CartesianGrid vertical={false} stroke="#263c4e" strokeDasharray="3 6"/><XAxis dataKey="x" type="number" domain={['dataMin','dataMax']} stroke="#8aa0b7" fontSize={10} label={{value:`${a.axes.x_label} (${a.axes.x_unit})`,position:'insideBottom',offset:-15,fill:'#91a9bc',fontSize:10}}/><YAxis domain={[0,1]} width={40} stroke="#8aa0b7" fontSize={10}/><Tooltip contentStyle={{background:'#101f2b',border:'1px solid #3a5669',fontSize:10}}/><Legend verticalAlign="top" wrapperStyle={{fontSize:10}}/><Line dataKey="pinned" name={`Pinned ${pinned.id.slice(0,8)}`} stroke="#c2a7ef" strokeDasharray="5 4" dot={false} isAnimationActive={false}/><Line dataKey="current" name={`Current ${current!.id.slice(0,8)}`} stroke="#6ed6cf" dot={false} isAnimationActive={false}/></LineChart></ResponsiveContainer></div></>:<p className="connected-stale">Different sweep axes, protocols or sample coordinates. Results are kept separate; no pointwise difference or overlay is calculated.</p>}
   <details className="connected-record-details" open><summary>Changed configuration ({changes.length})</summary>{changes.length?<div className="table-scroll"><table><thead><tr><th>Setting</th><th>Pinned</th><th>Current</th></tr></thead><tbody>{changes.map(key=><tr key={key}><td>{key}</td><td>{left[key]??'Not present'}</td><td>{right[key]??'Not present'}</td></tr>)}</tbody></table></div>:<p className="connected-help">The configurations match. Seeded measurements should reproduce within the same model and software versions.</p>}</details>
  </>}
 </section>;
}
