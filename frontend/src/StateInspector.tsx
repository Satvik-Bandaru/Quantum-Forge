import {useState} from 'react';
import {Bloch,ProbabilityChart} from './charts';
import type {Snapshot,Result} from './types';

export function Registers({state}:{state:Snapshot|Result}){
 return <div className="table-scroll"><table className="register-table"><thead><tr><th>Qubit</th><th>P(|1⟩)</th><th>Bloch x / y / z</th><th>Purity</th><th>Entropy (bits)</th></tr></thead><tbody>{state.registers?.map(r=><tr key={r.qubit}><td><code>q{r.qubit}</code></td><td><div className="register-prob"><span style={{width:`${r.p1*100}%`}}/></div><code>{(r.p1*100).toFixed(1)}%</code></td><td><code>{r.bloch.map(v=>Math.abs(v)<1e-8?'0.000':v.toFixed(3)).join(' / ')}</code></td><td>{r.purity.toFixed(3)}</td><td><span className={r.entropy>.5?'entropy-badge':''}>{r.entropy.toFixed(3)}</span></td></tr>)}</tbody></table></div>;
}

export function Amplitudes({state,qubits}:{state:Snapshot|Result;qubits:number}){
 const [showZero,setShowZero]=useState(false);
 const amplitudes=state.amplitudes||[],probabilities=state.probabilities||[];
 return <><div className="row between amplitude-controls"><p className="caption">Complex amplitudes include phase. Probabilities alone can hide interference.</p><label className="check-label"><input type="checkbox" checked={showZero} onChange={e=>setShowZero(e.target.checked)}/>Include zero states</label></div><div className="amplitude-table table-scroll"><table><thead><tr><th>Basis state</th><th>Amplitude</th><th>Probability</th><th>Phase</th></tr></thead><tbody>{amplitudes.map((a,i)=>({a,i,p:probabilities[i]})).filter(x=>showZero||x.p>1e-9).map(({a,i,p})=>{const phase=Math.atan2(a[1],a[0]);return <tr key={i}><td><code>|{i.toString(2).padStart(qubits,'0')}⟩</code></td><td><code>{a[0].toFixed(4)} {a[1]<0?'−':'+'} {Math.abs(a[1]).toFixed(4)}i</code></td><td>{(p*100).toFixed(3)}%</td><td>{p>1e-9?<span className="phase-cell"><i className="phase-wheel"><i style={{transform:`rotate(${-phase*180/Math.PI}deg)`}}/></i><code>{phase.toFixed(3)} rad</code></span>:'—'}</td></tr>})}</tbody></table></div></>;
}

export default function StateInspector({state,qubits,counts,shots}:{state:Snapshot|Result;qubits:number;counts?:Record<string,number>;shots?:number}){
 const [tab,setTab]=useState('Register');
 return <section className="panel"><div className="panel-title"><div><span className="eyebrow">IDEAL QUANTUM MEMORY</span><h2>State inspector</h2></div><span className="tag">q₀ is the leftmost bit</span></div><div className="inspector-tabs">{['Register','Amplitudes','Bloch sphere',...(counts?['Final readout']:[])].map(t=><button className={tab===t?'selected':''} key={t} onClick={()=>setTab(t)}>{t}</button>)}</div>{tab==='Register'&&<><Registers state={state}/><p className="caption">Entropy describes each qubit versus the remaining register in this pure ideal state. A Bell pair has local purity 0.5 and entropy 1 bit.</p></>}{tab==='Amplitudes'&&<Amplitudes state={state} qubits={qubits}/>} {tab==='Bloch sphere'&&<div className="inspector-bloch"><Bloch vectors={state.bloch||[]}/></div>}{tab==='Final readout'&&counts&&<><p className="notice">Final program readout, independent of the selected debugger step. Histograms include configured noise; the ideal bars are the final ideal state.</p><ProbabilityChart probabilities={('snapshots' in state&&state.snapshots?.at(-1)?.probabilities)||state.probabilities||[]} counts={counts} qubits={qubits} shots={shots||1024}/></>}</section>;
}
