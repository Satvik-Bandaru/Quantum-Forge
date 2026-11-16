# Main Quantum Laboratory Implementation Plan

**Goal:** Make a real navigable 3D laboratory the primary entrance while preserving every functional module, including Photonics Lab.

**Architecture:** React Three Fiber renders locally stored glTF equipment assets in a modern research room. A DOM equipment inspector, gallery and accessible equipment list connect to the existing App navigation and job lifecycle. Bell preparation uses the existing Python experiment endpoint and SQLite persistence; the room never invents telemetry.

**Tech stack:** Existing React 19 / TypeScript / FastAPI, Three.js, React Three Fiber 9, Drei 10, local GLB and image assets, Playwright.

**Spec:** User request “COMPLETE AND INTEGRATE THE QUANTUM FORGE MAIN LAB” of November 8, 2026.

## Binding requirements and implementation decisions

- Main Quantum Lab is first navigation entry and initial page; Overview and Photonics Lab remain.
- Detailed educational equipment models: central exposed dilution refrigerator, optical bench, racks, control/optimization/research workstations. Use authored GLB meshes, materials, UV textures and recognizable hardware details, not placeholder boxes.
- Real laboratory photographs are locally stored with documented origin/license; supplied concept images are explicitly illustrative and retained separately.
- Click/raycast on equipment selects inspector; keyboard-accessible equipment selectors provide equivalent controls. Orbit, zoom, camera presets and walk controls support exploration.
- Refrigerator → Virtual Computer / Circuit Builder; optics → Photonics Lab; controls → Physical Quantum Lab; optimization → QUBO / Optimization Lab; research → Experiments / History.
- Bell H(q0), CX(q0,q1), 1024 shots, seed 42, zero configured noise uses existing experiment API. Show returned counts/probabilities, backend, run ID and saved status. No random or hardcoded measured results.
- Low graphics defaults on: capped DPR, demand rendering, no real-time shadows, no bloom/postprocessing. High mode opt-in. WebGL failure must provide a clear fallback with usable module links.
- Information panes occupy layout space; notifications and the existing learning guide must not cover critical controls. Responsive layout has no horizontal overflow.
- Work in the current project on feature branch; preserve current server/data; no automatic GitHub publish. Reference images are present. No manufacturer CAD or live QPU is claimed.

## Tasks

- [x] Asset ingestion: copy accessible user reference images; obtain licensed real lab photos; store source attribution and truthful labels; verify actual file data.
- [x] Equipment authoring: create reproducible detailed textured GLB models and asset inventory, with conservative mesh/texture budgets.
- [x] Scene: implement R3F canvas, room, lights, model loading, selection, camera navigation, low/high modes, loading/failure states.
- [x] Integration: landing page, inspector, gallery, navigation, Bell callback/result rendering through shared job lifecycle, overlay layout fixes.
- [x] Verification: fresh frontend build; focused Playwright with actual raycast selection, camera motion, every module link, persisted backend Bell evidence, gallery load, low/mobile/fallback layouts; backend suite and relevant existing UI regression tests.
- [x] Independent review, screenshots, documentation and limitations. Update this ledger with observed outcomes before reporting completion.

## Review focus

- A model or texture returns 404: error state must expose the failure, not silently replace it with a fake room.
- Low graphics/context loss: module links and actual experiments remain accessible.
- A second job is running or backend is disconnected: no fabricated success and no duplicate job submission.
- Navigation during Bell execution: shared job state and History preserve the executed record.
- Mobile + guide + notification: no hidden dismissal controls, clipped inspector or intersecting floating panels.

## Progress

- Baseline confirmed: clean working tree at d431825; Main Quantum Lab absent. User-supplied reference images accessible. Branch feat/main-quantum-lab.

- Implemented locally stored GLB equipment (four unique models, seven instances), three real attributed photographs and three separately labeled user concept illustrations. Source asset loading and actual canvas raycasting verified.
- Independent review identified CSS import ordering and failed-GLTF cache retry; both fixed and scoped review found no remaining important issues. Mobile guide navigation now closes the sidebar.
- Final verification on November 15, 2026: production build passed; Python suite **215 passed** (12.22 s); full Playwright suite **26 passed** (1.2 min), including the formerly timed-out Max-Cut comparison.
- Browser Bell run `d61de411-2f57-43a0-8819-c3e74d61db37` completed and survived a page reload / History restore. Actual Qiskit Aer counts: 00=526, 11=498, 01=10=0; 1,024 shots and seed 42. Complete evidence saved in `docs/main-lab-verification-bell.json`.
- Visible in-app walkthrough also clicked the refrigerator mesh and ran Bell successfully: `fb3abd2d-328f-466e-b579-f4596be2fa2b`, identical seeded counts, Qiskit Aer 0.18.2, saved to SQLite.
- Final screenshots: main-lab-overview.png, main-lab-quantum-computer.png, main-lab-bell-result.png, main-lab-photo-gallery.png, main-lab-mobile.png, main-lab-live.jpg.
- Remaining limits: educational equipment rather than manufacturer CAD; no live QPU or instrument telemetry; bounded camera without physical obstacle collision; low graphics configured and tested, not a hardware performance guarantee. Large lazy-loaded Three.js chunk and an upstream Three.Clock deprecation warning remain nonblocking.
