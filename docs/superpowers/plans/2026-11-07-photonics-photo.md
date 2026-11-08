# Photonics photo experience

**Goal:** Put the user's supplied photonics studio image into the working lab and connect visible equipment with simulator controls.

**Approach:** Preserve the existing classical MZI calculation, controls, schematic and saved results. Make the photo guide the default bench view, with five keyboard-accessible equipment hotspots, matching selection in the component library, an enlarged equipment detail, a short explanation, and a button that focuses the relevant control. A Photo lab/Schematic toggle retains both views. Import the original PNG as a local Vite asset so the built app works offline; no image generation or remote dependencies are needed.

The image is a visual reference, not a live instrument feed. Its embedded quantum labels and chart values are artwork; the app's actual model and results remain explicitly classical wave optics. Photo guide selections do not run calculations or change numerical settings. No database or backend change is needed.

- [x] Inspect supplied image and current photonics controls.
- [x] Add local image and interactive scene component with responsive styles.
- [x] Integrate shared component selection, diagram toggle and focus links.
- [x] Build production frontend and verify image loads, navigation and current optical workflow in Chrome.
- [x] Inspect desktop/mobile screenshots and record results.


## Verification

- Production TypeScript/Vite build passed. The exact supplied image is bundled locally as `quantum-photonics-studio-CP9jpDhT.png` (2,393.59 kB), served by the existing `/assets` mount.
- Two new photo workflow tests first failed on the missing image in the old build, then passed after integration.
- `playwright test tests/photonics-photo.spec.ts tests/physical-photonics.spec.ts`: **5 passed**, 15.4 s. Includes image loading, all five selections, explanatory guide changes, focus jumps, shared photo/schematic selection, mobile bounds, and the existing physical/optical numerical workflows.
- Desktop and 390px mobile scene screenshots were visually inspected: `docs/screenshots/photonics-photo-desktop.png` and `photonics-photo-mobile.png`.
- No backend, model schema, dependency package, or saved experiment was changed. Browser verification created actual numerical test runs through the existing API.

Files: `frontend/src/PhotonicsScene.tsx`, `photonics-scene.css`, `assets/quantum-photonics-studio.png`, `vite-env.d.ts`, integration in `PhotonicsLab.tsx`, tests in `frontend/tests/photonics-photo.spec.ts`, and the README photonics description.
