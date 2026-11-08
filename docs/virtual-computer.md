# The virtual quantum computer

QF-8 is an ideal statevector debugger with a separate noisy final-shot readout. It runs on the Mac CPU using Qiskit and Aer. The eight visual slots represent virtual register positions, not physical superconducting qubits, calibration data, or fabricated hardware telemetry.

## Write and execute a program

Select 1–8 register qubits and write bounded quantum assembly. Each executable line contains an operation. Gate operands are ordered **control(s), target**, and bitstrings are displayed **q0 first**.

```text
# Prepare an entangled pair
H q0
CX q0, q1
MEASURE ALL
```

Supported operations:

| Family | Instructions |
| --- | --- |
| Single-qubit gates | X, Y, Z, H, S, SDG, T, TDG |
| Angled gates | RX, RY, RZ, P |
| Two-qubit gates | CX/CNOT, CZ, CP, SWAP |
| Three-qubit gate | CCX (Toffoli) |
| Readout annotation | MEASURE ALL |

Examples:

```text
RY pi/3 q0
RZ -pi/4 q0
CP pi/2 q0, q1
CCX q0, q1, q2
```

Angles support numeric literals, `pi`, parentheses, addition, subtraction, multiplication, and division. Expressions are parsed with a bounded AST interpreter. No function calls, exponentiation, Python, shell commands, file access, loops, gate macros, or arbitrary code are executed. Angles are capped at ±100π. The program is capped at 12 KB and 96 executable instructions.

A subset of OpenQASM 2 is accepted:

```qasm
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0],q[1];
measure q[0] -> c[0];
measure q[1] -> c[1];
```

Register names are `q` and `c`; declared register sizes must match the selected machine size. Full-register readout `measure q -> c;` is accepted. Terminal measurement annotations always sample the complete register. Partial or intermediate measurement semantics, arbitrary includes, custom gate definitions, reset instructions, and classical feed-forward are intentionally not supported. `Reset debugger` rewinds the inspector to |0…0⟩; it does not physically reverse a noisy measurement.

The exported QASM is an actual executed circuit, decomposed into the supported basis. General experiments whose decomposition fits the debugger limits can be moved into the virtual computer. Larger circuits remain executable in Experiments and downloadable as QASM.

## Inspect execution

`Execute program` runs all instructions in a bounded worker and records the ideal state after each. The debugger's program counter selects one of those **actual precomputed snapshots**. Forward/back, a scrubber, and trace playback inspect them without rerunning a costly simulation. Playback pauses independently of the job; the shared global Cancel control stops a running worker.

The selected step provides:

- Complex amplitudes and phase angles for every basis state.
- Computational-basis probabilities.
- Per-qubit reduced Bloch vector, P(1), purity Tr(ρ²), and entropy −Tr(ρ log₂ρ).
- State normalization and complex128 statevector payload, exactly 16 × 2ⁿ bytes. This payload excludes circuit objects, snapshots, interpreter and library overhead; the RSS watchdog monitors the real worker memory separately.

For a pure full-register state, a single qubit's positive entropy indicates entanglement with the rest of the register. This local entropy is not a complete multipartite entanglement characterization. Phase is undefined for zero-amplitude states and is displayed as unavailable. A state norm of 1 is the expected normalization, not a model-accuracy metric.

The **Final program readout** remains the final circuit's histogram regardless of debugger position. Ideal state displays never incorporate configured noise; histogram counts do. Measurement annotations do not collapse earlier snapshots. Gate depolarization applies to the actual supported basis gates, and readout bit flips apply to each final detector bit.

All programs are saved as experiment runs in SQLite. History restores both source configuration and the recorded trace. JSON exports include every snapshot; CSV exports contain the final distribution. Program text and executed QASM have separate downloads, so edits are never silently presented as executed code.

## General experiments

| Experiment | Executed computation | Independent check / interpretation |
| --- | --- | --- |
| Bell / GHZ | H plus CX entangling circuit | Correlated probabilities and local reduced states |
| Interference | H RZ(φ) H | P(0) = cos²(φ/2) |
| Grover | Marked-state phase oracle and diffusion | sin²((2r+1) asin(1/√N)); oracle is supplied, not hidden external data |
| QFT / inverse QFT | H, controlled phases and swaps | Classical positive/negative exponent DFT amplitudes, up to global phase |
| QPE | Controlled phase powers plus inverse QFT | Exact binary phase when representable; finite-resolution distribution otherwise |
| Deutsch–Jozsa | Constant or balanced parity oracle | All-zero input result means constant; nonzero parity mask means balanced |
| Superdense coding | Bell resource, local encoding, joint decoding | Two recovered bits; requires shared entanglement and one transmitted qubit |
| Teleportation | State preparation, Bell resource, coherent corrections | Ideal receiver-state fidelity; deferred-measurement equivalent, not actual remote transmission |
| VQE | Four-angle RY/CNOT variational circuit | Exact 4×4 eigensolver for H = −Z0 − Z1 + g X0X1; noiseless training |
| CHSH | Bell state and four separate rotated-basis measurements | Ideal 2√2 vs classical bound 2; finite sampled correlation table includes noise |

Diagnostics are **ideal/reference calculations unless explicitly labelled sampled**. This distinction remains visible when noise is enabled. CHSH makes four measurement-setting batches plus the displayed computational-basis Bell readout, each with the configured shots. VQE expectations are analytical, so noise controls affect its final readout rather than training. Native depth counts the supported simulator basis, not a routed physical-device gate depth. No simulation establishes quantum advantage by its runtime.

## Limits and future work

Machine limits are 8 qubits and 96 instructions, within the service's configured global caps. General algorithms use up to 6 work qubits plus one eigenstate/ancilla qubit; other circuit-builder jobs retain the 12-qubit ceiling. Every job shares the existing timeout, memory watchdog, and single concurrency slot.

Dynamic measurements, reset channels, full OpenQASM, error correction, arbitrary user Python and real QPU access are outside this release. They are not represented by fake controls or fabricated results.
