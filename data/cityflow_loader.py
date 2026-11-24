"""
CityFlow Multi-Camera Dataset Loader.

Loads real traffic video streams, calibration parameters, ROI masks, and
ground-truth vehicle tracking annotations for multi-camera vehicle tracking.
"""

import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Generator

import cv2
import numpy as np
import yaml

from data.annotation_parser import CityFlowAnnotationParser


class CityFlowLoader:
    """
    Synchronized multi-camera video and metadata loader for CityFlow.
    """

    def __init__(self,
                 dataset_root: Optional[str] = None,
                 scene: Optional[str] = None,
                 config_path: str = "config/config.yaml"):
        self.config: Dict[str, Any] = {}
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}

        # Resolve root
        if dataset_root:
            self.root = Path(dataset_root)
        elif "dataset" in self.config and "root" in self.config["dataset"]:
            self.root = Path(self.config["dataset"]["root"])
        else:
            self.root = Path("sample_data/cityflow_sample")

        self.scene = scene or self.config.get("dataset", {}).get("scene", "S01")

        # Discover camera paths
        self.cameras: Dict[str, Dict[str, Any]] = {}
        self.caps: Dict[str, cv2.VideoCapture] = {}
        self.annotation_parser = CityFlowAnnotationParser()
        self.timestamps: Dict[str, float] = {}

        self._initialize_dataset()

    def _initialize_dataset(self):
        """Discovers camera directories, opens video streams, and loads annotations."""
        if not self.root.exists():
            raise FileNotFoundError(f"CityFlow root does not exist: {self.root.resolve()}")

        # Locate cameras under scene or root
        search_dirs = [self.root / self.scene, self.root]
        cam_paths: Dict[str, Path] = {}

        for s_dir in search_dirs:
            if s_dir.exists():
                for p in s_dir.rglob("*"):
                    if p.is_file() and p.name in ["vdo.avi", "vdo.mp4"]:
                        cam_id = p.parent.name
                        cam_paths[cam_id] = p.parent
                    elif p.is_dir() and p.name == "img1":
                        cam_id = p.parent.name
                        cam_paths[cam_id] = p.parent

        if not cam_paths:
            # Fallback for camera folder names
            for p in self.root.rglob("*"):
                if p.is_dir() and (p.name.startswith("c0") or p.name.startswith("cam")):
                    cam_paths[p.name] = p

        print(f"[*] CityFlowLoader found {len(cam_paths)} cameras: {list(cam_paths.keys())}")

        for cam_id, cam_dir in sorted(cam_paths.items()):
            c_info = self._setup_camera(cam_id, cam_dir)
            self.cameras[cam_id] = c_info

        # Load timestamps if present
        for ts_name in ["cam_timestamp.txt", "cam_timestamps.txt"]:
            ts_p = self.root / self.scene / ts_name
            if not ts_p.exists():
                ts_p = self.root / ts_name
            if ts_p.exists():
                with open(ts_p, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            self.timestamps[parts[0]] = float(parts[1])

    def _setup_camera(self, cam_id: str, cam_dir: Path) -> Dict[str, Any]:
        """Sets up capture, calibration, ROI, and annotations for one camera."""
        media_type = "unknown"
        media_path = None
        w, h = 1920, 1080
        fps = 30.0
        frame_count = 0

        # Video file check
        for v_name in ["vdo.mp4", "vdo.avi", f"{cam_id}.mp4", f"{cam_id}.avi"]:
            v_p = cam_dir / v_name
            if v_p.exists():
                media_type = "video"
                media_path = str(v_p)
                cap = cv2.VideoCapture(str(v_p))
                if cap.isOpened():
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    self.caps[cam_id] = cap
                break

        # Calibration
        calibration = {}
        for c_name in ["calibration.txt", f"{cam_id}_calibration.txt"]:
            c_p = cam_dir / c_name
            if c_p.exists():
                calibration = self._load_calibration(c_p)
                break

        # ROI mask
        roi_mask = None
        for r_name in ["roi.jpg", "roi.png"]:
            r_p = cam_dir / r_name
            if r_p.exists():
                roi_mask = cv2.imread(str(r_p), cv2.IMREAD_GRAYSCALE)
                break

        # Annotations
        for gt_name in [cam_dir / "gt" / "gt.txt", cam_dir / "gt.txt"]:
            if gt_name.exists():
                self.annotation_parser.parse_camera_gt(cam_id, str(gt_name))
                break

        return {
            "camera_id": cam_id,
            "dir": str(cam_dir),
            "media_type": media_type,
            "media_path": media_path,
            "width": w,
            "height": h,
            "fps": fps,
            "frame_count": frame_count,
            "calibration": calibration,
            "roi_mask": roi_mask
        }

    def _load_calibration(self, calib_path: Path) -> Dict[str, Any]:
        """Parses camera calibration parameters into matrices."""
        matrices = []
        curr = []
        with open(calib_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                try:
                    vals = [float(p) for p in parts]
                    if len(vals) in [3, 4]:
                        curr.append(vals)
                        if len(curr) == 3:
                            matrices.append(np.array(curr, dtype=np.float32))
                            curr = []
                except ValueError:
                    continue

        calib = {}
        if len(matrices) >= 1:
            calib["K"] = matrices[0]  # Intrinsic
        if len(matrices) >= 2:
            calib["extrinsic"] = matrices[1]
        if len(matrices) >= 3:
            calib["H"] = matrices[2]  # Homography ground plane
        return calib

    def get_camera_ids(self) -> List[str]:
        """Returns sorted list of available camera identifiers."""
        return sorted(list(self.cameras.keys()))

    def get_video_info(self, camera_id: str) -> Dict[str, Any]:
        """Returns resolution, fps, and frame count for a camera."""
        c = self.cameras.get(camera_id)
        if not c:
            raise KeyError(f"Camera ID {camera_id} not found.")
        return {
            "width": c["width"],
            "height": c["height"],
            "fps": c["fps"],
            "frame_count": c["frame_count"]
        }

    def get_frame(self, camera_id: str, frame_id: int) -> Optional[np.ndarray]:
        """
        Reads frame from camera at 1-based frame_id.
        """
        if camera_id not in self.caps:
            return None

        cap = self.caps[camera_id]
        # Frame indices in OpenCV are 0-based
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, frame_id - 1))
        ret, frame = cap.read()
        if ret:
            return frame
        return None

    def get_synchronized_frames(self, frame_id: int) -> Dict[str, Optional[np.ndarray]]:
        """
        Retrieves synchronized frames for all cameras at 1-based frame_id.
        """
        result = {}
        for cam_id in self.get_camera_ids():
            result[cam_id] = self.get_frame(cam_id, frame_id)
        return result

    def get_target_initialization(self, target_id: int, camera_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the earliest ground-truth bounding box and frame for a target in a camera.
        Used for Benchmark Mode initialization.
        """
        recs = [r for r in self.annotation_parser.vehicle_camera_index.get((target_id, camera_id), [])]
        if not recs:
            return None
        earliest = min(recs, key=lambda r: r["frame_id"])
        return {
            "camera_id": camera_id,
            "frame_id": earliest["frame_id"],
            "vehicle_id": target_id,
            "bbox": earliest["bbox"]
        }

    def release(self):
        """Releases all open video capture streams."""
        for cap in self.caps.values():
            if cap.isOpened():
                cap.release()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
