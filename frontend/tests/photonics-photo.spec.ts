import {test,expect,type Locator} from '@playwright/test';

const photoName='Quantum Forge photonics studio reference';
const explorations=[
 {hotspot:'Explore laser source',component:'Coherent source',explanation:/laser|light|beam/i},
 {hotspot:'Explore beam splitters',component:'Beam splitter 1',explanation:/split|paths|recombine/i},
 {hotspot:'Explore mirrors',component:'Upper mirror',explanation:/redirect|steer|reflect/i},
 {hotspot:'Explore phase shifter',component:'Phase shifter',explanation:/phase|timing|waves/i},
 {hotspot:'Explore power meters',component:'Power meter D0',explanation:/power|measure|brightness/i},
];

async function expectLoadedPhoto(photo:Locator){
 await expect(photo).toBeVisible();
 await expect.poll(()=>photo.evaluate((element:HTMLImageElement)=>element.complete&&element.naturalWidth>0)).toBe(true);
}

test('studio photo explains real components and links their simulation controls',async({page})=>{
 await page.setViewportSize({width:1440,height:1000});
 await page.goto('/');
 await page.getByRole('button',{name:'Photonics Lab',exact:true}).click();
 const scene=page.getByTestId('photonics-scene');
 const photo=scene.getByRole('img',{name:photoName,exact:true});
 const guide=page.getByTestId('photonics-component-guide');
 const controls=page.locator('section.panel').filter({has:page.getByText('SELECTED COMPONENT',{exact:true})});
 await expectLoadedPhoto(photo);
 await scene.scrollIntoViewIfNeeded();
 await scene.screenshot({path:'../docs/screenshots/photonics-photo-desktop.png'});

 let previousGuide=await guide.innerText();
 for(const exploration of explorations){
  await scene.getByRole('button',{name:exploration.hotspot,exact:true}).click();
  await expect(controls.getByRole('heading',{name:exploration.component,exact:true})).toBeVisible();
  await expect(guide.getByRole('heading')).toBeVisible();
  await expect(guide).toContainText(exploration.explanation);
  await expect(guide).not.toHaveText(previousGuide);
  previousGuide=await guide.innerText();
 }

 await scene.getByRole('button',{name:'Explore laser source',exact:true}).click();
 await guide.getByRole('button',{name:'Adjust this component',exact:true}).click();
 await expect(page.getByRole('spinbutton',{name:'Source power (mW)',exact:true})).toBeFocused();
 await scene.getByRole('button',{name:'Explore phase shifter',exact:true}).click();
 await guide.getByRole('button',{name:'Adjust this component',exact:true}).click();
 await expect(page.getByRole('spinbutton',{name:'Relative phase φ (radians)',exact:true})).toBeFocused();

 await page.getByRole('button',{name:'Schematic',exact:true}).click();
 await expect(photo).toBeHidden();
 await expect(page.locator('svg.optical-bench')).toBeVisible();
 await page.getByRole('button',{name:'Inspect SOURCE',exact:true}).click();
 await expect(controls.getByRole('heading',{name:'Coherent source',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Photo lab',exact:true}).click();
 await expectLoadedPhoto(photo);
 await expect(guide).toContainText(/laser|light|beam/i);
});

test('studio photo and all component hotspots remain usable on mobile',async({page})=>{
 const viewport={width:390,height:844};
 await page.setViewportSize(viewport);
 await page.goto('/');
 await page.getByRole('button',{name:'Toggle navigation',exact:true}).click();
 await page.getByRole('button',{name:'Photonics Lab',exact:true}).click();
 const scene=page.getByTestId('photonics-scene');
 const photo=scene.getByRole('img',{name:photoName,exact:true});
 const guide=page.getByTestId('photonics-component-guide');
 await expectLoadedPhoto(photo);
 const imageBounds=await photo.boundingBox();
 expect(imageBounds).not.toBeNull();
 expect(imageBounds!.width).toBeGreaterThan(250);
 expect(imageBounds!.x).toBeGreaterThanOrEqual(0);
 expect(imageBounds!.x+imageBounds!.width).toBeLessThanOrEqual(viewport.width);

 for(const exploration of explorations){
  const hotspot=scene.getByRole('button',{name:exploration.hotspot,exact:true});
  await hotspot.scrollIntoViewIfNeeded();
  await expect(hotspot).toBeVisible();
  const bounds=await hotspot.boundingBox();
  expect(bounds).not.toBeNull();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x+bounds!.width).toBeLessThanOrEqual(viewport.width);
  await hotspot.click();
  await expect(guide.getByRole('heading')).toBeVisible();
  await expect(guide).toContainText(exploration.explanation);
 }

 await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth)).toBeLessThanOrEqual(viewport.width);
 await scene.scrollIntoViewIfNeeded();
 await scene.screenshot({path:'../docs/screenshots/photonics-photo-mobile.png'});
});
