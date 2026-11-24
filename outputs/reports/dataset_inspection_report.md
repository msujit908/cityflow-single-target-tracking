# CityFlow Dataset Inspection & Multi-Camera Topology Report
**Analyzed Dataset Root:** `E:\ML101\cityflow-single-target-tracking\sample_data\cityflow_sample`

## 1. Executive Summary
- **Total Camera Views Discovered:** 2
- **Camera Identifiers:** c001, c002
- **Annotation Format(s) Detected:** mot_gt_txt
- **Total Unique Vehicle Identities:** 3
- **Cross-Camera Handoff Identities:** 1
- **Single-Camera Local Identities:** 2

## 2. Multi-Camera Topology & Cross-Camera Handoffs
| Vehicle ID | Observed In Cameras | Spatial-Temporal Camera Timeline |
| :--- | :--- | :--- |
| **Vehicle 1** | c001, c002 | c001 [F1-F17] &rarr; c002 [F35-F50] |

### Observed Ground-Truth Transitions & Travel Delays
| Target ID | Source Camera | Exit Frame | Destination Camera | Entry Frame | Travel Delay (Frames) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | c001 | 17 | c002 | 35 | **18 frames** |

## 3. Camera Streams Specification
| Camera ID | Media Type | Resolution | FPS | Frame Count | Calibration | Active Vehicles |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **c001** | video | 1920x1080 | 30.0 | 121 | Available | 1, 2 |
| **c002** | video | 1920x1080 | 30.0 | 121 | Available | 1, 3 |

## 4. Vehicle Bounding Box & Scale Characteristics
- **Sample Bounding Boxes Analyzed:** 65
- **Average Bounding Box Dimensions:** 265.0 x 220.8 px
- **Average Aspect Ratio (H/W):** 0.91
- **Width Range:** [129 px, 501 px]
- **Height Range:** [102 px, 390 px]

---
*Generated automatically by CityFlow Single-Target Tracking Dataset Inspection Utility.*