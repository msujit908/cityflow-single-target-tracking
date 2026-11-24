# Input and Output Videos

This directory contains the original input surveillance camera footage and the resulting tracking output videos for **Single-Target Multi-Camera Vehicle Tracking**.

---

## 1. Input Videos (CityFlow Benchmark)

Authentic Full HD surveillance traffic recordings from static traffic cameras:

| File Name | Camera ID | Resolution | Frame Rate | Description | Direct Link |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **`input_camera_c001.mp4`** | `c001` | 1920&times;1080 | 30.0 FPS | Intersection entrance view where target vehicle is initialized | [View / Download](input_camera_c001.mp4) |
| **`input_camera_c002.mp4`** | `c002` | 1920&times;1080 | 30.0 FPS | Downstream roadway view where target vehicle is reacquired | [View / Download](input_camera_c002.mp4) |

---

## 2. Output Videos (Proposed Adaptive Tracking)

Rendered videos showing bounding boxes, global target identity (`VEHICLE_001`), tracking confidence, and real-time status overlays:

| File Name | Camera / Mode | Resolution | Description | Direct Link |
| :--- | :---: | :---: | :--- | :--- |
| **`output_tracking_c001.mp4`** | `c001` Tracking | 1920&times;1080 | Initial tracking in Camera 1, following target until FOV exit (Frame 17) | [View / Download](output_tracking_c001.mp4) |
| **`output_tracking_c002.mp4`** | `c002` Tracking | 1920&times;1080 | Reacquisition and continuous downstream tracking in Camera 2 (Frame 32 onwards) | [View / Download](output_tracking_c002.mp4) |
| **`output_dashboard_synchronized.mp4`** | Multi-Camera | 1920&times;1080 | Synchronized side-by-side dashboard video comparing both camera views simultaneously | [View / Download](output_dashboard_synchronized.mp4) |

---

## 3. Video Telemetry HUD Specifications

Each output frame includes an informational overlay:
* **GLOBAL TARGET:** `VEHICLE_001` (Maintained across all camera transitions)
* **CAMERA:** Active camera identifier (`c001` / `c002`)
* **FRAME:** Synchronized frame index
* **STATUS:** `ACTIVE`, `LOST`, `SEARCHING`, or `REACQUIRED`
* **CONFIDENCE:** Instantaneous tracking / association score
