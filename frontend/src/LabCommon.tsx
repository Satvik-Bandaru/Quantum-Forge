import {useRef,useState} from 'react';
import {Download,Bookmark,CheckCircle2,Info} from 'lucide-react';
import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,CartesianGrid,Tooltip,Legend,ReferenceLine} from 'recharts';
import {Exports} from './Optimization';
import {download} from './api';
import type {LabResult,Run} from './types';

export function Scope({data,x,lines,xLabel,yLabel,reference}:{data:Record<string,number>[];x:string;lines:{key:string;name:string;color:string;dash?:string}[];xLabel:string;yLabel:string;reference?:number}){
 return <div className="lab-scope"><div className="scope-axis-label">{yLabel}</div><ResponsiveContainer width="100%" height={260}><LineChart data={data} margin={{top:12,right:18,bottom:23,left:0}}><CartesianGrid vertical={false} stroke="#24364b" strokeDasharray="3 5"/><XAxis dataKey={x} type="number" domain={['dataMin','dataMax']} tickFormatter={v=>Number(v).toFixed(2)} fontSize={9} stroke="#7187a4" label={{value:xLabel,position:'insideBottom',offset:-15,fill:'#7b91ad',fontSize:10}}/><YAxis fontSize={9} stroke="#7187a4" width={45} tickFormatter={v=>Number(v).toFixed(2)}/><Tooltip labelFormatter={v=>`${Number(v).toFixed(4)} ${xLabel}`} formatter={(v,name)=>[Number(v).toFixed(6),name]} contentStyle={{background:'#111d2d',border:'1px solid #374964',borderRadius:7,fontSize:11}}/><Legend verticalAlign="top" wrapperStyle={{fontSize:9,paddingBottom:15}}/>{lines.map(l=><Line key={l.key} dataKey={l.key} name={l.name} stroke={l.color} strokeWidth={1.8} dot={false} isAnimationActive={false} strokeDasharray={l.dash}/>)}{reference!==undefined&&<ReferenceLine x={reference} stroke="#a78bd2" strokeDasharray="3 3"/>}</LineChart></ResponsiveContainer></div>;
}

export function LabMetric({label,value,unit}:{label:string;value:unknown;unit?:string}){
 const text=value==null?'—':typeof value==='number'?(Math.abs(value)<1e-10?'0':Math.abs(value)<.0001?value.toExponential(3):value.toFixed(4)):String(value);
 return <div className="lab-metric"><span>{label}</span><b>{text}<small>{unit}</small></b></div>;
}

export function Evidence({run}:{run:Run}){
 const result=run.result as unknown as LabResult;
 const ref=useRef<HTMLDivElement>(null);
 function exportSvg(){const svg=ref.current?.parentElement?.parentElement?.querySelector('.recharts-surface');if(svg){download(`${run.kind}-plot.svg`,new XMLSerializer().serializeToString(svg),'image/svg+xml')}}
 return <><div ref={ref} className="lab-evidence-row"><span className="tag"><CheckCircle2 size={12}/>Saved run {run.id.slice(0,8)}</span><Exports run={run}/><button className="button small" onClick={exportSvg}><Download size={13}/>Plot SVG</button></div><details className="lab-model-record"><summary>Model, initial conditions, software and raw evidence</summary><pre>{JSON.stringify({configuration:run.config,backend:result.backend,versions:result.versions,model:result.model,assumptions:result.assumptions,checks:result.checks,metrics:result.metrics},null,2)}</pre></details><div className="lab-limitations"><h3><Info size={15}/>Model boundaries</h3>{result.limitations.map(t=><p key={t}>{t}</p>)}</div></>;
}

export function usePinned(run:Run|null){const [pinned,setPinned]=useState<Run|null>(null);return {pinned,pin:()=>{if(run)setPinned(run)},clear:()=>setPinned(null)}}
export function PinControl({run,pinned,pin,clear}:{run:Run|null;pinned:Run|null;pin:()=>void;clear:()=>void}){return <div className="row lab-compare"><button className="button small" disabled={!run} onClick={pin}><Bookmark size={13}/>Pin run for comparison</button>{pinned&&<><span className="caption">Reference {pinned.id.slice(0,8)}</span><button className="text-button" onClick={clear}>Clear</button></>}</div>}
