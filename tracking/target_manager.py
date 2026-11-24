"""
Global Target Manager Module.

Maintains persistent single-target state across all cameras:
- global_target_id
- current_camera_id
- current_bbox [x, y, w, h]
- appearance_embedding
- last_observed_frame
- previous_camera
- camera_exit_frame
- tracking_confidence
- target_status: ACTIVE, LOST, SEARCHING, REACQUIRED

Ensures identity persistence and provides structured tracking log generation.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


class TargetStatus(str, Enum):
    ACTIVE = "ACTIVE"
    LOST = "LOST"
    SEARCHING = "SEARCHING"
    REACQUIRED = "REACQUIRED"


class GlobalTargetManager:
    """
    Persistent state manager for the single selected vehicle target.
    """

    def __init__(self,
                 global_target_id: int = 1,
                 initial_camera: str = "c001",
                 initial_bbox: Optional[List[int]] = None,
                 initial_frame: int = 1):
        self.global_target_id = global_target_id
        self.current_camera_id: str = initial_camera
        self.previous_camera_id: Optional[str] = None

        self.current_bbox: Optional[List[int]] = initial_bbox or [0, 0, 0, 0]
        self.last_known_bbox: Optional[List[int]] = initial_bbox or [0, 0, 0, 0]

        self.last_observed_frame: int = initial_frame
        self.camera_exit_frame: Optional[int] = None
        self.tracking_confidence: float = 1.0
        self.status: TargetStatus = TargetStatus.ACTIVE

        # Appearance representation
        self.appearance_embedding: Optional[np.ndarray] = None

        # History tracking logs
        # Each entry: {frame_id, camera_id, global_target_id, bbox, confidence, status}
        self.tracking_history: List[Dict[str, Any]] = []

        # Cross-camera transition logs
        self.transition_history: List[Dict[str, Any]] = []

    def log_frame(self,
                  frame_id: int,
                  camera_id: str,
                  bbox: Optional[List[int]],
                  confidence: float,
                  status: TargetStatus):
        """
        Records frame-level state into tracking history.
        """
        self.current_camera_id = camera_id
        self.tracking_confidence = float(confidence)
        self.status = status

        if bbox is not None and status in [TargetStatus.ACTIVE, TargetStatus.REACQUIRED]:
            self.current_bbox = bbox
            self.last_known_bbox = bbox
            self.last_observed_frame = frame_id
        else:
            self.current_bbox = None

        b = self.current_bbox or [0, 0, 0, 0]

        entry = {
            "frame_id": frame_id,
            "camera_id": camera_id,
            "global_target_id": self.global_target_id,
            "bbox_x": b[0],
            "bbox_y": b[1],
            "bbox_width": b[2],
            "bbox_height": b[3],
            "confidence": float(confidence),
            "tracking_status": self.status.value
        }
        self.tracking_history.append(entry)

    def mark_lost(self, camera_id: str, frame_id: int):
        """Transitions target to LOST status."""
        self.status = TargetStatus.LOST
        self.camera_exit_frame = frame_id
        self.current_bbox = None
        self.tracking_confidence = 0.0

    def mark_searching(self, frame_id: int):
        """Transitions target to SEARCHING across candidate cameras."""
        self.status = TargetStatus.SEARCHING
        self.current_bbox = None

    def mark_reacquired(self,
                        new_camera_id: str,
                        frame_id: int,
                        bbox: List[int],
                        confidence: float,
                        association_score: float):
        """
        Records successful reacquisition in a new camera.
        """
        self.previous_camera_id = self.current_camera_id
        self.current_camera_id = new_camera_id
        self.current_bbox = bbox
        self.last_known_bbox = bbox
        self.last_observed_frame = frame_id
        self.tracking_confidence = float(confidence)
        self.status = TargetStatus.REACQUIRED

        # Record transition event
        exit_f = self.camera_exit_frame or (frame_id - 1)
        transition_entry = {
            "global_target_id": self.global_target_id,
            "from_camera": self.previous_camera_id,
            "exit_frame": exit_f,
            "to_camera": new_camera_id,
            "entry_frame": frame_id,
            "delay_frames": frame_id - exit_f,
            "association_score": float(association_score)
        }
        self.transition_history.append(transition_entry)

    def get_state(self) -> Dict[str, Any]:
        """Returns current state snapshot."""
        return {
            "global_target_id": self.global_target_id,
            "camera_id": self.current_camera_id,
            "status": self.status.value,
            "bbox": self.current_bbox,
            "last_known_bbox": self.last_known_bbox,
            "confidence": self.tracking_confidence,
            "last_observed_frame": self.last_observed_frame,
            "previous_camera": self.previous_camera_id
        }
