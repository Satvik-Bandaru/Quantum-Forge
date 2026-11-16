import {Component,Suspense,lazy,useEffect,useRef,useState} from 'react';
import type {ErrorInfo,ReactNode} from 'react';
import {ArrowRight,Atom,Camera,CheckCircle2,ChevronRight,Compass,Cpu,ExternalLink,FlaskConical,Image as ImageIcon,Info,Loader2,Maximize2,RotateCcw,SlidersHorizontal} from 'lucide-react';
import type {Page,Run} from '../types';
import type {InstrumentId} from '../connected/types';
import {labPhotos} from './photos';
import type {LabPhoto} from './photos';

const LabScene=lazy(()=>import('./LabScene'));
type StationId='quantum'|'optics'|'control'|'optimization'|'research';
type View='overview'|StationId;
const stations:{id:StationId;number:string;name:string;label:string;short:string;description:string;detail:string;links:Page[]}[]=[
 {id:'quantum',number:'01',name:'Quantum computer',label:'Dilution refrigerator',short:'Quantum computing',description:'Explore the thermal stages, coaxial wiring and sample chamber of a superconducting-qubit system.',detail:'The exposed refrigerator is an educational cutaway. Its thermal stages and wiring illustrate how a chip is isolated from environmental noise. No temperature or hardware status is being measured here.',links:['Connected Instruments','Virtual Computer','Circuit Builder','Error Correction']},
 {id:'optics',number:'02',name:'Optical bench',label:'Photonics & interferometry',short:'Photonics',description:'Follow the optical path through a laser source, precision mounts, splitters and detectors.',detail:'Open the existing Photonics Lab to change the phase and loss of a classical Mach–Zehnder model. The 3D bench explains equipment; the functional module computes the optical fields.',links:['Photonics Lab','Quantum Optics']},
 {id:'control',number:'03',name:'Qubit control workstation',label:'Control electronics',short:'Qubit control',description:'Inspect the racks and workstation used to prepare, drive and read out quantum systems.',detail:'The rack front panels are educational instrument illustrations. Open microwave controls to configure the connected drive and pulse path, or inspect readout to see results returned by the Python simulator. Physical Quantum Lab remains available separately.',links:['Connected Instruments','Physical Quantum Lab']},
 {id:'optimization',number:'04',name:'Optimization workstation',label:'Optimization & algorithms',short:'Optimization',description:'Turn a binary decision problem into an energy model and compare executed solvers.',detail:'QUBO and Optimization Lab use local classical and quantum-circuit simulators. Timings are CPU measurements, not evidence of quantum speedup.',links:['QUBO Lab','Optimization Lab']},
 {id:'research',number:'05',name:'Research console',label:'Experiments & evidence',short:'Research',description:'Prepare experiments, compare their predictions and return to your saved scientific record.',detail:'Every submitted simulation is recorded by the local Python service. History preserves its inputs, result, seed, software versions and completion status.',links:['Experiments','History']},
];

class SceneBoundary extends Component<{children:ReactNode;onFailure:(message:string)=>void},{failed:boolean}>{
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true}}
 componentDidCatch(error:Error,info:ErrorInfo){this.props.onFailure(error.message);console.warn('Quantum lab scene failed',error.message,info.componentStack)}
 render(){return this.state.failed?null:this.props.children}
}

function ScenePlaceholder({message}:{message:string}){return <div className="ml-scene-placeholder"><Compass size={30}/><p>{message}</p><span>The equipment directory and experiments remain available below.</span></div>}

function Gallery({photo,setPhoto}:{photo:LabPhoto;setPhoto:(photo:LabPhoto)=>void}){
 const [filter,setFilter]=useState<'all'|'photograph'|'illustration'>('all');
 const [failed,setFailed]=useState<string[]>([]);
 return <section className="ml-gallery" id="lab-photo-gallery" aria-label="Laboratory Photo Gallery">
  <div className="ml-section-heading"><div><span className="ml-eyebrow">THE HARDWARE, IN CONTEXT</span><h2>Photo Gallery</h2></div><div className="ml-gallery-filters" aria-label="Image category">{(['all','photograph','illustration'] as const).map(value=><button key={value} aria-pressed={filter===value} onClick={()=>setFilter(value)}>{value==='all'?'All images':value==='photograph'?'Real photographs':'Concept references'}</button>)}</div></div>
  <div className="ml-gallery-feature"><div className="ml-gallery-image">{failed.includes(photo.id)?<p role="alert">Image unavailable: {photo.src}</p>:<img key={photo.id} src={photo.src} alt={photo.title} onError={()=>setFailed(old=>[...old,photo.id])}/>}</div><div className="ml-gallery-caption"><span className={`ml-image-kind ${photo.kind}`}>{photo.kind==='photograph'?'REAL LABORATORY PHOTOGRAPH':'ILLUSTRATIVE CONCEPT IMAGE'}</span><h3>{photo.title}</h3><p>{photo.description}</p><p className="ml-credit">{photo.credit}</p>{photo.source.startsWith('https://')&&<a href={photo.source} target="_blank" rel="noreferrer">Source & attribution <ExternalLink size={13}/></a>}<p className="ml-image-note">This image is reference material. It is not a live camera feed or a source of simulation measurements.</p></div></div>
  <div className="ml-gallery-thumbs">{labPhotos.filter(p=>filter==='all'||p.kind===filter).map(p=><button key={p.id} aria-label={`View image: ${p.title}`} aria-pressed={photo.id===p.id} onClick={()=>setPhoto(p)}><img src={p.src} alt="" loading="lazy"/><span>{p.title}<small>{p.kind==='photograph'?'Photograph':'Concept reference'}</small></span></button>)}</div>
 </section>
}

function BellResult({run,openRun,navigate}:{run:Run;openRun:(id:string)=>void;navigate:(page:Page)=>void}){
 if(run.status==='running')return <div className="ml-bell-pending" role="status"><Loader2 size={15} className="spin"/><span>{run.progress||'Executing Bell experiment in Python…'}</span></div>;
 if(run.status!=='completed'||!run.result)return <div className="ml-bell-error" role="alert">Run {run.status}: {run.error||'No completed measurement returned.'}</div>;
 const result=run.result,shots=result.shots||0;
 return <section className="ml-bell-result" data-testid="bell-result" data-run-id={run.id} aria-label="Saved Bell experiment results">
  <div className="ml-result-heading"><CheckCircle2 size={16}/><b>Completed · saved to History</b></div>
  <p>Actual sampled counts from the Python backend</p>
  <div className="ml-counts">{['00','01','10','11'].map((state,i)=>{const count=result.counts?.[state]??0;return <div key={state}><code>|{state}⟩</code><div className="ml-count-track"><span style={{width:`${shots?100*count/shots:0}%`}}/></div><b data-testid={`bell-count-${state}`}>{count}</b><small>ideal {((result.probabilities?.[i]??0)*100).toFixed(1)}%</small></div>})}</div>
  <dl><div><dt>Shots</dt><dd>{shots.toLocaleString()}</dd></div><div><dt>Seed</dt><dd>{result.seed}</dd></div><div><dt>Compute time</dt><dd>{result.runtime_s.toFixed(4)} s</dd></div></dl>
  <p className="ml-result-backend">{result.backend} · Qiskit Aer {result.versions['qiskit-aer']}</p>
  <code className="ml-run-id">{run.id}</code>
  <div className="ml-result-actions"><button onClick={()=>openRun(run.id)}>Inspect saved run <ArrowRight size={13}/></button><button onClick={()=>navigate('History')}>History</button></div>
  <p className="ml-result-note">Counts are sampled simulation outcomes; ideal probabilities come from the statevector. This is CPU simulation, not a physical QPU measurement.</p>
 </section>
}

export default function MainQuantumLab({navigate,openInstrument,connected,busy,onStartBell,bellRun,openRun}:{navigate:(page:Page)=>void;openInstrument:(id:InstrumentId)=>void;connected:boolean;busy:boolean;onStartBell:()=>Promise<void>;bellRun:Run|null;openRun:(id:string)=>void}){
 const [selected,setSelected]=useState<StationId|null>(null),[view,setView]=useState<View>('overview'),[viewRequest,setViewRequest]=useState(0);
 const [lowGraphics,setLowGraphics]=useState(()=>localStorage.getItem('qf-lab-graphics')!=='high');
 const [ready,setReady]=useState(false),[failure,setFailure]=useState(''),[sceneKey,setSceneKey]=useState(0),[sceneEnabled,setSceneEnabled]=useState(true);
 const [galleryOpen,setGalleryOpen]=useState(false),[photo,setPhoto]=useState<LabPhoto>(labPhotos[0]);
 const [submitting,setSubmitting]=useState(false);
 const galleryRef=useRef<HTMLDivElement>(null),sceneRef=useRef<HTMLDivElement>(null);
 const station=stations.find(s=>s.id===selected);
 useEffect(()=>localStorage.setItem('qf-lab-graphics',lowGraphics?'low':'high'),[lowGraphics]);
 function select(id:string){if(stations.some(s=>s.id===id))setSelected(id as StationId)}
 function camera(next:View){setView(next);setViewRequest(r=>r+1)}
 function showGallery(next?:LabPhoto){if(next)setPhoto(next);setGalleryOpen(true);requestAnimationFrame(()=>galleryRef.current?.scrollIntoView({behavior:'smooth',block:'start'}))}
 async function runBell(){setSubmitting(true);try{await onStartBell()}finally{setSubmitting(false)}}
 async function retryScene(){try{const scene=await import('./LabScene');scene.clearLabModels();setFailure('');setReady(false);setSceneEnabled(true);setSceneKey(k=>k+1)}catch(error){setFailure(`Could not reload 3D assets: ${(error as Error).message}`)}}
 const preview=station?(labPhotos.find(p=>p.kind==='photograph'&&p.equipment.includes(station.id))||labPhotos.find(p=>p.equipment.includes(station.id))):undefined;
 return <div className="main-quantum-lab">
  <div className="ml-page-heading"><div><span className="ml-eyebrow">QUANTUM FORGE / THE RESEARCH FACILITY</span><h1>Main Quantum Laboratory</h1><p>Explore the equipment. Follow your curiosity into a working experiment.</p></div><button className="button" onClick={()=>showGallery()} aria-expanded={galleryOpen} aria-controls="lab-photo-gallery"><ImageIcon size={16}/>Photo Gallery</button></div>
  <div className="ml-toolbar"><div className="ml-connection"><span className={`dot ${connected?'':'offline'}`}/>{connected?'Python simulator connected':'Python simulator disconnected'}<span className="ml-divider"/>Educational 3D facility</div><label className="ml-graphics"><SlidersHorizontal size={14}/><input type="checkbox" checked={lowGraphics} onChange={e=>setLowGraphics(e.target.checked)} aria-label="Low graphics mode"/>Low graphics</label></div>
  <div className={`ml-workspace ${selected?'has-selection':''}`}>
   <div className="ml-viewport-column">
    <div className="ml-scene" ref={sceneRef} data-testid="lab-canvas" data-graphics={lowGraphics?'low':'high'}>
     {sceneEnabled&&!failure?<SceneBoundary key={sceneKey} onFailure={setFailure}><Suspense fallback={<ScenePlaceholder message="Loading laboratory models…"/>}><LabScene selected={selected} onSelect={select} lowGraphics={lowGraphics} view={view} viewRequest={viewRequest} onReady={()=>setReady(true)} onError={setFailure}/></Suspense></SceneBoundary>:<ScenePlaceholder message={failure?`3D view unavailable: ${failure}`:'3D view paused. Use the equipment directory to explore.'}/>}
     <div className="ml-scene-badge"><span className="ml-small-dot"/>{ready&&!failure&&sceneEnabled?'3D environment ready':failure?'3D load failed':sceneEnabled?'Loading 3D environment':'3D paused'}</div>
     <div className="ml-scene-title"><span>01 / MAIN FACILITY</span><b>A place for discovery.</b></div>
    </div>
    <div className="ml-camera-bar"><span><Compass size={14}/>Drag to orbit · scroll to zoom · WASD to move</span><div><button aria-label="Reset laboratory view" onClick={()=>camera('overview')}><RotateCcw size={14}/>Reset view</button><button onClick={()=>{setSceneEnabled(v=>!v);setReady(false)}}>{sceneEnabled?'Pause 3D':'Resume 3D'}</button>{failure&&<button onClick={retryScene}>Retry 3D</button>}</div></div>
    <div className="ml-station-directory" aria-label="Equipment directory">{stations.map(s=><button key={s.id} aria-label={`Select ${s.name}`} aria-pressed={selected===s.id} onClick={()=>select(s.id)}><span>{s.number}</span><b>{s.short}</b><ChevronRight size={13}/></button>)}</div>
    <div className="ml-scene-footnote"><Info size={14}/><p>{lowGraphics?'Low graphics: demand rendering, pixel ratio 1, no real-time shadows.':'Detailed mode: higher pixel density and lighting quality.'} Equipment models explain hardware; numerical results appear only after an experiment runs.</p></div>
   </div>
   <aside className="ml-inspector" aria-label="Equipment information" data-testid="equipment-inspector">
    {station?<><div className="ml-inspector-heading"><span className="ml-station-number">{station.number}</span><span className="ml-eyebrow">EQUIPMENT EXPLORER</span></div><h2>{station.name}</h2><span className="ml-equipment-label">{station.label}</span><p className="ml-equipment-description">{station.description}</p><button className="ml-focus-button" onClick={()=>camera(station.id)}><Maximize2 size={14}/>Move closer</button>
      {preview&&<button className="ml-context-photo" onClick={()=>showGallery(preview)}><img src={preview.src} alt={preview.title}/><span><Camera size={13}/>{preview.kind==='photograph'?'Real hardware photograph':'Illustrative reference'}<ArrowRight size={13}/></span></button>}
      {(station.id==='quantum'||station.id==='control')&&<div className="ml-module-links"><span className="ml-eyebrow">CONFIGURE CONNECTED EQUIPMENT</span>{station.id==='quantum'?<><button onClick={()=>openInstrument('cryostat')}>Configure refrigerator<ArrowRight size={15}/></button><button onClick={()=>openInstrument('device')}>Configure quantum device<ArrowRight size={15}/></button></>:<><button onClick={()=>openInstrument('microwave')}>Configure microwave controls<ArrowRight size={15}/></button><button onClick={()=>openInstrument('readout')}>Inspect readout and results<ArrowRight size={15}/></button></>}</div>}
      <div className="ml-module-links"><span className="ml-eyebrow">OPEN A WORKING MODULE</span>{station.links.map(page=><button key={page} onClick={()=>page==='Connected Instruments'?openInstrument(station.id==='quantum'?'cryostat':'microwave'):navigate(page)}>{page}<ArrowRight size={15}/></button>)}</div>
      {station.id==='quantum'&&<section className="ml-bell"><div><Atom size={16}/><h3>Your first experiment</h3></div><p>Prepare a Bell pair with H → CX and measure 1,024 shots.</p><code>|Φ⁺⟩ = (|00⟩ + |11⟩) / √2</code><button className="ml-run-button" disabled={!connected||busy||submitting} onClick={runBell}>{busy||submitting?<Loader2 size={15} className="spin"/>:<FlaskConical size={15}/>}Run Bell experiment</button><small>{!connected?'Connect the Python service to execute.':busy?'A simulation is running.':'Local Qiskit Aer · seed 42 · zero configured noise'}</small>{bellRun&&<BellResult run={bellRun} openRun={openRun} navigate={navigate}/>}</section>}
      <details className="ml-model-note"><summary>About this educational model</summary><p>{station.detail}</p></details>
    </>:<div className="ml-welcome"><span className="ml-welcome-icon"><Cpu size={26}/></span><span className="ml-eyebrow">STEP INSIDE THE LAB</span><h2>Where would you like to begin?</h2><p>Click a piece of equipment in the room, or choose a station below the 3D view.</p><div className="ml-welcome-tip"><Atom size={21}/><div><b>Start with a Bell pair</b><p>Select the quantum computer to prepare two entangled qubits on the local simulator.</p></div></div><div className="ml-evidence-key"><span><i className="model"/>3D models: educational hardware</span><span><i className="photo"/>Photos: attributed reference material</span><span><i className="measurement"/>Results: executed Python simulations</span></div>{bellRun&&<button className="button" onClick={()=>select('quantum')}>Return to Bell experiment<ArrowRight size={13}/></button>}</div>}
   </aside>
  </div>
  <div className="ml-below"><span><CheckCircle2 size={15}/>Five connected research stations</span><button onClick={()=>showGallery()}><Camera size={15}/>Explore laboratory photographs<ArrowRight size={14}/></button></div>
  <div ref={galleryRef}>{galleryOpen&&<Gallery photo={photo} setPhoto={setPhoto}/>}</div>
 </div>
}
