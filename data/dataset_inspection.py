"""
CityFlow Dataset Inspection Utility.

Scans and analyzes CityFlow / CityFlowV2 or AICity tracking datasets without making
assumptions about directory depth, naming conventions, camera identifiers, or annotation schemas.

Identifies:
1. Camera IDs and hierarchical organization (scenes, subsets, cameras).
2. Media modalities (video containers e.g. vdo.avi, vdo.mp4 vs frame sequences img1/*.jpg).
3. Frame resolution, frame count, and FPS.
4. Camera calibration files (intrinsics K, distortion, homography H, extrinsics).
5. ROI masks (roi.jpg, roi.png).
6. Ground-truth vehicle annotations and identity IDs.
7. Multi-camera vehicle transitions, travel times, and spatial-temporal relationships.
8. Outputs comprehensive Markdown inspection report and machine-readable JSON summary.
"""

import os
import sys
import glob
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Optional, Tuple

import cv2
import numpy as np
import yaml


class CityFlowDatasetInspector:
    """
    Intelligent scanner and analyzer for CityFlow multi-camera vehicle tracking datasets.
    """

    def __init__(self, dataset_root: Optional[str] = None, config_path: str = "config/config.yaml"):
        self.config: Dict[str, Any] = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}

        if dataset_root:
            self.root = Path(dataset_root)
        elif "dataset" in self.config and "root" in self.config["dataset"]:
            self.root = Path(self.config["dataset"]["root"])
        else:
            self.root = Path("sample_data/cityflow_sample")

        self.inspection_results: Dict[str, Any] = {}

    def inspect(self) -> Dict[str, Any]:
        """
        Runs comprehensive inspection on the dataset root.
        """
        print(f"[*] Commencing CityFlow Dataset Inspection on: {self.root.resolve()}")
        if not self.root.exists():
            raise FileNotFoundError(f"Dataset root does not exist: {self.root.resolve()}")

        # 1. Discover all camera directories
        camera_nodes = self._find_camera_nodes(self.root)
        print(f"[*] Discovered {len(camera_nodes)} camera sequences across dataset structure.")

        cameras_info: Dict[str, Any] = {}
        global_identities: Dict[int, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))
        all_bboxes: List[List[int]] = []
        annotation_formats_detected = set()

        for cam_id, cam_path in sorted(camera_nodes.items()):
            cam_data = self._inspect_camera_node(cam_id, cam_path)
            cameras_info[cam_id] = cam_data
            if cam_data.get("annotation_format"):
                annotation_formats_detected.add(cam_data["annotation_format"])

            for vid, frames in cam_data["vehicle_frames"].items():
                global_identities[vid][cam_id].extend(frames)

            all_bboxes.extend(cam_data["sample_bboxes"])

        # 2. Multi-camera cross-identity analysis
        cross_camera_identities = {}
        single_camera_identities = {}
        transition_events = []

        for vid, cams in sorted(global_identities.items()):
            if len(cams) > 1:
                cam_timeline = []
                for cid, f_list in cams.items():
                    cam_timeline.append({
                        "camera_id": cid,
                        "first_frame": min(f_list),
                        "last_frame": max(f_list),
                        "total_frames": len(f_list)
                    })
                cam_timeline.sort(key=lambda x: x["first_frame"])
                cross_camera_identities[vid] = {
                    "cameras": list(cams.keys()),
                    "num_cameras": len(cams),
                    "timeline": cam_timeline
                }

                # Compute pairwise transitions
                for i in range(len(cam_timeline) - 1):
                    src = cam_timeline[i]
                    dst = cam_timeline[i + 1]
                    delay = dst["first_frame"] - src["last_frame"]
                    transition_events.append({
                        "vehicle_id": vid,
                        "from_camera": src["camera_id"],
                        "exit_frame": src["last_frame"],
                        "to_camera": dst["camera_id"],
                        "entry_frame": dst["first_frame"],
                        "travel_delay_frames": delay
                    })
            else:
                cid = list(cams.keys())[0]
                f_list = cams[cid]
                single_camera_identities[vid] = {
                    "camera_id": cid,
                    "first_frame": min(f_list),
                    "last_frame": max(f_list),
                    "total_frames": len(f_list)
                }

        # 3. Discover camera timestamps and topology
        topology_info = self._discover_topology(self.root)
        timestamps_info = self._discover_timestamps(self.root)

        # 4. Compute bbox scale statistics
        scale_stats = {}
        if all_bboxes:
            widths = [b[2] for b in all_bboxes]
            heights = [b[3] for b in all_bboxes]
            aspect_ratios = [b[3] / max(1, b[2]) for b in all_bboxes]
            scale_stats = {
                "sample_count": len(all_bboxes),
                "mean_width": float(np.mean(widths)),
                "mean_height": float(np.mean(heights)),
                "mean_aspect_ratio_h_w": float(np.mean(aspect_ratios)),
                "min_width": int(np.min(widths)),
                "max_width": int(np.max(widths)),
                "min_height": int(np.min(heights)),
                "max_height": int(np.max(heights))
            }

        self.inspection_results = {
            "dataset_root": str(self.root.resolve()),
            "total_cameras": len(cameras_info),
            "camera_ids": list(cameras_info.keys()),
            "annotation_formats_detected": list(annotation_formats_detected),
            "total_unique_vehicles": len(global_identities),
            "cross_camera_vehicles_count": len(cross_camera_identities),
            "single_camera_vehicles_count": len(single_camera_identities),
            "cross_camera_identities": cross_camera_identities,
            "transition_events": transition_events,
            "cameras": cameras_info,
            "topology": topology_info,
            "timestamps": timestamps_info,
            "scale_stats": scale_stats
        }

        return self.inspection_results

    def _find_camera_nodes(self, root: Path) -> Dict[str, Path]:
        """
        Discovers camera directories by searching for video files, img1 folders, or gt.txt.
        """
        camera_nodes: Dict[str, Path] = {}

        # Search for video files (vdo.avi, vdo.mp4) or subfolders
        for p in root.rglob("*"):
            if p.is_file() and p.name in ["vdo.avi", "vdo.mp4"]:
                cam_dir = p.parent
                cam_id = cam_dir.name
                camera_nodes[cam_id] = cam_dir
            elif p.is_dir() and p.name == "img1":
                cam_dir = p.parent
                cam_id = cam_dir.name
                camera_nodes[cam_id] = cam_dir

        # Fallback: check directories matching c001, c002, cam_*, etc.
        if not camera_nodes:
            for p in root.rglob("*"):
                if p.is_dir() and (p.name.startswith("c0") or p.name.startswith("cam")):
                    camera_nodes[p.name] = p

        return camera_nodes

    def _inspect_camera_node(self, cam_id: str, cam_path: Path) -> Dict[str, Any]:
        """
        Inspects an individual camera directory for media, calibration, ROI, and annotations.
        """
        media_type = "unknown"
        media_path = None
        resolution = (0, 0)
        fps = 30.0
        frame_count = 0

        # Check for video file
        for v_name in ["vdo.mp4", "vdo.avi", f"{cam_id}.mp4", f"{cam_id}.avi"]:
            v_file = cam_path / v_name
            if v_file.exists():
                media_type = "video"
                media_path = str(v_file)
                cap = cv2.VideoCapture(str(v_file))
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    resolution = (w, h)
                cap.release()
                break

        # Check for frame sequence
        if media_type == "unknown":
            img_dir = cam_path / "img1" if (cam_path / "img1").is_dir() else cam_path
            img_files = sorted(glob.glob(str(img_dir / "*.jpg")) + glob.glob(str(img_dir / "*.png")))
            if img_files:
                media_type = "image_sequence"
                media_path = str(img_dir)
                frame_count = len(img_files)
                sample = cv2.imread(img_files[0])
                if sample is not None:
                    resolution = (sample.shape[1], sample.shape[0])

        # Check ROI mask
        has_roi = False
        roi_path = None
        for r_name in ["roi.jpg", "roi.png", f"{cam_id}_roi.jpg"]:
            r_file = cam_path / r_name
            if r_file.exists():
                has_roi = True
                roi_path = str(r_file)
                break

        # Check Calibration
        has_calibration = False
        calibration_info = {}
        for c_name in ["calibration.txt", f"{cam_id}_calibration.txt", "calib.txt"]:
            c_file = cam_path / c_name
            if c_file.exists():
                has_calibration = True
                calibration_info = self._parse_calibration(c_file)
                break

        # Parse Annotations
        ann_format, vehicle_frames, sample_bboxes = self._parse_annotations(cam_id, cam_path)

        return {
            "camera_id": cam_id,
            "path": str(cam_path),
            "media_type": media_type,
            "media_path": media_path,
            "resolution": resolution,
            "fps": fps,
            "frame_count": frame_count,
            "has_roi": has_roi,
            "roi_path": roi_path,
            "has_calibration": has_calibration,
            "calibration": calibration_info,
            "annotation_format": ann_format,
            "active_vehicles": sorted(list(vehicle_frames.keys())),
            "vehicle_frames": vehicle_frames,
            "sample_bboxes": sample_bboxes[:50]
        }

    def _parse_calibration(self, calib_file: Path) -> Dict[str, Any]:
        """Parses camera calibration file containing intrinsics, extrinsics, or homography."""
        info = {"file": str(calib_file), "raw_lines": []}
        try:
            with open(calib_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            info["raw_lines"] = lines[:15]
            # Check for matrix blocks
            matrices = []
            current_mat = []
            for l in lines:
                if l.startswith("#"):
                    continue
                parts = l.split()
                try:
                    vals = [float(p) for p in parts]
                    if len(vals) in [3, 4]:
                        current_mat.append(vals)
                        if len(current_mat) == 3:
                            matrices.append(current_mat)
                            current_mat = []
                except ValueError:
                    continue
            if matrices:
                info["matrices_found"] = len(matrices)
                info["primary_matrix"] = matrices[0]
        except Exception as e:
            info["parse_error"] = str(e)
        return info

    def _parse_annotations(self, cam_id: str, cam_path: Path) -> Tuple[Optional[str], Dict[int, List[int]], List[List[int]]]:
        """
        Detects and parses annotation format:
        1. MOT format gt/gt.txt: <frame>, <id>, <x>, <y>, <w>, <h>, <conf>, <x_w>, <y_w>, <z_w>
        2. Root gt.txt
        3. Detection files det/det.txt
        """
        vehicle_frames: Dict[int, List[int]] = defaultdict(list)
        sample_bboxes: List[List[int]] = []
        fmt = None

        candidate_gt = [
            cam_path / "gt" / "gt.txt",
            cam_path / "gt.txt",
            cam_path / "det" / "det.txt"
        ]

        gt_file = None
        for cg in candidate_gt:
            if cg.exists():
                gt_file = cg
                break

        if gt_file:
            fmt = "mot_gt_txt"
            with open(gt_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [p.strip() for p in line.replace(" ", ",").split(",") if p.strip()]
                    if len(parts) >= 6:
                        try:
                            f_idx = int(float(parts[0]))
                            vid = int(float(parts[1]))
                            x = int(float(parts[2]))
                            y = int(float(parts[3]))
                            w = int(float(parts[4]))
                            h = int(float(parts[5]))

                            if vid > 0:
                                vehicle_frames[vid].append(f_idx)
                                if len(sample_bboxes) < 100:
                                    sample_bboxes.append([x, y, w, h])
                        except ValueError:
                            continue

        return fmt, vehicle_frames, sample_bboxes

    def _discover_topology(self, root: Path) -> Dict[str, Any]:
        """Discovers topology files (topology.json or topology.txt)."""
        topo_files = list(root.rglob("topology.json")) + list(root.rglob("topology.txt"))
        if topo_files:
            try:
                with open(topo_files[0], "r", encoding="utf-8") as f:
                    if topo_files[0].suffix == ".json":
                        return json.load(f)
                    return {"raw_text": f.read()}
            except Exception as e:
                return {"error": str(e)}
        return {"status": "none_found_in_root"}

    def _discover_timestamps(self, root: Path) -> Dict[str, Any]:
        """Discovers camera timestamp synchronization file."""
        ts_files = list(root.rglob("cam_timestamp.txt")) + list(root.rglob("cam_timestamps.txt"))
        timestamps = {}
        if ts_files:
            try:
                with open(ts_files[0], "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamps[parts[0]] = float(parts[1])
            except Exception as e:
                timestamps["error"] = str(e)
        return timestamps

    def generate_report(self, output_path: str = "outputs/reports/dataset_inspection_report.md") -> str:
        """
        Generates a professional Markdown inspection report.
        """
        if not self.inspection_results:
            self.inspect()

        res = self.inspection_results
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        lines = [
            "# CityFlow Dataset Inspection & Multi-Camera Topology Report",
            f"**Analyzed Dataset Root:** `{res['dataset_root']}`\n",
            "## 1. Executive Summary",
            f"- **Total Camera Views Discovered:** {res['total_cameras']}",
            f"- **Camera Identifiers:** {', '.join(res['camera_ids'])}",
            f"- **Annotation Format(s) Detected:** {', '.join(res['annotation_formats_detected']) or 'None'}",
            f"- **Total Unique Vehicle Identities:** {res['total_unique_vehicles']}",
            f"- **Cross-Camera Handoff Identities:** {res['cross_camera_vehicles_count']}",
            f"- **Single-Camera Local Identities:** {res['single_camera_vehicles_count']}\n",
            "## 2. Multi-Camera Topology & Cross-Camera Handoffs",
            "| Vehicle ID | Observed In Cameras | Spatial-Temporal Camera Timeline |",
            "| :--- | :--- | :--- |"
        ]

        for vid, data in res["cross_camera_identities"].items():
            tl_str = " &rarr; ".join([f"{t['camera_id']} [F{t['first_frame']}-F{t['last_frame']}]" for t in data["timeline"]])
            cams_str = ", ".join(data["cameras"])
            lines.append(f"| **Vehicle {vid}** | {cams_str} | {tl_str} |")

        lines.extend([
            "\n### Observed Ground-Truth Transitions & Travel Delays",
            "| Target ID | Source Camera | Exit Frame | Destination Camera | Entry Frame | Travel Delay (Frames) |",
            "| :---: | :---: | :---: | :---: | :---: | :---: |"
        ])

        for tr in res["transition_events"]:
            lines.append(
                f"| **{tr['vehicle_id']}** | {tr['from_camera']} | {tr['exit_frame']} | "
                f"{tr['to_camera']} | {tr['entry_frame']} | **{tr['travel_delay_frames']} frames** |"
            )

        lines.extend([
            "\n## 3. Camera Streams Specification",
            "| Camera ID | Media Type | Resolution | FPS | Frame Count | Calibration | Active Vehicles |",
            "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |"
        ])

        for cid, cinfo in res["cameras"].items():
            res_str = f"{cinfo['resolution'][0]}x{cinfo['resolution'][1]}"
            calib_str = "Available" if cinfo["has_calibration"] else "None"
            v_str = ", ".join(map(str, cinfo["active_vehicles"]))
            lines.append(
                f"| **{cid}** | {cinfo['media_type']} | {res_str} | {cinfo['fps']} | "
                f"{cinfo['frame_count']} | {calib_str} | {v_str} |"
            )

        if res.get("scale_stats"):
            s = res["scale_stats"]
            lines.extend([
                "\n## 4. Vehicle Bounding Box & Scale Characteristics",
                f"- **Sample Bounding Boxes Analyzed:** {s['sample_count']}",
                f"- **Average Bounding Box Dimensions:** {s['mean_width']:.1f} x {s['mean_height']:.1f} px",
                f"- **Average Aspect Ratio (H/W):** {s['mean_aspect_ratio_h_w']:.2f}",
                f"- **Width Range:** [{s['min_width']} px, {s['max_width']} px]",
                f"- **Height Range:** [{s['min_height']} px, {s['max_height']} px]"
            ])

        lines.extend([
            "\n---",
            "*Generated automatically by CityFlow Single-Target Tracking Dataset Inspection Utility.*"
        ])

        report_content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        # Also save JSON summary
        json_path = output_path.replace(".md", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)

        print(f"[+] Dataset Inspection Report generated at: {output_path}")
        print(f"[+] Machine-readable summary saved at: {json_path}")
        return report_content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect CityFlow Multi-Camera Tracking Dataset")
    parser.add_argument("--root", type=str, default=None, help="Path to CityFlow dataset root")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Path to configuration YAML")
    parser.add_argument("--output", type=str, default="outputs/reports/dataset_inspection_report.md", help="Output Markdown report path")
    args = parser.parse_args()

    inspector = CityFlowDatasetInspector(dataset_root=args.root, config_path=args.config)
    inspector.generate_report(output_path=args.output)
