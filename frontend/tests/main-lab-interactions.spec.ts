import {test,expect} from '@playwright/test';
import {writeFileSync} from 'node:fs';

test('Bell experiment executes through Python and survives a page reload in History',async({page})=>{
 await page.setViewportSize({width:1512,height:1050});
 await page.goto('/');
 await expect(page.locator('.ml-connection').filter({hasText:'Python simulator connected'})).toBeVisible();
 await expect(page.getByText('3D environment ready',{exact:true})).toBeVisible({timeout:60000});
 const canvasBounds=await page.locator('[data-testid="lab-canvas"] canvas').boundingBox();
 await page.mouse.click(canvasBounds!.x+canvasBounds!.width*.525,canvasBounds!.y+canvasBounds!.height*.47);
 const response=page.waitForResponse(r=>r.url().endsWith('/api/jobs')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Run Bell experiment',exact:true}).click();
 const submitted=await response;
 expect(submitted.status()).toBe(202);
 const job=await submitted.json();
 expect(job.kind).toBe('experiment');
 expect(job.config).toMatchObject({algorithm:'bell',qubits:2,shots:1024,seed:42,gate_error:0,readout_error:0});
 const result=page.getByTestId('bell-result');
 await expect(result).toContainText('Completed · saved to History',{timeout:60000});
 await expect(result).toHaveAttribute('data-run-id',job.id);
 const saved=await(await page.request.get('/api/history/'+job.id)).json();
 expect(saved.status).toBe('completed');
 expect(saved.result.algorithm).toBe('bell');
 expect(saved.result.versions['qiskit-aer']).toBeTruthy();
 expect(Object.values(saved.result.counts).reduce((sum:number,value)=>sum+Number(value),0)).toBe(1024);
 for(const state of ['00','01','10','11'])await expect(page.getByTestId('bell-count-'+state)).toHaveText(String(saved.result.counts[state]||0));
 expect(saved.result.counts['01']||0).toBe(0);
 expect(saved.result.counts['10']||0).toBe(0);
 expect(saved.result.probabilities[0]).toBeCloseTo(.5,10);
 expect(saved.result.probabilities[3]).toBeCloseTo(.5,10);
 await page.getByRole('button',{name:'Move closer',exact:true}).click();
 await expect(page.getByText('3D environment ready',{exact:true})).toBeVisible({timeout:60000});
 await expect.poll(async()=>Math.abs(Number((await page.locator('[data-testid="lab-canvas"] canvas').getAttribute('data-camera-position'))!.split(',')[2])-3.34)).toBeLessThan(.01);
 await page.screenshot({path:'../docs/screenshots/main-lab-bell-result.png',fullPage:true});
 writeFileSync('../docs/main-lab-verification-bell.json',JSON.stringify(saved,null,2)+'\n');
 console.log('VERIFIED BELL RUN',JSON.stringify({id:saved.id,counts:saved.result.counts,backend:saved.result.backend,shots:saved.result.shots}));
 await page.reload();
 await page.getByRole('navigation',{name:'Main navigation'}).getByRole('button',{name:'History',exact:true}).click();
 const row=page.getByRole('row').filter({hasText:job.id.slice(0,8)});
 await expect(row).toContainText(/completed/i);
 await row.getByRole('button',{name:'Open experiment',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Quantum Experiments',exact:true})).toBeVisible();
 expect((await(await page.request.get('/api/history/'+job.id)).json()).result.counts).toEqual(saved.result.counts);
});

test('all five station inspectors link to their working modules and the gallery loads local photos',async({page})=>{
 await page.setViewportSize({width:1512,height:1050});
 await page.goto('/');
 const nav=page.getByRole('navigation',{name:'Main navigation'});
 for(const [station,modules] of [
  ['Quantum computer',['Virtual Computer','Circuit Builder']],
  ['Optical bench',['Photonics Lab']],
  ['Qubit control workstation',['Physical Quantum Lab']],
  ['Optimization workstation',['QUBO Lab','Optimization Lab']],
  ['Research console',['Experiments','History']],
 ] as [string,string[]][]){
  for(const module of modules){
   await page.getByRole('button',{name:'Select '+station,exact:true}).click();
   await page.getByTestId('equipment-inspector').getByRole('button',{name:module,exact:true}).click();
   await expect(nav.getByRole('button',{name:module,exact:true})).toHaveClass(/active/);
   if(module==='Photonics Lab')await expect(page.getByRole('img',{name:'Quantum Forge photonics studio reference',exact:true})).toBeVisible();
   await nav.getByRole('button',{name:'Main Quantum Lab',exact:true}).click();
  }
 }
 await page.getByRole('button',{name:'Photo Gallery',exact:true}).click();
 const gallery=page.getByRole('region',{name:'Laboratory Photo Gallery'});
 const thumbs=gallery.locator('.ml-gallery-thumbs button');
 await expect(thumbs).toHaveCount(6);
 for(let i=0;i<6;i++){
  await thumbs.nth(i).click();
  const photo=gallery.locator('.ml-gallery-image img');
  await expect.poll(()=>photo.evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true);
  expect(await photo.getAttribute('src')).toMatch(/^\/lab\/photos\//);
 }
 await gallery.getByRole('button',{name:'Real photographs',exact:true}).click();
 await expect(thumbs).toHaveCount(3);
 await thumbs.first().click();
 await expect(gallery).toContainText('REAL LABORATORY PHOTOGRAPH');
 await gallery.screenshot({path:'../docs/screenshots/main-lab-photo-gallery.png'});
 await gallery.getByRole('button',{name:'Concept references',exact:true}).click();
 await expect(thumbs).toHaveCount(3);
 await thumbs.first().click();
 await expect(gallery).toContainText('ILLUSTRATIVE CONCEPT IMAGE');
});

test('mobile controls, graphics preference and inline guide remain usable without overlap',async({page})=>{
 await page.setViewportSize({width:390,height:844});
 await page.goto('/');
 await expect(page.getByText('3D environment ready',{exact:true})).toBeVisible({timeout:60000});
 const low=page.getByRole('checkbox',{name:'Low graphics mode'});
 await expect(low).toBeChecked();
 await low.uncheck();
 await page.reload();
 await expect(low).not.toBeChecked();
 await low.check();
 await expect(page.getByText('3D environment ready',{exact:true})).toBeVisible({timeout:60000});
 await page.getByRole('button',{name:'Select Quantum computer',exact:true}).click();
 await expect(page.getByRole('button',{name:'Run Bell experiment',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.screenshot({path:'../docs/screenshots/main-lab-mobile.png',fullPage:true});
 await page.getByRole('button',{name:'Toggle navigation',exact:true}).click();
 await page.getByRole('button',{name:'Open learning guide',exact:true}).click();
 const guide=page.locator('.learning-drawer');
 await expect(guide).toBeVisible();
 expect(await guide.evaluate(el=>getComputedStyle(el).position)).toBe('relative');
 const guideBounds=await guide.boundingBox(),labBounds=await page.locator('.main-quantum-lab').boundingBox();
 expect(guideBounds!.y+guideBounds!.height).toBeLessThanOrEqual(labBounds!.y);
 await page.getByRole('button',{name:'Close learning guide',exact:true}).click();
 await page.getByRole('button',{name:'Pause 3D',exact:true}).click();
 await expect(page.locator('[data-testid="lab-canvas"] canvas')).toHaveCount(0);
 await page.getByRole('button',{name:'Resume 3D',exact:true}).click();
 await expect(page.getByText('3D environment ready',{exact:true})).toBeVisible({timeout:60000});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
});
