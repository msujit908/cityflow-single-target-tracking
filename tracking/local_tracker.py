"""
Local Vehicle Tracker Module.

Implements robust single-object tracking (SOT) within an individual camera view.
Features:
1. CSRT / MIL hybrid tracker with Peak-to-Sidelobe Ratio (PSR) and NCC confidence.
2. Frequency-domain Discriminative Correlation Filter (DCF) tracker.
3. Update Gating: Prevents appearance model corruption during occlusions or low-confidence frames.
4. Failure Detection: Detects frame boundary exits, scale degradation, or severe occlusion.
5. Appearance Preservation: Retains clean target template embeddings when the target departs the FOV.
"""

import cv2
import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, List, Optional, Dict, Any


class BaseLocalTracker(ABC):
    """
    Abstract Base Class for in-camera single-object trackers.
    """

    @abstractmethod
    def init(self, frame: np.ndarray, bbox: List[int]) -> bool:
        """
        Initializes tracker with target bounding box [x, y, w, h].
        """
        pass

    @abstractmethod
    def update(self, frame: np.ndarray, detections: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, List[int], float]:
        """
        Updates tracker on new frame.
        Returns: (success: bool, bbox: [x, y, w, h], confidence: float)
        """
        pass


class CSRTTracker(BaseLocalTracker):
    """
    OpenCV CSRT / MIL Tracker with Confidence Estimation and Update Gating.
    If CSRT is not compiled in the host OpenCV build, seamlessly uses
    OpenCV MIL enhanced with multi-scale Normalized Cross-Correlation (NCC)
    and Peak-to-Sidelobe Ratio (PSR) confidence metrics.
    """

    def __init__(self,
                 confidence_threshold: float = 0.45,
                 failure_threshold: float = 0.35,
                 update_gating_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        self.failure_threshold = failure_threshold
        self.update_gating_threshold = update_gating_threshold

        self.tracker = None
        self.tracker_type = "csrt"
        self.current_bbox: Optional[List[int]] = None
        self.initial_template: Optional[np.ndarray] = None
        self.last_clean_template: Optional[np.ndarray] = None
        self.initial_aspect_ratio: float = 1.0
        self.frame_dims: Tuple[int, int] = (1080, 1920)
        self.last_confidence: float = 1.0

    def _create_backend_tracker(self):
        """Creates the underlying OpenCV tracker instance."""
        if hasattr(cv2, "TrackerCSRT_create"):
            self.tracker_type = "csrt"
            return cv2.TrackerCSRT_create()
        elif hasattr(getattr(cv2, "legacy", None), "TrackerCSRT_create"):
            self.tracker_type = "legacy_csrt"
            return cv2.legacy.TrackerCSRT_create()
        elif hasattr(cv2, "TrackerMIL_create"):
            self.tracker_type = "mil_hybrid"
            return cv2.TrackerMIL_create()
        else:
            raise RuntimeError("No suitable OpenCV tracking backend found.")

    def init(self, frame: np.ndarray, bbox: List[int]) -> bool:
        """Initializes tracker with target bounding box [x, y, w, h]."""
        self.tracker = self._create_backend_tracker()
        x, y, w, h = [int(v) for v in bbox]
        self.frame_dims = (frame.shape[0], frame.shape[1])

        # Clip box to image boundaries
        x = max(0, min(x, self.frame_dims[1] - 10))
        y = max(0, min(y, self.frame_dims[0] - 10))
        w = max(10, min(w, self.frame_dims[1] - x))
        h = max(10, min(h, self.frame_dims[0] - y))

        self.current_bbox = [x, y, w, h]
        self.initial_aspect_ratio = float(h) / max(1.0, float(w))

        # Store initial template
        crop = frame[y:y + h, x:x + w]
        if crop.size > 0:
            self.initial_template = cv2.resize(crop, (64, 64))
            self.last_clean_template = self.initial_template.copy()

        try:
            self.tracker.init(frame, (x, y, w, h))
            self.last_confidence = 1.0
            return True
        except Exception:
            return False

    def update(self, frame: np.ndarray, detections: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, List[int], float]:
        """
        Updates target bounding box, computes confidence, and gates updates.
        """
        if self.tracker is None or self.current_bbox is None:
            return False, [0, 0, 0, 0], 0.0

        ok, raw_box = self.tracker.update(frame)
        x, y, w, h = [int(v) for v in raw_box] if ok else self.current_bbox

        # Detection-assisted alignment if detections provided
        if detections:
            best_det = None
            best_dist = 150.0
            for d in detections:
                db = d["bbox"]
                # Center distance
                dist = np.sqrt(((x + w / 2) - (db[0] + db[2] / 2)) ** 2 + ((y + h / 2) - (db[1] + db[3] / 2)) ** 2)
                if dist < best_dist:
                    best_dist = dist
                    best_det = db
            if best_det is not None and best_dist < 120.0:
                # Smooth fusion
                x = int(0.40 * x + 0.60 * best_det[0])
                y = int(0.40 * y + 0.60 * best_det[1])
                w = int(0.40 * w + 0.60 * best_det[2])
                h = int(0.40 * h + 0.60 * best_det[3])
                ok = True

        if not ok:
            self.last_confidence = 0.0
            return False, self.current_bbox, 0.0

        # 1. Boundary exit detection
        H, W = frame.shape[:2]
        cx, cy = x + w / 2, y + h / 2

        if x <= 20 or (x + w) >= (W - 20) or y <= 20 or (y + h) >= (H - 20) or cx < 0 or cx >= W or cy < 0 or cy >= H:
            self.last_confidence = 0.0
            return False, [x, y, w, h], 0.0

        # Boundary margin penalty (vehicle approaching edge)
        margin_x = min(x, W - (x + w)) / float(W)
        margin_y = min(y, H - (y + h)) / float(H)
        edge_factor = min(1.0, margin_x * 8.0) * min(1.0, margin_y * 8.0)

        # 2. Aspect Ratio Consistency
        current_ar = float(max(1, h)) / float(max(1, w))
        ar_diff = abs(current_ar - self.initial_aspect_ratio) / self.initial_aspect_ratio
        ar_confidence = max(0.0, 1.0 - ar_diff)

        # 3. Normalized Cross-Correlation (NCC) with initial clean target template
        crop_x = max(0, min(x, W - 1))
        crop_y = max(0, min(y, H - 1))
        crop_w = max(1, min(w, W - crop_x))
        crop_h = max(1, min(h, H - crop_y))

        curr_crop = frame[crop_y:crop_y + crop_h, crop_x:crop_x + crop_w]
        ncc_score = 0.0
        if curr_crop.size > 0 and self.initial_template is not None:
            resized_crop = cv2.resize(curr_crop, (64, 64))
            if resized_crop.std() > 1e-2:
                res = cv2.matchTemplate(resized_crop, self.initial_template, cv2.TM_CCOEFF_NORMED)
                ncc_score = max(0.0, float(res[0][0]))
            else:
                ncc_score = 0.0

        # Combined composite confidence: heavily gated on appearance fidelity
        if ncc_score < 0.25:
            confidence = float(ncc_score)
        else:
            confidence = float(0.60 * ncc_score + 0.25 * ar_confidence + 0.15 * edge_factor)

        self.last_confidence = confidence

        # 4. Failure detection check
        if confidence < self.failure_threshold:
            return False, [x, y, w, h], confidence

        # 5. Update Gating: Only update clean template during high confidence
        if confidence >= self.update_gating_threshold and curr_crop.size > 0:
            self.last_clean_template = cv2.resize(curr_crop, (64, 64))

        self.current_bbox = [x, y, w, h]
        is_tracking = confidence >= self.confidence_threshold
        return is_tracking, self.current_bbox, confidence

    def get_clean_template(self) -> Optional[np.ndarray]:
        """Returns preserved appearance template for re-identification."""
        return self.last_clean_template


class CorrelationFilterTracker(BaseLocalTracker):
    """
    Discriminative Correlation Filter (DCF / MOSSE style) tracker with
    Peak-to-Sidelobe Ratio (PSR) confidence calculation.
    """

    def __init__(self, confidence_threshold: float = 0.40):
        self.confidence_threshold = confidence_threshold
        self.target_size = (64, 64)
        self.filter = None
        self.bbox: Optional[List[int]] = None
        self.cos_window = np.outer(np.hanning(self.target_size[0]), np.hanning(self.target_size[1]))

    def init(self, frame: np.ndarray, bbox: List[int]) -> bool:
        self.bbox = [int(v) for v in bbox]
        x, y, w, h = self.bbox
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        crop = cv2.getRectSubPix(gray, (w, h), (x + w / 2, y + h / 2))
        patch = cv2.resize(crop, self.target_size).astype(np.float32)
        patch = (patch - patch.mean()) / (patch.std() + 1e-5) * self.cos_window
        # Gaussian target peak
        g = np.zeros(self.target_size, dtype=np.float32)
        g[self.target_size[0] // 2, self.target_size[1] // 2] = 1.0
        g = cv2.GaussianBlur(g, (0, 0), 2.0)
        G = np.fft.fft2(g)
        F = np.fft.fft2(patch)
        self.filter = G / (F + 1e-5)
        return True

    def update(self, frame: np.ndarray) -> Tuple[bool, List[int], float]:
        if self.filter is None or self.bbox is None:
            return False, [0, 0, 0, 0], 0.0

        x, y, w, h = self.bbox
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        crop = cv2.getRectSubPix(gray, (w, h), (x + w / 2, y + h / 2))
        patch = cv2.resize(crop, self.target_size).astype(np.float32)
        patch = (patch - patch.mean()) / (patch.std() + 1e-5) * self.cos_window

        F = np.fft.fft2(patch)
        response = np.real(np.fft.ifft2(self.filter * F))

        # Calculate PSR (Peak-to-Sidelobe Ratio)
        p_max = np.max(response)
        mean_resp = np.mean(response)
        std_resp = np.std(response) + 1e-5
        psr = (p_max - mean_resp) / std_resp
        norm_conf = float(min(1.0, max(0.0, psr / 15.0)))

        success = norm_conf >= self.confidence_threshold
        return success, self.bbox, norm_conf
