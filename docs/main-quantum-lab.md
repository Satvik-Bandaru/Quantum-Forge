# Main Quantum Laboratory

Main Quantum Lab is the initial page and first item in the left navigation. Overview and every prior module, including the Photonics Lab and its photo workbench, remain available.

## Explore

- Click a visible equipment mesh to select its inspector. The equipment directory offers the same selection with keyboard-accessible buttons.
- Drag to orbit, scroll/pinch to zoom, and use right-drag to pan. Focus the canvas and use WASD or arrow keys to move; Escape releases keyboard focus.
- Choose **Move closer** for an equipment camera view; **Reset view** returns to the room overview.
- **Low graphics** is enabled by default and saved in this browser. It uses pixel ratio 1, demand rendering and no real-time shadows. Detailed mode caps pixel ratio at 1.5. **Pause 3D** releases the scene while leaving module access available.

| Equipment | Working modules |
| --- | --- |
| Quantum computer / dilution refrigerator | Virtual Computer, Circuit Builder |
| Optical bench | Existing Photonics Lab |
| Qubit control workstation / electronics racks | Physical Quantum Lab |
| Optimization workstation | QUBO Lab, Optimization Lab |
| Research console | Experiments, History |

## Execute a real simulation

1. Click the refrigerator or select **Quantum computing** in the equipment directory.
2. Click **Run Bell experiment** in its inspector.
3. The browser submits an `experiment` job with `algorithm: bell`, two qubits, 1,024 shots, seed 42 and zero configured gate/readout noise to `/api/jobs`.
4. The existing Python worker prepares H(q0), CX(q0,q1) using Qiskit Aer. It returns sampled counts, ideal statevector probabilities, software versions and actual compute time.
5. The existing SQLite store saves the run. The inspector shows the returned record ID and counts; **Inspect saved run** opens the full experiment module, and **History** opens the persistent notebook.

Measured sample counts are never synthesized by the frontend. Ideal statevector probabilities and sampled simulation outcomes have separate labels. A fixed seed makes this small experiment reproducible; it does not make a CPU simulation a physical measurement.

## Assets and visual meaning

- Four original educational GLB assets contain UV textures, metal materials, thermal plates, fasteners, curved coax wiring, perforated optical tables, optical mounts, instrument panels and workstation details. See [model inventory](main-lab-models.md) for dimensions, triangle counts, rebuild command and limitations.
- The integrated gallery stores three real laboratory photos in the project: two from Oak Ridge National Laboratory and one from FMN Laboratory. Attribution, source and Creative Commons licenses are in [asset credits](main-lab-assets.md).
- The three supplied main-hall, circuit-studio and photonics reference PNGs are labeled **illustrative concept images**, never live instruments or real laboratory photographs.
- Equipment information panels show contextual previews from the same local gallery assets. A failed model load is reported, and Retry 3D clears the failed loader entry before loading again. The directory and modules remain available during an asset or WebGL failure.

## Limits

This is an educational facility, not a manufacturer CAD model or calibrated hardware digital twin. Equipment screen textures are static illustrations with no live telemetry. The camera provides bounded inspection/navigation rather than physical collision simulation. The low graphics configuration targets modest GPU and memory use, but it is not a measured performance guarantee for every 16 GB Mac. No live quantum processor, dilution refrigerator, laser, or laboratory instrument is connected.

The WebGL scene requires a compatible browser. Software rendering and initial shader compilation can be slower. A modern local browser and low graphics mode are the default path; the ordinary module links work even if 3D rendering fails.

## Verification — November 15, 2026

- Production build passed; 215 Python tests passed; all 26 Playwright browser tests passed.
- The browser tests click actual equipment meshes, navigate camera controls, open all connected modules, load all gallery images, restore a saved Bell run after reload, recover a missing GLB via Retry 3D, and check 390 px mobile layout and nonoverlapping inline guide.
- [Actual Bell run record](main-lab-verification-bell.json): 1,024 shots with seed 42 returned 526 counts for 00 and 498 for 11; the other two outcomes were zero. The stored ideal statevector probabilities are 0.5 for each of 00 and 11.
- [Main room](screenshots/main-lab-overview.png), [refrigerator detail](screenshots/main-lab-quantum-computer.png), [real results](screenshots/main-lab-bell-result.png), [photo gallery](screenshots/main-lab-photo-gallery.png), and [mobile view](screenshots/main-lab-mobile.png).
