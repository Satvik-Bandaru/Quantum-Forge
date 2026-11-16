# Connected physical laboratory v0.6

The user explicitly authorizes ordinary implementation milestones without further design approval. Continue the existing uncommitted v0.5 application in place; preserve history, photonics, original modules and low-graphics 3D behavior.

## Scope and approach

The fresh baseline passes 343 Python tests and 35 browser tests. Typed ports, finite-pulse Lindblad dynamics, readout sampling, persistence, compute bounds and 3D navigation already exist. This phase fills the remaining physical-workflow gaps instead of rebuilding them.

Use a bounded lumped thermal network (fixed room boundary, intermediate stages and mixing chamber) with explicit heat capacity, load, thermal conductance and cooling power. Preserve the previous exponential model as a selectable legacy mode so historical configurations remain reproducible. This is an educational thermal circuit, not a calibrated dilution refrigerator or helium-cycle model. Its computed mixing-chamber temperature feeds the existing thermal population and transition rates.

A manufacturer-specific refrigeration model would require unavailable calibration data. A decorative temperature animation would not meet the request. The thermal circuit is the implementer's choice because conservation and analytical limiting cases are independently testable.

Add explicit typed instrument signals, calibration status and uncertainty provenance. Distinguish declared settings, predicted signals, sampled measurements and estimates derived from sampled calibration evidence. Disconnected or faulted ports must not imply live signals.

Extend the bounded experiment engine with amplitude calibration and an explicit dephasing protocol, retaining existing Rabi/Ramsey/echo/T1/sweeps/readout calibration. Calibration must derive estimates from returned counts, report resolution/uncertainty and limitations, and never silently rewrite settings. Finite-shot intervals must behave sensibly even at zero/all-success counts.

Extend the existing Connected Instruments screen with thermal configuration and computed stage information, calibration evidence, signal provenance, immutable pinned-run comparison and contextual navigation from existing 3D equipment. Preserve accessible controls and mobile layout. A new room or new renderer is outside scope.

## Acceptance

- Thermal limiting cases, energy balance, numerical accuracy and failure handling are tested.
- Configured heat load affects temperature and actual quantum predictions.
- Signal compatibility, calibration evidence, sampled uncertainties and saved-run replay are verified.
- Browser workflow configures thermal network, runs a backend experiment, modifies controls, compares and restores History.
- All existing tests/build/startup checks remain green; docs and downloadable source package are refreshed.
- Only bounded free local computation is enabled. No paid infrastructure or hardware fidelity claim.
