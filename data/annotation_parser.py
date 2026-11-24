"""
CityFlow Annotation Parser.

Parses multi-camera tracking annotations into the unified CityFlow data structure:
{
    "camera_id": camera_id,
    "frame_id": frame_id,
    "vehicle_id": vehicle_id,
    "bbox": [x, y, width, height]
}

Supports:
1. MOTChallenge-style per-camera gt.txt (<frame>, <id>, <x>, <y>, <w>, <h>, <conf>, ...)
2. Unified scene-level gt.txt (<camera_id>, <id>, <frame>, <x>, <y>, <w>, <h>, ...)
3. Per-frame or multi-camera JSON annotations
4. Detection baseline files (det/det.txt, det_yolo3.txt)
"""

import os
import json
import glob
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple


class CityFlowAnnotationParser:
    """
    Parser that normalizes heterogeneous CityFlow annotations into unified records.
    """

    def __init__(self):
        # Master list of unified annotation dictionaries
        self.annotations: List[Dict[str, Any]] = []

        # Fast lookup indexes:
        # (camera_id, frame_id) -> list of annotations
        self.frame_index: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
        # vehicle_id -> list of annotations sorted by frame
        self.vehicle_index: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        # (vehicle_id, camera_id) -> list of annotations
        self.vehicle_camera_index: Dict[Tuple[int, str], List[Dict[str, Any]]] = defaultdict(list)

    def parse_camera_gt(self, camera_id: str, gt_path: str) -> List[Dict[str, Any]]:
        """
        Parses a camera-specific ground truth file.
        Format: <frame_id>, <vehicle_id>, <x>, <y>, <w>, <h>, <conf>, <x_world>, <y_world>, <z_world>
        """
        if not os.path.exists(gt_path):
            return []

        parsed = []
        with open(gt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.replace(" ", ",").split(",") if p.strip()]
                if len(parts) >= 6:
                    try:
                        frame_id = int(float(parts[0]))
                        vehicle_id = int(float(parts[1]))
                        x = int(float(parts[2]))
                        y = int(float(parts[3]))
                        w = int(float(parts[4]))
                        h = int(float(parts[5]))

                        record = {
                            "camera_id": camera_id,
                            "frame_id": frame_id,
                            "vehicle_id": vehicle_id,
                            "bbox": [x, y, w, h]
                        }
                        self._add_record(record)
                        parsed.append(record)
                    except ValueError:
                        continue
        return parsed

    def parse_unified_scene_gt(self, gt_path: str) -> List[Dict[str, Any]]:
        """
        Parses a unified scene-level ground truth file.
        Format: <camera_id> <vehicle_id> <frame_id> <x> <y> <w> <h> ...
        """
        if not os.path.exists(gt_path):
            return []

        parsed = []
        with open(gt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.replace(" ", ",").split(",") if p.strip()]
                if len(parts) >= 7:
                    try:
                        # Auto-detect whether first column is camera or frame
                        if parts[0].startswith("c0") or parts[0].startswith("cam"):
                            camera_id = parts[0]
                            vehicle_id = int(float(parts[1]))
                            frame_id = int(float(parts[2]))
                            x, y, w, h = [int(float(v)) for v in parts[3:7]]
                        else:
                            frame_id = int(float(parts[0]))
                            vehicle_id = int(float(parts[1]))
                            camera_id = parts[2] if (parts[2].startswith("c0") or parts[2].startswith("cam")) else "c001"
                            x, y, w, h = [int(float(v)) for v in parts[3:7]]

                        record = {
                            "camera_id": camera_id,
                            "frame_id": frame_id,
                            "vehicle_id": vehicle_id,
                            "bbox": [x, y, w, h]
                        }
                        self._add_record(record)
                        parsed.append(record)
                    except (ValueError, IndexError):
                        continue
        return parsed

    def _add_record(self, record: Dict[str, Any]):
        """Internal helper to insert into master list and fast lookup tables."""
        self.annotations.append(record)
        cid = record["camera_id"]
        fid = record["frame_id"]
        vid = record["vehicle_id"]

        self.frame_index[(cid, fid)].append(record)
        self.vehicle_index[vid].append(record)
        self.vehicle_camera_index[(vid, cid)].append(record)

    def get_bboxes_for_frame(self, camera_id: str, frame_id: int) -> List[Dict[str, Any]]:
        """Returns all vehicle bounding box annotations for a given camera and frame."""
        return self.frame_index.get((camera_id, frame_id), [])

    def get_target_bbox(self, camera_id: str, frame_id: int, target_id: int) -> Optional[List[int]]:
        """Returns the specific target vehicle bbox [x, y, w, h] if present in camera and frame."""
        for rec in self.frame_index.get((camera_id, frame_id), []):
            if rec["vehicle_id"] == target_id:
                return rec["bbox"]
        return None

    def get_vehicle_timeline(self, vehicle_id: int) -> List[Dict[str, Any]]:
        """
        Returns chronological timeline of vehicle appearances across all cameras.
        """
        recs = sorted(self.vehicle_index.get(vehicle_id, []), key=lambda r: r["frame_id"])
        cams = sorted(list(set(r["camera_id"] for r in recs)))
        timeline = []
        for cid in cams:
            c_recs = [r for r in recs if r["camera_id"] == cid]
            f_ids = [r["frame_id"] for r in c_recs]
            timeline.append({
                "camera_id": cid,
                "first_frame": min(f_ids),
                "last_frame": max(f_ids),
                "total_frames": len(f_ids)
            })
        timeline.sort(key=lambda t: t["first_frame"])
        return timeline

    def get_all_vehicle_ids(self) -> List[int]:
        """Returns sorted list of all unique vehicle IDs."""
        return sorted(list(self.vehicle_index.keys()))

    def get_cross_camera_vehicle_ids(self) -> List[int]:
        """Returns list of vehicle IDs that appear in 2 or more cameras."""
        cross = []
        for vid in self.get_all_vehicle_ids():
            cams = set(r["camera_id"] for r in self.vehicle_index[vid])
            if len(cams) > 1:
                cross.append(vid)
        return cross
