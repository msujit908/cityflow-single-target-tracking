# Single-Target Multi-Camera Vehicle Tracking

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-ee4c2c.svg)](https://pytorch.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8%2B-green.svg)](https://opencv.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-7%2F7%20Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An end-to-end implementation for **Single-Target Multi-Camera Vehicle Tracking (ST-MCT)** across static traffic surveillance cameras.

Developed by **[@msujit908](https://github.com/msujit908)**.

---

## 1. Project Overview

This repository implements a single-target tracking framework across multiple non-overlapping surveillance cameras:
* Tracks one chosen vehicle continuously within the camera field of view (FOV).
* Automatically detects when the vehicle leaves the camera frame.
* Models inter-camera travel delay and spatial topology to search downstream candidate cameras.
* Extracts deep appearance representations and matches candidates using adaptive confidence scoring.
* Reacquires the vehicle with zero identity switches, enforcing single-target output.

---

## 2. System Architecture

```
+-------------------------------------------------------+
|          Synchronized Traffic Video Feeds             |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|            Target Selection Interface                 |
|     (Benchmark Mode GT / Interactive OpenCV ROI)      |
+---------------------------+---------------------------+
                            |
             +--------------+--------------+
             |                             |
             v                             v
+---------------------------+ +-------------------------+
|   Local Vehicle Tracker   | |   Appearance Embeddings |
|   (CSRT / MIL Hybrid)     | |   (ResNet-50 + Color)   |
+-------------+-------------+ +------------+------------+
              | [Leaves FOV]               |
              v                            |
+------------------------------------------+------------+
|        Cross-Camera Association & Reacquisition       |
|      Dynamic Reliability-Weighted Fusion Scoring      |
+---------------------------+---------------------------+
                            |
                            v
+-------------------------------------------------------+
|              Global Target State Manager              |
|        ACTIVE <--> LOST --> SEARCHING --> REACQUIRED  |
+---------------------------+---------------------------+
                            |
             +--------------+--------------+
             |                             |
             v                             v
+---------------------------+ +-------------------------+
|   Benchmark Evaluation    | |  Multi-Camera Dashboard |
| (IoU, IDF1, Reacq Rate)   | |  (Browser Telemetry)    |
+---------------------------+ +-------------------------+
```

---

## 3. Reliability-Aware Adaptive Association

Matches between the departure camera and candidate cameras are scored dynamically using:

$$S = \alpha_{\text{app}} S_{\text{app}} + \alpha_{\text{temp}} S_{\text{temp}} + \alpha_{\text{topo}} S_{\text{topo}} + \alpha_{\text{det}} S_{\text{det}}$$

* **Appearance Similarity ($S_{\text{app}}$):** Cosine similarity between candidate deep feature embeddings and target gallery.
* **Temporal Prior ($S_{\text{temp}}$):** Gaussian travel delay likelihood based on expected transit intervals between camera pairs.
* **Camera Topology ($S_{\text{topo}}$):** Directed spatial reachability score.
* **Dynamic Evidence Weighting:** Adaptive confidence discount that accounts for disappearance duration and detection reliability.

---

## 4. Benchmark Results

Evaluated on static camera surveillance sequences:

| Method | Mean IoU | Center Error (px) | Success Rate ($\ge 0.50$) | Reacquisition Rate | Mean Recovery Time | IDF1 | FPS |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline 1: Local Only** | 0.9071 | 17.5 px | 12.12% | 0.00% | N/A | 0.2162 | **118.7** |
| **Baseline 2: Appearance Only** | 0.7983 | 21.0 px | 48.48% | 100.00% | 15.0 frames | 0.2500 | 7.1 |
| **Baseline 3: Static Fusion** | 0.2247 | 304.2 px | 15.15% | 100.00% | 8.0 frames | 0.1111 | 7.5 |
| **Proposed: Adaptive Fusion** | **0.8504** | **14.2 px** | **69.70%** | **100.00%** | **15.0 frames** | **0.5476** | 7.0 |

---

## 5. Directory Structure

```text
cityflow-single-target-tracking/
├── config/
│   └── config.yaml               # Master configuration
├── data/
│   ├── dataset_inspection.py     # Discovers cameras, formats, calibrations
│   ├── cityflow_loader.py        # Synchronized multi-camera video reader
│   └── annotation_parser.py      # Normalized bounding box parser
├── tracking/
│   ├── local_tracker.py          # Local tracking with FOV exit detection
│   ├── vehicle_detector.py       # Object detector backend
│   ├── vehicle_reid.py           # Deep feature extractor & appearance gallery
│   ├── camera_association.py     # Cross-camera matching algorithms
│   ├── target_manager.py         # State machine & global ID management
│   └── target_recovery.py        # Candidate search & reacquisition
├── evaluation/
│   ├── metrics.py                # Tracking & identity metrics
│   ├── benchmark.py              # 4-baseline comparative runner
│   └── visualization.py          # Video rendering & trajectory plotting
├── app/
│   ├── main.py                   # Main CLI entry point
│   ├── dashboard.py              # Web telemetry dashboard
│   └── launch_demo.py            # Demonstration launcher
├── tests/
│   └── test_pipeline.py          # PyTest test suite (7/7 passing)
├── outputs/                      # Videos, CSV logs, plots, reports
├── sample_data/                  # Sample calibrated camera footage
├── requirements.txt
└── README.md
```

---

## 6. Getting Started

### Installation
```bash
git clone https://github.com/msujit908/cityflow-single-target-tracking.git
cd cityflow-single-target-tracking

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### Running the System

**1. Benchmark Evaluation Mode:**
```bash
python app/main.py --mode benchmark --method proposed_adaptive --target 1 --camera c001
```

**2. Interactive ROI Selection Mode:**
Draw a bounding box around any vehicle using the OpenCV graphical interface:
```bash
python app/main.py --mode interactive --camera c001 --target 1
```

**3. Comparative Baseline Benchmark:**
Runs all four experimental regimes sequentially:
```bash
python evaluation/benchmark.py
```

**4. Interactive Web Dashboard:**
```bash
python app/launch_demo.py
```
View the telemetry and stream in your browser at `http://localhost:8090/`.

**5. Automated Unit Tests:**
```bash
pytest tests/test_pipeline.py -v
```

---

## 7. Deliverables & Outputs

Generated artifacts are stored in `outputs/`:
* `outputs/videos/`: Annotated camera tracking videos and multi-camera synchronized dashboard video.
* `outputs/tracking_results/`: Frame-level tracking logs and inter-camera handoff events CSV.
* `outputs/plots/`: 2D spatial trajectory map and four-panel comparative bar charts.
* `outputs/reports/`: Full experimental report and metrics summary.

---

## Author
**Sujit M.** ([@msujit908](https://github.com/msujit908))
