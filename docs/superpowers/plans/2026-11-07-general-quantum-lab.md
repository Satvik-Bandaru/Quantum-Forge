# General Quantum Lab and Virtual Computer

User requests a general quantum computing lab and a virtual quantum computer. Continue implementation directly under the existing authorization; retain all experiments and saved history.

Architecture: keep FastAPI's bounded worker and SQLite history. Add `machine` and `experiment` jobs, a bounded assembly compiler, Qiskit state snapshots, and a general algorithm engine. Extend the React navigation and overview with Experiments and Virtual Computer. No arbitrary Python execution or physical QPU claims.

- [x] Scientific tests first: assembly safety, reversible execution, register statistics, Grover amplitude amplification, analytical QFT phases, exact QPE, Deutsch–Jozsa, dense coding, teleportation fidelity, CHSH correlations, VQE energy bounds.
- [x] Implement reusable circuit analysis and assembly compiler; bounded step-by-step virtual machine (8 qubits, 96 operations).
- [x] Implement general experiments with explicit inputs, circuit inspection, actual outputs, theory/reference comparisons, and exports.
- [x] Integrate API validation, job lifecycle, persistence, history restoration, CSV output; retain old job types and data.
- [x] Build general experiment catalog and virtual computer editor/debugger, register view, step control, state inspector, program import/export, machine resource limits.
- [x] Update overview, curriculum/roadmap, docs and browser tests. Run complete suite, build, browser workflows, and independent code review. Leave the updated app running locally.

Safety: retain one job, 45s timeout, RSS watchdog. Inspect only ideal states when stepping; terminal noisy readout is a separate final sample. Measurement does not pretend to collapse earlier snapshots. General experiments use small bounded inputs. Teleportation uses explicitly labelled deferred-measurement coherent corrections. QFT phases are validated independently; q0 is always the leftmost bit.

## Verified result
- Full backend suite: 78 passed (one documented upstream Starlette/httpx deprecation warning).
- Full frontend check suite: 13 passed, including all original workflows, real algorithm-to-machine QASM handoff, instruction stepping, malformed assembly, history replay, phase comparison and Toffoli resize regressions.
- TypeScript and Vite production build passed; pip check reported no broken requirements.
- Independent scientific/integration review found a control2 resize defect; fixed and verified with a browser regression.
- Desktop and mobile screenshots visually inspected; latest files are in docs/screenshots/.
- No additional packages, QPU accounts, credentials or cloud services were added. Old run history is preserved.
- Local server is running at http://127.0.0.1:8777.
