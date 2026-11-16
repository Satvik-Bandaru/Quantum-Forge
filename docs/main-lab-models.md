# Main Quantum Lab equipment models

The four GLBs are original Quantum Forge educational models. The refrigeration cutaway, optical layout, rack instruments, and workstation represent familiar laboratory assemblies at plausible scale. Equipment labels, the rack standby windows, and the workstation circuit schematic are static illustrations. The models are unsuitable for manufacturing, optical alignment, cryogenic engineering, or instrument calibration.

| Asset | Width × height × depth (m) | Triangles | Material primitives | Size (bytes) |
| --- | ---: | ---: | ---: | ---: |
| `dilution-refrigerator.glb` | 1.571 × 2.830 × 1.192 | 45,420 | 13 | 1,794,608 |
| `optical-bench.glb` | 3.008 × 1.113 × 1.215 | 63,350 | 12 | 2,600,020 |
| `electronics-rack.glb` | 0.644 × 2.036 × 0.910 | 26,412 | 11 | 1,226,636 |
| `workstation.glb` | 1.455 × 1.364 × 1.392 | 6,726 | 13 | 436,728 |
| Total for the four unique files | | 141,908 | 49 | 6,057,992 |

- The refrigerator exposes an upper vacuum can, a partial rear shield, five thermal plates, their fasteners and supports, fourteen curved coax runs, and a lower mixing chamber.
- The optical bench has 1,440 recessed mounting holes in the mesh, two levels of rail detail, adjustable posts, a source housing, mounted lens cells, mirrors, a beamsplitter cube, and two cabled detector assemblies.
- The electronics rack has instrument rails and removable-looking panels with ventilation slots, knob assemblies, coax connectors, front patch cables, and rear cable routing.
- The workstation has a desk, monitor and mount, a patterned keyboard with individual keycaps, a trackpad, a cabled interface, and a chair with armrests and five casters. The scene can reuse this asset for control, optimization, and research stations.

The files live in `frontend/public/lab/models` and are served at `/lab/models/`. Coordinates use meters and Y-up, with the floor at Y = 0 and the X/Z bounding box centered on the origin. The viewing side faces +Z. Each GLB contains one indexed mesh primitive per material, UVs and normals for every vertex, and embedded PNGs for the metal finish and equipment labels. The workstation also embeds a circuit illustration. The texture sizes are 256 × 256, 256 × 512, and 512 × 288 pixels.

## Rebuild

Install the existing frontend dependencies with `npm ci --prefix frontend`. From the repository root run `node scripts/build-lab-models.mjs` with Node.js 24. The script uses the project's installed Three.js to build the meshes and writes self-contained glTF 2.0 binaries. It prints the dimensions, triangle count, material draw count, image count, and size for each file.
