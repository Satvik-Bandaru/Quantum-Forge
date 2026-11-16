import {test,expect,Page} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';

async function acquire(page:Page){
 const response=page.waitForResponse(response=>response.url().endsWith('/api/jobs')&&response.request().method()==='POST');
 await page.getByRole('button',{name:'Run research experiment',exact:true}).click();
 const submitted=await response;expect(submitted.status()).toBe(202);const initial=await submitted.json();
 await expect(page.getByTestId('research-result')).toHaveAttribute('data-run-id',initial.id,{timeout:30000});
 const record=await (await page.request.get('/api/history/'+initial.id)).json();expect(record.status).toBe('completed');return record;
}

test('single-photon paths, phase, loss and detection use returned quantum probabilities',async({page})=>{
 await page.goto('/');const nav=page.getByRole('navigation',{name:'Main navigation'});
 await expect(nav.getByRole('button',{name:'Quantum Optics',exact:true})).toHaveCount(1,{timeout:1000});
 await nav.getByRole('button',{name:'Quantum Optics',exact:true}).click();
 const first=await acquire(page);expect(first.result.probabilities.detector1).toBeCloseTo(1,10);expect(first.result.probabilities.detector0).toBeCloseTo(0,10);
 await page.getByLabel('Optical phase (rad)',{exact:true}).fill(String(Math.PI));
 await expect(page.getByTestId('stale-research-result')).toBeVisible();
 const shifted=await acquire(page);expect(shifted.result.probabilities.detector0).toBeCloseTo(1,10);
 await page.getByLabel('Path coherence',{exact:true}).fill('0');
 const mixed=await acquire(page);expect(mixed.result.probabilities.detector0).toBeCloseTo(.5,10);
 await page.getByLabel('Detector 0 efficiency',{exact:true}).fill('0');
 const lost=await acquire(page);expect(lost.result.probabilities.no_click).toBeCloseTo(.5,10);expect(Object.values(lost.result.counts).reduce((a:any,b:any)=>a+b,0)).toBe(1024);
 await mkdir('../docs/verification',{recursive:true});await writeFile('../docs/verification/nexus-single-photon-run.json',JSON.stringify(lost,null,2));
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../docs/screenshots/nexus-quantum-optics.png',fullPage:true});
});

test('repetition-code correction matches analytic failure and reopens from History',async({page})=>{
 await page.goto('/');const nav=page.getByRole('navigation',{name:'Main navigation'});await nav.getByRole('button',{name:'Error Correction',exact:true}).click();
 const first=await acquire(page);expect(first.result.metrics.logical_error_probability).toBeCloseTo(.028,10);expect(first.result.metrics.corrected_fidelity).toBeCloseTo(.972,10);
 await page.getByLabel('Physical X-error probability',{exact:true}).fill('.4');
 const changed=await acquire(page);expect(changed.result.metrics.logical_error_probability).toBeCloseTo(.352,10);
 await page.reload();await nav.getByRole('button',{name:'History',exact:true}).click();
 const row=page.getByRole('row').filter({hasText:changed.id.slice(0,8)});await row.getByRole('button',{name:'Open experiment'}).click();
 await expect(page.getByTestId('research-result')).toHaveAttribute('data-run-id',changed.id);
 await expect(page.getByLabel('Physical X-error probability',{exact:true})).toHaveValue('0.4');
 await writeFile('../docs/verification/nexus-repetition-code-run.json',JSON.stringify(changed,null,2));
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../docs/screenshots/nexus-error-correction.png',fullPage:true});
});

test('quantum optics remains usable on mobile with bounded inputs',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await page.getByRole('button',{name:'Toggle navigation'}).click();
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:'Quantum Optics',exact:true}).click();
 await page.getByLabel('Detector 0 efficiency',{exact:true}).fill('-1');
 await expect(page.getByRole('button',{name:'Run research experiment',exact:true})).toBeDisabled();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBe(true);
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../docs/screenshots/nexus-quantum-optics-mobile.png',fullPage:true});
});
