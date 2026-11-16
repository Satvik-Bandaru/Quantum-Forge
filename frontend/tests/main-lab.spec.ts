import {test,expect} from '@playwright/test';

test('main laboratory is the landing page and loads actual 3D assets',async({page})=>{
 await page.setViewportSize({width:1512,height:1050});
 const failures:string[]=[];
 page.on('pageerror',error=>console.log('PAGE ERROR',error.message));
 page.on('console',message=>{if(message.type()==='error'||message.type()==='warning')console.log('BROWSER',message.text())});
 page.on('response',r=>{if(r.url().includes('/lab/')&&r.status()>=400)failures.push(r.url())});
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Main Quantum Laboratory',exact:true})).toBeVisible();
 await expect(page.getByRole('button',{name:'Main Quantum Lab',exact:true})).toHaveClass(/active/);
 try{await expect(page.getByText('3D environment ready',{exact:true})).toBeVisible({timeout:60000})}catch(error){await page.screenshot({path:'../docs/screenshots/main-lab-load-diagnostic.png',fullPage:true});console.log('ASSET FAILURES',failures);throw error}
 await expect(page.locator('[data-testid="lab-canvas"] canvas')).toBeVisible();
 await expect(page.getByRole('checkbox',{name:'Low graphics mode'})).toBeChecked();
 expect(failures).toEqual([]);
 await page.screenshot({path:'../docs/screenshots/main-lab-overview.png',fullPage:true});
});

test('raycast equipment clicks and camera navigation operate on the actual canvas',async({page})=>{
 await page.setViewportSize({width:1512,height:1050});
 await page.goto('/');
 await expect(page.getByText('3D environment ready',{exact:true})).toBeVisible({timeout:60000});
 const canvas=page.locator('[data-testid="lab-canvas"] canvas');
 const bounds=await canvas.boundingBox();
 expect(bounds).not.toBeNull();
 // Hit visible equipment meshes in the verified overview, not DOM station buttons.
 const targets=[
  {name:'Quantum computer',x:.525,y:.47},
  {name:'Optical bench',x:.35,y:.53},
  {name:'Qubit control workstation',x:.80,y:.49},
  {name:'Optimization workstation',x:.88,y:.65},
  {name:'Research console',x:.87,y:.80},
 ];
 for(const target of targets){
  await page.mouse.click(bounds!.x+bounds!.width*target.x,bounds!.y+bounds!.height*target.y);
  await expect(page.getByTestId('equipment-inspector').getByRole('heading',{name:target.name,exact:true})).toBeVisible();
 }
 await page.mouse.click(bounds!.x+bounds!.width*.525,bounds!.y+bounds!.height*.47);
 const initial=await canvas.getAttribute('data-camera-position');
 await page.getByRole('button',{name:'Move closer',exact:true}).click();
 await expect.poll(()=>canvas.getAttribute('data-camera-position')).not.toBe(initial);
 await expect.poll(async()=>{const p=(await canvas.getAttribute('data-camera-position'))!.split(',').map(Number);return Math.abs(p[2]-3.34)}).toBeLessThan(.01);
 await page.screenshot({path:'../docs/screenshots/main-lab-quantum-computer.png',fullPage:true});
 const close=await canvas.getAttribute('data-camera-position');
 await canvas.focus();
 await canvas.press('w');
 await expect.poll(()=>canvas.getAttribute('data-camera-position')).not.toBe(close);
 const walked=await canvas.getAttribute('data-camera-position');
 await page.mouse.move(bounds!.x+bounds!.width*.5,bounds!.y+bounds!.height*.5);
 await page.mouse.down();
 await page.mouse.move(bounds!.x+bounds!.width*.6,bounds!.y+bounds!.height*.52,{steps:8});
 await page.mouse.up();
 await expect.poll(()=>canvas.getAttribute('data-camera-position')).not.toBe(walked);
 await page.getByRole('button',{name:'Reset laboratory view',exact:true}).click();
 await expect.poll(()=>canvas.getAttribute('data-camera-position')).toBe(initial);
});

test('missing model is reported and retry recovers after the asset is restored',async({page})=>{
 await page.route('**/lab/models/dilution-refrigerator.glb',route=>route.abort());
 await page.goto('/');
 await expect(page.getByText('3D load failed',{exact:true})).toBeVisible({timeout:60000});
 await expect(page.getByText(/3D view unavailable:/)).toBeVisible();
 await page.unroute('**/lab/models/dilution-refrigerator.glb');
 await page.getByRole('button',{name:'Retry 3D',exact:true}).click();
 await expect(page.getByText('3D environment ready',{exact:true})).toBeVisible({timeout:60000});
 await page.getByRole('button',{name:'Select Optical bench',exact:true}).click();
 await page.getByTestId('equipment-inspector').getByRole('button',{name:'Photonics Lab',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Photonics Lab',exact:true})).toBeVisible();
});
