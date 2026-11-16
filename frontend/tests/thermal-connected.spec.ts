import {test,expect,type Page} from '@playwright/test';
import {mkdirSync,writeFileSync} from 'node:fs';

test.use({actionTimeout:15000});

async function navigate(page:Page,name:string){
 const toggle=page.getByRole('button',{name:'Toggle navigation',exact:true});
 if(await toggle.isVisible())await toggle.click();
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name,exact:true}).click();
}
async function openBench(page:Page){
 await page.goto('/');await navigate(page,'Connected Instruments');
 await expect(page.getByTestId('apparatus-status')).toHaveText('Ready to acquire');
}
async function acquire(page:Page){
 await expect(page.getByRole('button',{name:'Run connected experiment',exact:true})).toBeEnabled();
 const submission=page.waitForResponse(response=>response.url().endsWith('/api/jobs')&&response.request().method()==='POST');
 await page.getByRole('button',{name:'Run connected experiment',exact:true}).click();
 const response=await submission;expect(response.status()).toBe(202);const job=await response.json();
 await expect(page.getByTestId('connected-result')).toHaveAttribute('data-run-id',job.id,{timeout:60000});
 const run=await(await page.request.get('/api/history/'+job.id)).json();
 expect(run.status).toBe('completed');expect(run.result.checks.every((check:{passed:boolean})=>check.passed)).toBe(true);
 return run;
}

test('3D equipment context opens actual instrument controls without replacing the draft',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Select Quantum computer',exact:true}).click();
 await page.getByRole('button',{name:'Configure refrigerator',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Dilution refrigerator',exact:true})).toBeVisible();
 await expect(page.getByLabel('Thermal model',{exact:true})).toBeVisible();
 await page.getByLabel('Elapsed simulated time (s)',{exact:true}).fill('1980');
 await navigate(page,'Main Quantum Lab');
 await page.getByRole('button',{name:'Select Quantum computer',exact:true}).click();
 await page.getByRole('button',{name:'Configure quantum device',exact:true}).click();
 await expect(page.getByLabel('Device frequency (GHz)',{exact:true})).toBeVisible();
 await navigate(page,'Main Quantum Lab');
 await page.getByRole('button',{name:'Select Qubit control workstation',exact:true}).click();
 await page.getByRole('button',{name:'Configure microwave controls',exact:true}).click();
 await expect(page.getByLabel('Source frequency (GHz)',{exact:true})).toBeVisible();
 await navigate(page,'Main Quantum Lab');
 await page.getByRole('button',{name:'Select Qubit control workstation',exact:true}).click();
 await page.getByRole('button',{name:'Inspect readout and results',exact:true}).click();
 await expect(page.getByLabel('Assignment error 0 → 1',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Select Dilution refrigerator',exact:true}).click();
 await expect(page.getByLabel('Elapsed simulated time (s)',{exact:true})).toHaveValue('1980');
});

test('completed runs can be pinned and compared without mixing incompatible axes',async({page})=>{
 await openBench(page);await page.getByLabel('Sample points',{exact:true}).fill('51');
 await page.getByLabel('Sweep stop',{exact:true}).fill('0.1');
 const first=await acquire(page);
 await page.getByRole('button',{name:'Pin run for comparison',exact:true}).click();
 await expect(page.getByTestId('connected-comparison')).toContainText(first.id.slice(0,8));
 await page.getByRole('button',{name:'Select Microwave source',exact:true}).click();
 await page.getByLabel('Source power (dBm)',{exact:true}).fill('-6');
 const second=await acquire(page);
 await expect(page.getByTestId('connected-comparison')).toContainText('Maximum density difference');
 await expect(page.getByTestId('connected-comparison')).toContainText(second.id.slice(0,8));
 expect(Math.max(...second.result.series.map((row:{probability:number},i:number)=>Math.abs(row.probability-first.result.series[i].probability)))).toBeGreaterThan(.2);
 await navigate(page,'History');
 await page.getByRole('row').filter({hasText:first.id.slice(0,8)}).getByRole('button',{name:'Open experiment',exact:true}).click();
 await expect(page.getByTestId('connected-comparison')).toContainText(first.id.slice(0,8));
 await page.getByLabel('Experiment sequence',{exact:true}).selectOption('frequency_sweep');
 await acquire(page);
 await expect(page.getByTestId('connected-comparison')).toContainText('Different sweep axes');
 await expect(page.getByTestId('comparison-overlay')).toHaveCount(0);
 await page.getByRole('button',{name:'Clear pinned comparison',exact:true}).click();
 await expect(page.getByTestId('connected-comparison')).toHaveCount(0);
});

test('thermal heat load changes backend quantum populations and saved evidence replays',async({page,baseURL})=>{
 const original=await(await page.request.get('/api/apparatus')).json();
 try{
  await page.setViewportSize({width:1512,height:1050});await openBench(page);
  await page.getByLabel('Thermal model',{exact:true}).selectOption('thermal_network');
  await expect(page.getByTestId('thermal-state')).toBeVisible();
  await expect(page.getByTestId('apparatus-status')).toHaveText('Ready to acquire');
  await page.getByLabel('Sample points',{exact:true}).fill('51');
  await page.getByLabel('Sweep stop',{exact:true}).fill('0.1');
  const cold=await acquire(page);
  expect(cold.result.apparatus_status.thermal.valid).toBe(true);
  expect(cold.result.apparatus_status.thermal.checks.every((check:{passed:boolean})=>check.passed)).toBe(true);
  await page.getByRole('button',{name:'Pin run for comparison',exact:true}).click();
  await page.getByLabel('Mixing chamber: Heat load (W)',{exact:true}).fill('0.00012');
  await expect(page.getByTestId('apparatus-status')).toHaveText('Ready to acquire');
  await page.getByRole('button',{name:'Save apparatus',exact:true}).click();
  await expect(page.getByTestId('apparatus-save-state')).toHaveText('Saved apparatus');
  const warm=await acquire(page);
  expect(warm.result.apparatus_status.derived.temperature_k).toBeGreaterThan(cold.result.apparatus_status.derived.temperature_k+.04);
  expect(warm.result.series[0].probability-cold.result.series[0].probability).toBeGreaterThan(.02);
  await expect(page.getByTestId('connected-comparison')).toContainText('apparatus.cryostat.network.mixing_chamber.heat_load_w');
  const replayResponse=await page.request.post('/api/jobs',{headers:{Origin:new URL(baseURL!).origin},data:{kind:'connected',config:cold.config}});
  expect(replayResponse.status()).toBe(202);const replayJob=await replayResponse.json();
  await expect.poll(async()=>((await(await page.request.get('/api/jobs/'+replayJob.id)).json()).status),{timeout:60000}).toBe('completed');
  const replay=await(await page.request.get('/api/history/'+replayJob.id)).json();
  expect(replay.result.series).toEqual(cold.result.series);
  await navigate(page,'History');
  await page.getByRole('row').filter({hasText:cold.id.slice(0,8)}).getByRole('button',{name:'Open experiment',exact:true}).click();
  await expect(page.getByLabel('Thermal model',{exact:true})).toHaveValue('thermal_network');
  await expect(page.getByLabel('Mixing chamber: Heat load (W)',{exact:true})).toHaveValue('0.000001');
  await expect(page.getByTestId('connected-result')).toHaveAttribute('data-run-id',cold.id);
  await expect(page.getByTestId('apparatus-status')).toHaveText('Ready to acquire');
  mkdirSync('../docs/verification',{recursive:true});mkdirSync('../docs/screenshots',{recursive:true});
  writeFileSync('../docs/verification/nexus-thermal-workflow.json',JSON.stringify({cold,warm,replay},null,2)+'\n');
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'../docs/screenshots/nexus-thermal-laboratory.png',fullPage:true});
 }finally{
  const current=await(await page.request.get('/api/apparatus')).json();
  await page.request.put('/api/apparatus',{headers:{Origin:new URL(baseURL!).origin},data:{revision:current.revision,config:original.config}});
 }
});

test('amplitude calibration and dephasing expose sampled uncertainties and analytical evidence',async({page})=>{
 await openBench(page);await page.getByLabel('Sample points',{exact:true}).fill('51');
 await page.getByLabel('Experiment sequence',{exact:true}).selectOption('amplitude_calibration');
 const calibration=await acquire(page);
 expect(calibration.result.amplitude_calibration.status).toBe('estimated');
 expect(calibration.result.amplitude_calibration.estimated_pi_factor).toBeGreaterThan(.9);
 expect(calibration.result.amplitude_calibration.estimated_pi_factor).toBeLessThan(1.1);
 await expect(page.getByTestId('amplitude-calibration')).toContainText('Conditional 95% confidence interval');
 await page.getByRole('button',{name:'Select Pulse sequencer',exact:true}).click();
 await expect(page.getByLabel('Nominal π pulse duration (µs)',{exact:true})).toHaveValue('0.05');
 await page.getByLabel('Experiment sequence',{exact:true}).selectOption('dephasing');
 const dephasing=await acquire(page);
 // Finite pulses are compared to the instantaneous half-pulse limiting reference.
 expect(dephasing.result.reference.max_absolute_error).toBeLessThan(.01);
 expect(dephasing.result.series.every((point:{confidence_low:number;confidence_high:number})=>point.confidence_high>point.confidence_low)).toBe(true);
 await expect(page.getByRole('heading',{name:'Analytical special-case comparison',exact:true})).toBeVisible();
 await page.getByText('Raw acquired samples (51)',{exact:true}).click();
 await expect(page.getByRole('columnheader',{name:'95% shot interval',exact:true})).toBeVisible();
 mkdirSync('../docs/verification',{recursive:true});
 writeFileSync('../docs/verification/nexus-calibration-workflow.json',JSON.stringify({calibration,dephasing},null,2)+'\n');
});

test('multistage controls and evidence fit the mobile viewport',async({page})=>{
 await page.setViewportSize({width:390,height:844});await openBench(page);
 await page.getByLabel('Thermal model',{exact:true}).selectOption('thermal_network');
 await expect(page.getByTestId('thermal-state')).toBeVisible();
 await expect(page.getByLabel('Mixing chamber: Heat load (W)',{exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.getByText('Energy balance and thermal solver evidence',{exact:true}).click();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.getByRole('button',{name:'Select Microwave source',exact:true}).click();
 await page.getByText('Inspect input and output signals',{exact:true}).click();
 await expect(page.getByTestId('instrument-signal-evidence')).toContainText('predicted');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.getByRole('button',{name:'Select Dilution refrigerator',exact:true}).click();
 await page.evaluate(()=>window.scrollTo(0,0));
 mkdirSync('../docs/screenshots',{recursive:true});
 await page.screenshot({path:'../docs/screenshots/nexus-thermal-mobile.png',fullPage:true});
});
