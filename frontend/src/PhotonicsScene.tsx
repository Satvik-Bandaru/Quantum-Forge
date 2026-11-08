import {ArrowDown,ArrowUpRight,Camera,MousePointer2} from 'lucide-react';
import type {OpticalComponent,PhotonicsConfig} from './types';
import studioPhoto from './assets/quantum-photonics-studio.png';
import './photonics-scene.css';

const stations=[
 {id:'source',ids:['source'],label:'Laser',aria:'Explore laser source',x:12,y:58},
 {id:'bs1',ids:['bs1','bs2'],label:'Splitters',aria:'Explore beam splitters',x:34,y:47},
 {id:'upper_mirror',ids:['upper_mirror','lower_mirror'],label:'Mirrors',aria:'Explore mirrors',x:55,y:45},
 {id:'phase',ids:['phase'],label:'Phase',aria:'Explore phase shifter',x:66,y:60},
 {id:'detector0',ids:['detector0','detector1'],label:'Detection',aria:'Explore power meters',x:42,y:70},
] as const;

const explanations:Record<OpticalComponent,{name:string;description:string;try:string}>={
 source:{name:'Coherent source',description:'The laser supplies a steady light wave. Its power sets how much light enters the experiment; its wavelength determines how quickly phase changes with path length.',try:'Start with 1 mW, then change the source power and compare the two output powers.'},
 bs1:{name:'Beam splitter 1',description:'The first beam splitter sends light into two paths. A 50:50 splitter gives each path equal power, so the waves can interfere strongly when they meet again.',try:'Change BS1 power transmissivity to send more light into one arm.'},
 bs2:{name:'Beam splitter 2',description:'The second beam splitter recombines the two paths. The waves can add at one output and cancel at the other, depending on their relative phase.',try:'Keep both splitters at 0.5, then change the phase to exchange the bright and dark outputs.'},
 upper_mirror:{name:'Upper mirror',description:'Mirrors redirect the beam around the bench and bring the two paths back together. This model uses ideal mirrors; arm transmission controls light lost along each path.',try:'Reduce the upper-arm transmission and see how unequal paths reduce the interference contrast.'},
 lower_mirror:{name:'Lower mirror',description:'This mirror steers the lower path toward the recombiner. The mirror is ideal in this model; lower-arm transmission represents losses along that path.',try:'Block one arm completely to remove the phase-dependent interference fringe.'},
 phase:{name:'Phase shifter',description:'A phase shifter changes where one wave is in its cycle when the paths meet. In-step waves add; out-of-step waves can cancel. This steers power between the two outputs.',try:'With a balanced, lossless bench, change φ from 0 to π and run again. D0 and D1 exchange brightness.'},
 detector0:{name:'Power meter D0',description:'Detection turns outgoing light into a reading. In this simulator, D0 and D1 measure optical power in mW, with optional electronic noise.',try:'Compare the calculated power with the repeated meter readings. The detector equipment in the reference image is illustrative.'},
 detector1:{name:'Power meter D1',description:'D1 reads the other output. With no optical loss, the two calculated output powers add up to the source power even as their individual brightness changes.',try:'Change the phase, rerun the experiment, and compare both output powers below.'},
};

function setting(selected:OpticalComponent,config:PhotonicsConfig){
 if(selected==='source')return `${config.power_mw} mW · ${config.wavelength_nm} nm`;
 if(selected==='bs1'||selected==='bs2')return `${(100*config[selected==='bs1'?'splitter1':'splitter2']).toFixed(0)}% power transmissivity`;
 if(selected==='phase')return `Phase-shifter setting ${(config.phase_rad/Math.PI).toFixed(2)}π`;
 if(selected==='upper_mirror'||selected==='lower_mirror')return `${(100*config[selected==='upper_mirror'?'upper_transmission':'lower_transmission']).toFixed(0)}% arm transmission`;
 return `Meter noise σ = ${config.meter_noise_mw} mW`;
}

export default function PhotonicsScene({selected,select,adjust,config,busy}:{selected:OpticalComponent;select:(id:OpticalComponent)=>void;adjust:()=>void;config:PhotonicsConfig;busy:boolean}){
 const active=stations.find(station=>(station.ids as readonly string[]).includes(selected))!;
 const explanation=explanations[selected];
 return <div className="ph-scene" data-testid="photonics-scene">
  <div className="ph-photo-stage"><img className="ph-studio-photo" src={studioPhoto} alt="Quantum Forge photonics studio reference" width="1448" height="1086" fetchPriority="high"/><div className="ph-photo-heading"><span><Camera size={13}/>EXPLORE THE PHOTONICS STUDIO</span><p>Tap the equipment. Follow the light.</p></div>
   {stations.map((station,index)=><button key={station.id} className={`ph-hotspot ${station===active?'selected':''}`} style={{left:`${station.x}%`,top:`${station.y}%`}} aria-label={station.aria} aria-pressed={station===active} onClick={()=>select(station.id)}><b>{index+1}</b><span>{station.label}</span></button>)}
   <span className="ph-reference-label">Visual reference · not a live instrument feed</span>
  </div>
  <div className="ph-equipment-steps" aria-label="Follow the optical experiment">{stations.map((station,index)=><button key={station.id} aria-pressed={station===active} className={station===active?'selected':''} onClick={()=>select(station.id)}><span>0{index+1}</span>{station.label}</button>)}</div>
  <div className="ph-component-guide" data-testid="photonics-component-guide"><div className="ph-equipment-detail"><img src={studioPhoto} alt={`Equipment detail for ${explanation.name} from the reference image`} style={{transform:`translate(-${active.x}%,-${active.y}%)`}}/></div><div className="ph-guide-copy"><span className="ph-guide-eyebrow"><MousePointer2 size={12}/>UNDERSTAND THE EQUIPMENT</span><h3>{explanation.name}</h3><p>{explanation.description}</p><p className="ph-try"><b>Try it:</b> {explanation.try}</p><div className="ph-current-setting"><span>{config.bench_components.includes(selected)?'YOUR SETUP':'NOT PLACED ON YOUR BENCH'}</span><strong>{setting(selected,config)}</strong></div><button className="button small" disabled={busy} onClick={adjust}>Adjust this component<ArrowDown size={13}/></button></div></div>
  <div className="ph-photo-caption"><span>The image’s screens and labels are illustrative. Your classical MZI calculations and power readings appear below.</span><a href={studioPhoto} target="_blank" rel="noreferrer">View full image<ArrowUpRight size={12}/></a></div>
 </div>
}
