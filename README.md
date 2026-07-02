**Reliability-aware emergency routing for Connected Autonomous Vehicles under large-scale infrastructure disruption**

*Fully reproducible research framework accompanying our Reliability Engineering & System Safety manuscript.*

</p>

---

## Overview

This repository presents a complete research framework for reliability-aware routing of Connected Autonomous Vehicles (CAVs) operating in post-disaster transportation networks.

Unlike conventional vehicle routing approaches that assume a fully functional road and communication network, this framework explicitly models network reliability degradation and investigates how communication failures influence emergency medical service quality.

The framework integrates:

- Reliability-aware transportation network modeling
- Emergency vehicle routing with fuzzy time windows
- Multi-objective optimization
- Large-scale simulation
- Real-world disaster validation
- Automated publication-quality visualization

Every figure, table, animation, and report presented in the manuscript can be reproduced directly from this repository.

---

## Why this research?

Future autonomous transportation systems depend on reliable Vehicle-to-Infrastructure (V2I) communication.

During disasters such as widespread power outages, earthquakes, floods, or cyber-attacks, communication reliability rapidly deteriorates, reducing network connectivity and increasing travel delays.

This project investigates:

- How transportation network reliability affects emergency service quality.
- The critical reliability threshold where system performance collapses.
- Whether reliability-aware routing improves patient service rates.
- Which optimization algorithms perform best under degraded infrastructure.

---

## Scientific Contributions

- Reliability-aware CAV routing formulation with fuzzy time windows.
- Three-objective optimization balancing service quality, travel distance, and route reliability.
- Comprehensive benchmark of QiGA, GA, PSO, ALNS, TS, NSGA-II, and MOEA/D.
- Ten simulation experiments covering network degradation, fleet size, demand, priority, and algorithm performance.
- Real-world validation using the 2025 Iberian Peninsula blackout.
- Automated generation of publication-ready figures, tables, reports, MATLAB figures, and GIF animations.

---

### Main Framework (`code/`)

Contains the complete simulation framework used throughout the paper.

Key capabilities include:

- reliability-aware routing
- optimization algorithms
- experiment automation
- publication figures
- report generation

### Iberian Blackout Case Study (`case_study_iberia/`)

Implements the real-world validation using Madrid's transportation network.

Features include:

- OpenStreetMap network download
- blackout scenario generation
- geographic visualization
- animated GIF creation
- MATLAB figure generation

### 1. Core Concept Dashboard

<p align="center">
  <img src="Banner/GIF1_core_concept.gif" alt="Dashboard" width="500">
</p>

Shows the simultaneous evolution of:

- road reliability
- service rate
- blackout timeline
- awareness gap
- routing behaviour

---

### 2. Madrid Reliability Map

![](case_study_iberia/figures/gif/GIF2_madrid_map.gif)

Animated square-grid reliability evolution throughout the blackout.

---

### 3. Pareto Front Collapse

![](case_study_iberia/figures/gif/GIF3_pareto_collapse.gif)

Illustrates the reduction of feasible Pareto solutions as network reliability decreases.

---

### 4. Algorithm Convergence

![](case_study_iberia/figures/gif/GIF4_algorithm_race.gif)

Visual comparison of optimization performance for:

- QiGA
- NSGA-II
- MOEA/D
- GA
- ALNS

---

## Major Findings

| Finding | Observation |
|----------|-------------|
| Critical threshold | φ ≈ 0.82–0.85 marks rapid service collapse |
| Reliability-aware routing | Improves service rate by 18–35 percentage points |
| Fleet expansion | Cannot compensate for severely degraded networks |
| Priority routing | Protects critical patients during disruption |
| Best SOO | QiGA |
| Best MOO | MOEA/D |
| Hub failures | Produce substantially greater disruption than random failures |

---

## Case Study

The framework is validated using the **2025 Iberian Peninsula Blackout**.

The Madrid transportation network is reconstructed from OpenStreetMap and evaluated under four disruption scenarios representing the progression of the blackout.

The results demonstrate that reliability-aware routing substantially improves emergency medical service during severe infrastructure degradation.

![Banner](Banner/GIF2_madrid_map.gif)
---

## Citation

```bibtex
@article{razavi2026cav,
  title={Impact of Network Reliability on Service Quality in Connected Autonomous Vehicle Routing with Fuzzy Time Windows},
  author={Razavi, H. and others},
  journal={Reliability Engineering & System Safety},
  year={2026},
  note={Under Review}
}
```

---

## License

- Code: MIT License
- OpenStreetMap data: ODbL 1.0
- Madrid hospital data: CC BY 4.0

---

## Contact

**H. Razavi**

📧 hoomanrazavi68@gmail.com

For questions regarding datasets or implementation, please open an issue or contact the corresponding author.
