# TOTeM Conformance Checking

This repository contains the implementation of **object-centric conformance checking on Temporal Object Type Models (TOTeM)**.

Conformance checking compares real-world behavior with normative process models to detect deviations in business processes. Unlike existing workflow-based approaches (e.g., object-centric Petri nets), TOTeM models can explicitly represent **temporal relations**, **log cardinalities**, and **event cardinalities** between object types. This enables detecting deviations such as violations of the lean management pull principle or quality assurance constraints that workflow-based approaches cannot capture.

This tool computes **fitness** and **precision** metrics for all three TOTeM dimensions and provides an interactive web-based visualization of the conformance checking results.

![TOTeM Conformance Checking Explorer](totem-tool.png)

*The TOTeM conformance checking explorer showing fitness/precision values, event cardinality by activity, temporal relations by relation type, and log cardinality by relation type for the container logistics event log.*

## Quick Start

To run the application locally or contribute, please see our **[Developer Guide](DEVELOPMENT.md)**.

**One-time Setup:**
```bash
npm run setup-env
```

**Start App:**
```bash
npm run electron-dev
```

**Build Windows Executable:**
```bash
npm run build-all
```

## Distribution

The Windows executable is built using Electron and includes everything needed to run the application:
- Backend server and TOTeM library (built with PyInstaller)
- Frontend (served with Express.js)

## Documentation

- [QUICK_START.md](QUICK_START.md) - Development setup
- [BUILD_GUIDE.md](docs/BUILD_GUIDE.md) - Building executables
- [SETUP.md](docs/SETUP.md) - Detailed setup instructions
- [GIT_GUIDE.md](docs/GIT_GUIDE.md) - Git management guidelines

## Evaluation

The conformance checking approach was evaluated on 8 publicly accessible event logs. For each log, 11 TOTeM models were discovered using the TOTeM miner with tau values from 0 to 1 (step size 0.1), resulting in 88 TOTeM models in total. All experiments were run on an Apple M4 Pro chip with 24 GB RAM.

### Fitness and Precision vs. Tau

Fitness and precision balance each other as expected: at tau = 1 the miner considers all behavior and fitness is always 1, while precision is lowest. Lowering tau towards 0 increases precision and decreases fitness.

![Fitness and Precision vs. Tau](totem_lib/evaluation/conformance_metrics_vs_tau_combined.png)

*Fitness (top row) and precision (bottom row) for the temporal, log cardinality, and event cardinality dimensions across different tau values for all 8 event logs.*

### Runtime

For the evaluated logs, the algorithm scales linearly with the number of events and objects, and exponentially with the number of TOTeM arcs. For 7 of the 8 event logs the computation finishes in under 10 seconds on consumer hardware. Only the Age of Empires log (>2.3M events, >300K objects, 30 types) takes an average of ~350 seconds.

![Conformance Checking Runtime](totem_lib/evaluation/conformance_time_combined_arcs.png)

*Runtime in seconds over the number of events, number of objects, and number of TOTeM arcs (y-axis and event/object x-axes are logarithmic).*

Raw evaluation results and additional graphs are available in [`totem_lib/evaluation/`](totem_lib/evaluation/).
