import { test, expect } from '@playwright/test';

test('Bell circuit executes, saves and restores with real probabilities', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button',{name:'Circuit Builder',exact:true}).click();
  await page.getByRole('button',{name:'Bell state',exact:true}).click();
  await page.getByRole('button',{name:'Run circuit',exact:true}).click();
  await expect(page.getByText('Simulation complete',{exact:true})).toBeVisible({timeout:60000});
  await expect(page.getByTestId('probability-chart')).toContainText('00');
  await expect(page.getByText('The circuit has changed. Results below belong to the last saved run.',{exact:true})).toBeHidden();
  await expect(page.getByTestId('probability-chart')).toContainText('11');
  await page.getByLabel('Circuit name').fill('Browser Bell test');
  await page.getByRole('button',{name:'Save circuit',exact:true}).click();
  await expect(page.getByText('Circuit saved',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Clear circuit',exact:true}).click();
  await expect(page.getByText('0 operations',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:/Browser Bell test/}).first().click();
  await expect(page.getByText('2 operations',{exact:true})).toBeVisible();
  expect((await page.locator('#circuit-diagram title').allTextContents()).join(' ')).not.toContain('qnull');
  await page.getByRole('button',{name:'History',exact:true}).click();
  await expect(page.getByText('Circuit simulation').first()).toBeVisible();
});

test('Max-Cut comparison runs all three solvers and exports', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button',{name:'Optimization Lab',exact:true}).click();
  await page.getByRole('button',{name:'Run comparison',exact:true}).click();
  await expect(page.getByText('Comparison complete',{exact:true})).toBeVisible({timeout:60000});
  await expect(page.getByTestId('solver-comparison')).toContainText('QAOA');
  await expect(page.getByTestId('solver-comparison')).toContainText('Simulated annealing');
  const download = page.waitForEvent('download');
  await page.getByRole('button',{name:'Export JSON',exact:true}).click();
  expect((await download).suggestedFilename()).toMatch(/\.json$/);
});

test('Knapsack edit and history reload use real result', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button',{name:'Optimization Lab',exact:true}).click();
  await page.getByRole('button',{name:'Knapsack',exact:true}).click();
  await page.getByRole('button',{name:'Run comparison',exact:true}).click();
  await expect(page.getByText('Comparison complete',{exact:true})).toBeVisible({timeout:60000});
  await expect(page.getByTestId('solver-comparison')).toContainText('OR-Tools');
  await page.getByRole('button',{name:'History',exact:true}).click();
  await page.getByRole('button',{name:'Open experiment'}).first().click();
  await expect(page.getByTestId('solver-comparison')).toBeVisible();
});

test('knapsack comma editors preserve typing and use edited instance', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button',{name:'Optimization Lab',exact:true}).click();
  await page.getByRole('button',{name:'Knapsack',exact:true}).click();
  const weights=page.getByLabel('Item weights',{exact:true});
  await weights.fill('2, 3, ');
  await expect(weights).toHaveValue('2, 3, ');
  await weights.pressSequentially('4');
  await page.getByLabel('Item values',{exact:true}).fill('3, 4, 5');
  await page.getByLabel('Capacity',{exact:true}).fill('5');
  await page.getByRole('button',{name:'Run comparison',exact:true}).click();
  await expect(page.getByText('Comparison complete',{exact:true})).toBeVisible({timeout:60000});
  await expect(page.getByText('Exhaustive optimum:')).toContainText('7');
});

test('terminal measurement misuse shows a useful validation error', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button',{name:'Circuit Builder',exact:true}).click();
  await page.getByRole('button',{name:'Add M gate',exact:true}).click();
  await page.getByRole('button',{name:'Add H gate',exact:true}).click();
  await page.getByRole('button',{name:'Run circuit',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Measurements must be terminal');
});

test('desktop and mobile layouts render without horizontal overflow', async ({page}) => {
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'Quantum Forge Research Command Center'})).toBeVisible();
  await page.screenshot({path:'../docs/screenshots/overview.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await expect(page.locator('.qf-command-heading h1')).toHaveCount(1);
  await page.locator('.qf-laboratories').scrollIntoViewIfNeeded();
  await page.screenshot({path:'../docs/screenshots/quantum-forge-overview-mobile-labs.png'});
  await page.evaluate(()=>window.scrollTo(0,0));
  await expect(page.locator('.qf-command-heading h1')).toBeInViewport();
  await page.screenshot({path:'../docs/screenshots/quantum-forge-overview-mobile.png',fullPage:true});
  await page.setViewportSize({width:1440,height:1000});
  await page.getByRole('button',{name:'Circuit Builder',exact:true}).click();
  await page.getByRole('button',{name:'Bell state',exact:true}).click();
  await page.getByRole('button',{name:'Run circuit',exact:true}).click();
  await expect(page.getByText('Simulation complete',{exact:true})).toBeVisible({timeout:60000});
  await page.screenshot({path:'../docs/screenshots/circuit-builder.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await expect(page.getByRole('button',{name:'Run circuit',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(390);
  await page.screenshot({path:'../docs/screenshots/mobile.png',fullPage:true});
});


test('gate palette drag places a gate on the selected wire', async ({page}) => {
  await page.goto('/');
  await page.getByRole('button',{name:'Circuit Builder',exact:true}).click();
  await page.getByRole('button',{name:'Add H gate',exact:true}).dragTo(page.locator('#circuit-diagram > g').nth(1).locator('rect'));
  await expect(page.getByText('1 operations',{exact:true})).toBeVisible();
  expect((await page.locator('#circuit-diagram title').allTextContents()).join(' ')).toContain('H on q1');
  await page.getByRole('button',{name:'Run circuit',exact:true}).click();
  await expect(page.getByText('Simulation complete',{exact:true})).toBeVisible({timeout:60000});
  await expect(page.getByTestId('probability-chart')).toContainText('01');
});
