import {test,expect,type Page} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';
test.use({actionTimeout:15000});

async function openBench(page:Page){
 await page.goto('/');
 if(await page.getByRole('button',{name:'Toggle navigation',exact:true}).isVisible())await page.getByRole('button',{name:'Toggle navigation',exact:true}).click();
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:'Connected Instruments',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Connected Instruments',exact:true})).toBeVisible();
 await expect(page.getByTestId('apparatus-status')).toHaveText('Ready to acquire');
}
async function acquire(page:Page){
 const submitted=page.waitForResponse(response=>response.url().endsWith('/api/jobs')&&response.request().method()==='POST');
 await page.getByRole('button',{name:'Run connected experiment',exact:true}).click();
 const response=await submitted;expect(response.status()).toBe(202);
 const job=await response.json();expect(job.kind).toBe('connected');
 await expect(page.getByTestId('connected-result')).toHaveAttribute('data-run-id',job.id,{timeout:60000});
 const run=await(await page.request.get('/api/history/'+job.id)).json();
 expect(run.status).toBe('completed');
 expect(run.result.series.length).toBeGreaterThan(1);
 expect(run.result.checks.every((check:{passed:boolean})=>check.passed)).toBe(true);
 return run;
}
function difference(a:{series:{probability:number}[]},b:{series:{probability:number}[]}){return Math.max(...a.series.map((row,index)=>Math.abs(row.probability-b.series[index].probability)))}

test('connected acquisition responds to real temperature, source power and detuning changes',async({page})=>{
 await page.setViewportSize({width:1512,height:1050});await openBench(page);
 await page.getByLabel('Sample points',{exact:true}).fill('51');
 await page.getByLabel('Sweep stop',{exact:true}).fill('0.1');
 const baseline=await acquire(page);
 await page.getByRole('button',{name:'Select Microwave source',exact:true}).click();
 await page.getByLabel('Source power (dBm)',{exact:true}).fill('-10');
 await expect(page.getByTestId('stale-connected-result')).toBeVisible();
 const lowPower=await acquire(page);expect(difference(baseline.result,lowPower.result)).toBeGreaterThan(.2);
 await page.getByLabel('Source power (dBm)',{exact:true}).fill('0');
 await page.getByLabel('Source frequency (GHz)',{exact:true}).fill('5.015');
 const detuned=await acquire(page);expect(difference(baseline.result,detuned.result)).toBeGreaterThan(.2);
 await page.getByLabel('Source frequency (GHz)',{exact:true}).fill('5');
 await page.getByRole('button',{name:'Select Dilution refrigerator',exact:true}).click();
 await page.getByLabel('Base temperature (K)',{exact:true}).fill('0.08');
 const warm=await acquire(page);expect(warm.result.series[0].probability-baseline.result.series[0].probability).toBeGreaterThan(.03);
 await expect(page.getByText('Density prediction',{exact:true})).toBeVisible();
 await expect(page.getByText('Seeded finite-shot measurements',{exact:true})).toBeVisible();
 mkdirSync('../docs/verification',{recursive:true});
 writeFileSync('../docs/verification/nexus-connected-controls.json',JSON.stringify({baseline,lowPower,detuned,warm,maximumProbabilityDifference:{power:difference(baseline.result,lowPower.result),detuning:difference(baseline.result,detuned.result)},initialThermalPopulationDifference:warm.result.series[0].probability-baseline.result.series[0].probability},null,2)+'\n');
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:'../docs/screenshots/connected-instruments-desktop.png',fullPage:true});
});

test('missing ports and disabled instruments prevent acquisition with explicit computed reasons',async({page})=>{
 await openBench(page);
 const link=page.getByRole('checkbox',{name:'Connect microwave:rf to device:drive',exact:true});
 await link.uncheck();
 await expect(page.getByTestId('apparatus-status')).toHaveText('Acquisition blocked');
 await expect(page.getByRole('button',{name:'Run connected experiment',exact:true})).toBeDisabled();
 await expect(page.getByTestId('apparatus-issues')).toContainText(/microwave|drive|connection/i);
 await link.check();
 await expect(page.getByTestId('apparatus-status')).toHaveText('Ready to acquire');
 await page.getByRole('button',{name:'Select Binary readout',exact:true}).click();
 await page.getByRole('checkbox',{name:'Instrument enabled',exact:true}).uncheck();
 await expect(page.getByTestId('apparatus-status')).toHaveText('Acquisition blocked');
 await expect(page.getByTestId('apparatus-issues')).toContainText(/readout.*disabled|disabled.*readout/i);
 await page.getByRole('checkbox',{name:'Instrument enabled',exact:true}).check();
 await page.getByLabel('Injected fault',{exact:true}).selectOption('injected');
 await expect(page.getByTestId('apparatus-issues')).toContainText(/fault/i);
 await expect(page.getByRole('button',{name:'Run connected experiment',exact:true})).toBeDisabled();
 await page.getByLabel('Injected fault',{exact:true}).selectOption('none');
 await expect(page.getByTestId('apparatus-status')).toHaveText('Ready to acquire');
});

test('saved apparatus survives reload, detects revision conflicts and preserves History snapshots',async({page,baseURL})=>{
 const original=await(await page.request.get('/api/apparatus')).json();
 try{
  await openBench(page);
  await page.getByRole('button',{name:'Select Microwave source',exact:true}).click();
  await page.getByLabel('Source power (dBm)',{exact:true}).fill('-3');
  await page.getByRole('button',{name:'Save apparatus',exact:true}).click();
  await expect(page.getByTestId('apparatus-save-state')).toContainText('Saved apparatus');
  const historical=await acquire(page);
  await page.reload();
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:'Connected Instruments',exact:true}).click();
  await page.getByRole('button',{name:'Select Microwave source',exact:true}).click();
  await expect(page.getByLabel('Source power (dBm)',{exact:true})).toHaveValue('-3');
  const saved=await(await page.request.get('/api/apparatus')).json();
  const external={...saved.config,microwave:{...saved.config.microwave,power_dbm:-5}};
  expect((await page.request.put('/api/apparatus',{headers:{Origin:new URL(baseURL!).origin},data:{revision:saved.revision,config:external}})).ok()).toBe(true);
  await page.getByLabel('Source power (dBm)',{exact:true}).fill('-7');
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:'Overview',exact:true}).click();
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:'Connected Instruments',exact:true}).click();
  await page.getByRole('button',{name:'Select Microwave source',exact:true}).click();
  await expect(page.getByLabel('Source power (dBm)',{exact:true})).toHaveValue('-7');
  await page.getByRole('button',{name:'Save apparatus',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('saved apparatus changed');
  await expect(page.getByLabel('Source power (dBm)',{exact:true})).toHaveValue('-7');
  await page.getByRole('button',{name:'Reload saved apparatus',exact:true}).click();
  await expect(page.getByLabel('Source power (dBm)',{exact:true})).toHaveValue('-5');
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:'History',exact:true}).click();
  await page.getByRole('row').filter({hasText:historical.id.slice(0,8)}).getByRole('button',{name:'Open experiment',exact:true}).click();
  await expect(page.getByTestId('connected-result')).toHaveAttribute('data-run-id',historical.id);
  await page.getByRole('button',{name:'Select Microwave source',exact:true}).click();
  await expect(page.getByLabel('Source power (dBm)',{exact:true})).toHaveValue('-3');
  await expect(page.getByTestId('stale-connected-result')).toHaveCount(0);
 }finally{
  const current=await(await page.request.get('/api/apparatus')).json();
  await page.request.put('/api/apparatus',{headers:{Origin:new URL(baseURL!).origin},data:{revision:current.revision,config:original.config}});
 }
});

test('all seven protocols produce backend evidence and calibration is labeled synthetic',async({page})=>{
 await openBench(page);
 await page.getByLabel('Sample points',{exact:true}).fill('51');
 for(const sequence of ['ramsey','echo','t1','frequency_sweep','amplitude_sweep','readout_calibration']){
  await page.getByLabel('Experiment sequence',{exact:true}).selectOption(sequence);
  const run=await acquire(page);expect(run.result.sequence).toBe(sequence);
  if(sequence==='readout_calibration'){
   expect(run.result.series).toHaveLength(2);
   await expect(page.getByTestId('connected-result')).toContainText(/synthetic|ideal preparation/i);
  }
 }
});

test('mobile instrument controls and port faults stay accessible without horizontal overflow',async({page})=>{
 await page.setViewportSize({width:390,height:844});await openBench(page);
 for(const instrument of ['Microwave source','Pulse sequencer','Quantum device','Binary readout','Dilution refrigerator']){
  await page.getByRole('button',{name:'Select '+instrument,exact:true}).click();
  await expect(page.getByRole('heading',{name:instrument,exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 }
 await page.getByRole('button',{name:'Advance cooldown by 180 seconds',exact:true}).click();
 await expect(page.getByLabel('Elapsed simulated time (s)',{exact:true})).toHaveValue('1980');
 await page.getByRole('checkbox',{name:'Connect cryostat:thermal to device:thermal',exact:true}).uncheck();
 await expect(page.getByTestId('apparatus-status')).toHaveText('Acquisition blocked');
 await expect(page.getByRole('button',{name:'Run connected experiment',exact:true})).toBeDisabled();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:'../docs/screenshots/connected-instruments-mobile.png',fullPage:true});
});

test('initial apparatus loading keeps controls disabled until the matching saved snapshot arrives',async({page,baseURL})=>{
 const original=await(await page.request.get('/api/apparatus')).json();
 const config={...original.config,microwave:{...original.config.microwave,power_dbm:-9}};
 expect((await page.request.put('/api/apparatus',{headers:{Origin:new URL(baseURL!).origin},data:{revision:original.revision,config}})).ok()).toBe(true);
 let release!:()=>void;
 const gate=new Promise<void>(resolve=>{release=resolve});
 await page.route('**/api/apparatus',async route=>{
  if(route.request().method()!=='GET'){await route.continue();return}
  const response=await route.fetch();await gate;await route.fulfill({response});
 });
 try{
  await page.goto('/');
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:'Connected Instruments',exact:true}).click();
  await expect(page.getByTestId('apparatus-save-state')).toHaveText('Loading apparatus record…');
  await page.getByRole('button',{name:'Select Microwave source',exact:true}).click();
  await expect(page.getByLabel('Source power (dBm)',{exact:true})).toBeDisabled();
  await expect(page.getByRole('checkbox',{name:'Connect microwave:rf to device:drive',exact:true})).toBeDisabled();
  await expect(page.getByLabel('Experiment sequence',{exact:true})).toBeDisabled();
  await expect(page.getByRole('button',{name:'Run connected experiment',exact:true})).toBeDisabled();
  await expect(page.getByRole('button',{name:'Reload saved apparatus',exact:true})).toBeEnabled();
  release();
  await expect(page.getByLabel('Source power (dBm)',{exact:true})).toBeEnabled();
  await expect(page.getByLabel('Source power (dBm)',{exact:true})).toHaveValue('-9');
  await expect(page.getByTestId('apparatus-save-state')).toHaveText('Saved apparatus');
  await expect(page.getByTestId('apparatus-status')).toHaveText('Ready to acquire');
 }finally{
  release();
  const current=await(await page.request.get('/api/apparatus')).json();
  await page.request.put('/api/apparatus',{headers:{Origin:new URL(baseURL!).origin},data:{revision:current.revision,config:original.config}});
 }
});
