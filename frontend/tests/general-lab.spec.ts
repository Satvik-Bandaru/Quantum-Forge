import {test,expect} from '@playwright/test';

test('virtual computer executes and steps a Bell program',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Virtual Computer',exact:true}).click();
 await page.getByRole('button',{name:'Bell pair',exact:true}).click();
 await page.getByRole('button',{name:'Execute program',exact:true}).click();
 await expect(page.getByText('Program execution complete',{exact:true})).toBeVisible({timeout:60000});
 await expect(page.getByTestId('machine-step')).toContainText('0 / 3');
 await page.getByRole('button',{name:'Next instruction',exact:true}).click();
 await expect(page.getByTestId('machine-step')).toContainText('1 / 3');
 await page.getByRole('button',{name:'Next instruction',exact:true}).click();
 await expect(page.locator('.register-table')).toContainText('0.500');
 await expect(page.locator('.register-table')).toContainText('1.000');
 await page.getByRole('button',{name:'Reset debugger',exact:true}).click();
 await expect(page.getByTestId('machine-step')).toContainText('0 / 3');
 const download=page.waitForEvent('download');
 await page.getByRole('button',{name:'Export executed QASM',exact:true}).click();
 expect((await download).suggestedFilename()).toMatch(/\.qasm$/);
});

test('general lab runs Grover and opens its circuit on the computer',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Experiments',exact:true}).click();
 await page.getByRole('button',{name:'Grover search',exact:true}).click();
 await page.getByRole('button',{name:'Run experiment',exact:true}).click();
 await expect(page.getByText('Quantum experiment complete',{exact:true})).toBeVisible({timeout:60000});
 await expect(page.getByTestId('experiment-metrics')).toContainText('94.53');
 await page.getByRole('button',{name:'Open on virtual computer',exact:true}).click();
 await expect(page.getByLabel('Quantum program')).toHaveValue(/OPENQASM/);
 await page.getByRole('button',{name:'Execute program',exact:true}).click();
 await expect(page.getByText('Program execution complete',{exact:true})).toBeVisible({timeout:60000});
 await page.getByRole('button',{name:'History',exact:true}).click();
 await page.getByRole('button',{name:'Open experiment'}).first().click();
 await expect(page.getByRole('heading',{name:'Virtual Quantum Computer',exact:true})).toBeVisible();
});

test('superdense coding and malformed assembly have real outcomes',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Experiments',exact:true}).click();
 await page.getByRole('button',{name:'Superdense coding',exact:true}).click();
 await page.getByRole('combobox',{name:'Two-bit message',exact:true}).selectOption('11');
 await page.getByRole('button',{name:'Run experiment',exact:true}).click();
 await expect(page.getByText('Quantum experiment complete',{exact:true})).toBeVisible({timeout:60000});
 await expect(page.getByTestId('experiment-metrics')).toContainText('11');
 await page.getByRole('button',{name:'Virtual Computer',exact:true}).click();
 await page.getByLabel('Quantum program').fill('CX q0, q0');
 await page.getByRole('button',{name:'Execute program',exact:true}).click();
 await expect(page.getByRole('alert')).toContainText('Line 1');
});

test('general lab and virtual computer fit desktop and mobile',async({page})=>{
 await page.setViewportSize({width:1440,height:1000});
 await page.goto('/');
 await page.screenshot({path:'../docs/screenshots/general-overview.png',fullPage:true});
 await page.getByRole('button',{name:'Experiments',exact:true}).click();
 await page.getByRole('button',{name:'Quantum phase estimation',exact:true}).click();
 await page.getByRole('button',{name:'Run experiment',exact:true}).click();
 await expect(page.getByText('Quantum experiment complete',{exact:true})).toBeVisible({timeout:60000});
 await page.screenshot({path:'../docs/screenshots/general-experiments.png',fullPage:true});
 await page.getByRole('button',{name:'Virtual Computer',exact:true}).click();
 await page.getByRole('button',{name:'GHZ register',exact:true}).click();
 await page.getByRole('button',{name:'Execute program',exact:true}).click();
 await expect(page.getByText('Program execution complete',{exact:true})).toBeVisible({timeout:60000});
 await page.getByRole('button',{name:'Final state',exact:true}).click();
 await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:'../docs/screenshots/virtual-computer.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
 await page.screenshot({path:'../docs/screenshots/virtual-computer-mobile.png',fullPage:true});
});

test('reducing the register removes a Toffoli with an invalid second control',async({page})=>{
 await page.goto('/');
 await page.getByRole('button',{name:'Virtual Computer',exact:true}).click();
 await page.getByLabel('Quantum program').fill('CCX q1, q2, q0');
 await page.getByRole('button',{name:'Execute program',exact:true}).click();
 await expect(page.getByText('Program execution complete',{exact:true})).toBeVisible({timeout:60000});
 await page.getByRole('button',{name:'Open in Circuit Builder',exact:true}).click();
 await page.getByLabel('Qubits',{exact:true}).selectOption('2');
 await expect(page.getByText('0 operations',{exact:true})).toBeVisible();
});

test('phase-gate angle changes mark configurations as different',async()=>{
 const {sameConfig}=await import('../src/api');
 for(const name of ['P','CP']){
  expect(sameConfig({gates:[{name,target:1,angle:1}]},{gates:[{name,target:1,angle:2}]})).toBe(false);
 }
});
