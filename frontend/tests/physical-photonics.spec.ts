import {test,expect} from '@playwright/test';

test('Rabi pulse parameters change numerical evolution and preserve pinned evidence',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Physical Quantum Lab',exact:true}).click();
 await page.getByRole('spinbutton',{name:/Pulse duration/}).fill('0.5');
 await page.getByRole('spinbutton',{name:/Relaxation T/}).fill('');
 await page.getByRole('spinbutton',{name:/Pure dephasing/}).fill('');
 await page.getByRole('button',{name:'Run Rabi experiment',exact:true}).click();
 await expect(page.getByText('Rabi simulation complete',{exact:true})).toBeVisible({timeout:60000});
 await expect(page.locator('.lab-metric').filter({hasText:'Final Lindblad P₁'}).first()).toContainText('1.0000');
 await page.getByRole('button',{name:'Pin run for comparison',exact:true}).click();
 await page.getByRole('spinbutton',{name:/Drive Ω/}).fill('2');
 await page.getByRole('button',{name:'Run Rabi experiment',exact:true}).click();
 await expect(page.getByText('Rabi simulation complete',{exact:true})).toBeVisible({timeout:60000});
 await expect(page.locator('.lab-metric').filter({hasText:'Pinned final Lindblad P₁'})).toContainText('1.0000');
 await expect(page.locator('.lab-metric').filter({hasText:'Final Lindblad P₁'}).first().locator('b')).toHaveText('0');
 const json=page.waitForEvent('download');
 await page.getByRole('button',{name:'Export JSON',exact:true}).click();
 expect((await json).suggestedFilename()).toMatch(/\.json$/);
 const csv=page.waitForEvent('download');
 await page.getByRole('link',{name:'CSV',exact:true}).click();
 expect((await csv).suggestedFilename()).toMatch(/\.csv$/);
 const svg=page.waitForEvent('download');
 await page.getByRole('button',{name:'Plot SVG',exact:true}).click();
 expect((await svg).suggestedFilename()).toMatch(/\.svg$/);
 await page.getByRole('button',{name:'History',exact:true}).click();
 await page.getByRole('button',{name:'Open experiment'}).first().click();
 await expect(page.getByRole('heading',{name:'Rabi population dynamics',exact:true})).toBeVisible();
});

test('classical optical bench validates assembly and swaps bright and dark ports',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Photonics Lab',exact:true}).click();
 await page.getByRole('button',{name:'Empty bench',exact:true}).click();
 await page.getByRole('button',{name:'Run optical experiment',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('Missing:');
 for(const name of ['Coherent source','Beam splitter 1','Upper mirror','Lower mirror','Phase shifter','Beam splitter 2','Power meter D0','Power meter D1']){
  await page.getByRole('button',{name:'Place '+name,exact:true}).click();
 }
 await page.getByRole('button',{name:'Run optical experiment',exact:true}).click();
 await expect(page.getByText('Optical simulation complete',{exact:true})).toBeVisible({timeout:60000});
 await expect(page.locator('.lab-metric').filter({hasText:'D1 · calculated power'})).toContainText('1.0000');
 await page.getByRole('button',{name:'Pin run for comparison',exact:true}).click();
 await page.getByRole('button',{name:'Phase π',exact:true}).click();
 await page.getByRole('button',{name:'Run optical experiment',exact:true}).click();
 await expect(page.getByText('Optical simulation complete',{exact:true})).toBeVisible({timeout:60000});
 await expect(page.locator('.lab-metric').filter({hasText:'D0 · calculated power'})).toContainText('1.0000');
 await page.getByRole('button',{name:'History',exact:true}).click();
 await page.getByRole('button',{name:'Open experiment'}).first().click();
 await expect(page.getByRole('heading',{name:'Optical response',exact:true})).toBeVisible();
});

test('physical and photonics benches render on desktop and mobile',async({page})=>{
 await page.setViewportSize({width:1440,height:1000});
 await page.goto('/');
 await page.screenshot({path:'../docs/screenshots/research-command-center.png',fullPage:true});
 await page.getByRole('button',{name:'Physical Quantum Lab',exact:true}).click();
 await page.getByRole('button',{name:'Run Rabi experiment',exact:true}).click();
 await expect(page.getByText('Rabi simulation complete',{exact:true})).toBeVisible({timeout:60000});
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:'../docs/screenshots/physical-quantum-lab.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.screenshot({path:'../docs/screenshots/physical-quantum-lab-mobile.png',fullPage:true});
 await page.setViewportSize({width:1440,height:1000});
 await page.getByRole('button',{name:'Photonics Lab',exact:true}).click();
 await page.getByRole('button',{name:'Run optical experiment',exact:true}).click();
 await expect(page.getByText('Optical simulation complete',{exact:true})).toBeVisible({timeout:60000});
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:'../docs/screenshots/photonics-lab.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.screenshot({path:'../docs/screenshots/photonics-lab-mobile.png',fullPage:true});
});
