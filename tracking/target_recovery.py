"""
Target Recovery and Cross-Camera Handoff Module.

Implements the target recovery state machine and candidate matching pipeline:
1. Candidate Camera Selection: Discovers topologically plausible destination cameras.
2. Candidate Vehicle Proposal: Detects vehicles in candidate views using VehicleDetector.
3. Feature Extraction: Extracts embeddings via VehicleReIDExtractor.
4. Scoring & Filtering: Applies CrossCameraAssociation (Baseline 2, Baseline 3, or Proposed Method).
5. Target Reacquisition: Selects best match exceeding threshold and re-initializes local tracker.
"""

from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from tracking.target_manager import GlobalTargetManager, TargetStatus
from tracking.local_tracker import BaseLocalTracker
from tracking.vehicle_detector import VehicleDetector
from tracking.vehicle_reid import VehicleReIDExtractor
from tracking.camera_association import CrossCameraAssociation


class TargetRecoveryController:
    """
    Orchestrates target recovery across cameras during target disappearance.
    """

    def __init__(self,
                 target_manager: GlobalTargetManager,
                 reid_extractor: VehicleReIDExtractor,
                 detector: VehicleDetector,
                 association_engine: CrossCameraAssociation,
                 reacquisition_threshold: float = 0.55,
                 max_search_patience: int = 90,
                 use_proposed_adaptive: bool = True):
        self.target_manager = target_manager
        self.reid_extractor = reid_extractor
        self.detector = detector
        self.association_engine = association_engine
        self.reacquisition_threshold = reacquisition_threshold
        self.max_search_patience = max_search_patience
        self.use_proposed_adaptive = use_proposed_adaptive

    def search_and_recover(self,
                           frame_id: int,
                           candidate_frames: Dict[str, np.ndarray],
                           roi_masks: Optional[Dict[str, np.ndarray]] = None) -> Optional[Dict[str, Any]]:
        """
        Searches candidate cameras for the lost target.
        Returns recovery metadata if match found, else None.
        """
        roi_masks = roi_masks or {}
        from_cam = self.target_manager.previous_camera_id or self.target_manager.current_camera_id
        exit_frame = self.target_manager.camera_exit_frame or (frame_id - 1)
        travel_delay = frame_id - exit_frame

        if travel_delay > self.max_search_patience:
            self.target_manager.status = TargetStatus.LOST
            return None

        self.target_manager.mark_searching(frame_id)

        last_known_bbox = self.target_manager.last_known_bbox or [0, 0, 0, 0]
        best_candidate = None
        best_score = -1.0
        best_score_breakdown = {}

        # Scan candidate destination cameras (different from source exit camera)
        for cam_id, frame in candidate_frames.items():
            if frame is None:
                continue

            # Inter-camera handoff constraint: Target has departed from_cam
            if cam_id == from_cam:
                continue

            roi = roi_masks.get(cam_id)
            candidates = self.detector.detect(frame, roi_mask=roi)

            for cand in candidates:
                bbox = cand["bbox"]
                det_conf = cand["confidence"]

                # Extract candidate embedding
                cand_emb = self.reid_extractor.extract_embedding(frame, bbox)
                if cand_emb is None:
                    continue

                # Appearance similarity
                s_app = self.reid_extractor.compute_similarity(cand_emb)

                # Compute association score
                if self.use_proposed_adaptive:
                    score_dict = self.association_engine.compute_adaptive_reliability_score(
                        appearance_sim=s_app,
                        from_camera=from_cam,
                        to_camera=cam_id,
                        travel_delay=travel_delay,
                        last_bbox=last_known_bbox,
                        candidate_bbox=bbox,
                        detection_confidence=det_conf
                    )
                else:
                    score_dict = self.association_engine.compute_static_fusion_score(
                        appearance_sim=s_app,
                        from_camera=from_cam,
                        to_camera=cam_id,
                        travel_delay=travel_delay,
                        last_bbox=last_known_bbox,
                        candidate_bbox=bbox
                    )

                score = score_dict["total_score"]

                if score > best_score:
                    best_score = score
                    best_score_breakdown = score_dict
                    best_candidate = {
                        "camera_id": cam_id,
                        "frame_id": frame_id,
                        "bbox": bbox,
                        "score": score,
                        "confidence": det_conf,
                        "score_breakdown": score_dict,
                        "embedding": cand_emb
                    }

        # Check if best candidate clears reacquisition threshold
        if best_candidate and best_candidate["score"] >= self.reacquisition_threshold:
            # Reacquire target!
            self.target_manager.mark_reacquired(
                new_camera_id=best_candidate["camera_id"],
                frame_id=frame_id,
                bbox=best_candidate["bbox"],
                confidence=best_candidate["confidence"],
                association_score=best_candidate["score"]
            )
            # Update target gallery with reacquired view
            self.reid_extractor.update_target_gallery(
                best_candidate["embedding"],
                confidence=best_candidate["confidence"]
            )
            return best_candidate

        return None
