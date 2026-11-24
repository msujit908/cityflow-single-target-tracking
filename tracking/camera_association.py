"""
Cross-Camera Association Module.

Computes multi-modal cross-camera candidate matching scores combining:
1. S_app: Vehicle appearance embedding cosine similarity.
2. S_temp: Spatio-temporal travel delay consistency (Gaussian transit kernel).
3. S_trans: Camera topological transition probability prior.
4. S_motion: Directional and scale consistency across cameras.

Provides:
- Static Weight Fusion (Baseline 3)
- Proposed Dynamic Reliability-Aware Adaptive Fusion
"""

import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class CrossCameraAssociation:
    """
    Computes cross-camera association scores between a lost target vehicle
    and candidate vehicle detections in candidate destination cameras.
    """

    def __init__(self,
                 weights: Optional[Dict[str, float]] = None,
                 reacquisition_threshold: float = 0.55,
                 min_travel_delay: int = 5,
                 max_travel_delay: int = 60,
                 topology: Optional[Dict[str, Any]] = None):
        # Default static weights (Baseline 3)
        self.weights = weights or {
            "appearance": 0.40,
            "temporal": 0.25,
            "topology": 0.20,
            "motion": 0.15
        }
        self.reacquisition_threshold = reacquisition_threshold
        self.min_travel_delay = min_travel_delay
        self.max_travel_delay = max_travel_delay
        self.topology = topology or {}

        # Default transition priors if none provided
        self.default_transit_priors = {
            ("c001", "c002"): {"prob": 0.85, "mean_delay": 15.0, "std_delay": 4.0},
            ("c002", "c001"): {"prob": 0.80, "mean_delay": 16.0, "std_delay": 4.0},
            ("c003", "c004"): {"prob": 0.85, "mean_delay": 15.0, "std_delay": 4.0},
            ("c004", "c003"): {"prob": 0.80, "mean_delay": 16.0, "std_delay": 4.0}
        }

    def compute_temporal_consistency(self,
                                     from_camera: str,
                                     to_camera: str,
                                     travel_delay_frames: int) -> float:
        """
        Computes temporal consistency score S_temp using Gaussian travel-time distribution.
        S_temp = exp(- (dt - mu)^2 / (2 * sigma^2))
        """
        prior = self.default_transit_priors.get(
            (from_camera, to_camera),
            {"prob": 0.50, "mean_delay": 15.0, "std_delay": 8.0}
        )

        mu = prior["mean_delay"]
        sigma = prior["std_delay"]

        if travel_delay_frames < self.min_travel_delay:
            # Physically impossible teleportation
            return 0.05

        diff = travel_delay_frames - mu
        score = math.exp(- (diff ** 2) / (2.0 * (sigma ** 2)))
        return float(np.clip(score, 0.0, 1.0))

    def compute_topology_prior(self, from_camera: str, to_camera: str) -> float:
        """
        Returns topological transition probability S_trans.
        """
        if from_camera == to_camera:
            return 0.40  # In-camera re-emergence after occlusion

        prior = self.default_transit_priors.get((from_camera, to_camera))
        if prior:
            return float(prior["prob"])
        return 0.30

    def compute_motion_consistency(self,
                                   last_known_bbox: List[int],
                                   candidate_bbox: List[int],
                                   from_camera: str,
                                   to_camera: str) -> float:
        """
        Computes scale and velocity motion consistency S_motion.
        """
        _, _, w1, h1 = last_known_bbox
        _, _, w2, h2 = candidate_bbox

        area1 = float(max(1, w1 * h1))
        area2 = float(max(1, w2 * h2))

        # Scale ratio penalty
        scale_ratio = min(area1, area2) / max(area1, area2)

        # Aspect ratio consistency
        ar1 = float(h1) / max(1.0, float(w1))
        ar2 = float(h2) / max(1.0, float(w2))
        ar_consistency = max(0.0, 1.0 - abs(ar1 - ar2) / ar1)

        motion_score = 0.60 * scale_ratio + 0.40 * ar_consistency
        return float(np.clip(motion_score, 0.0, 1.0))

    def compute_static_fusion_score(self,
                                    appearance_sim: float,
                                    from_camera: str,
                                    to_camera: str,
                                    travel_delay: int,
                                    last_bbox: List[int],
                                    candidate_bbox: List[int]) -> Dict[str, float]:
        """
        Baseline 3: Static weighted sum:
        S = w1 * S_app + w2 * S_temp + w3 * S_trans + w4 * S_motion
        """
        s_app = float(appearance_sim)
        s_temp = self.compute_temporal_consistency(from_camera, to_camera, travel_delay)
        s_trans = self.compute_topology_prior(from_camera, to_camera)
        s_motion = self.compute_motion_consistency(last_bbox, candidate_bbox, from_camera, to_camera)

        w = self.weights
        total_w = w["appearance"] + w["temporal"] + w["topology"] + w["motion"]
        score = (
            w["appearance"] * s_app +
            w["temporal"] * s_temp +
            w["topology"] * s_trans +
            w["motion"] * s_motion
        ) / max(1e-5, total_w)

        return {
            "total_score": float(np.clip(score, 0.0, 1.0)),
            "s_app": s_app,
            "s_temp": s_temp,
            "s_trans": s_trans,
            "s_motion": s_motion
        }

    def compute_adaptive_reliability_score(self,
                                           appearance_sim: float,
                                           from_camera: str,
                                           to_camera: str,
                                           travel_delay: int,
                                           last_bbox: List[int],
                                           candidate_bbox: List[int],
                                           detection_confidence: float,
                                           gallery_diversity: float = 1.0) -> Dict[str, float]:
        """
        Proposed Method: Reliability-Aware Adaptive Cross-Camera Association.
        Dynamically adjusts evidence weights alpha_k based on:
        - Appearance quality / certainty (gallery diversity, appearance clarity).
        - Temporal decay factor over disappearance duration.
        - Candidate detection confidence.
        - Motion scale consistency.
        """
        s_app = float(appearance_sim)
        s_temp = self.compute_temporal_consistency(from_camera, to_camera, travel_delay)
        s_trans = self.compute_topology_prior(from_camera, to_camera)
        s_motion = self.compute_motion_consistency(last_bbox, candidate_bbox, from_camera, to_camera)

        # 1. Quality multipliers
        # Appearance reliability drops if appearance is ambiguous (near random similarity)
        gamma_app = max(0.2, (s_app ** 1.5)) * min(1.0, gallery_diversity)
        # Detection certainty
        gamma_det = float(detection_confidence)
        # Temporal reliability drops if target has been missing for too long
        gamma_temp = math.exp(-0.02 * max(0, travel_delay - self.max_travel_delay))
        # Topology certainty
        gamma_trans = s_trans

        # 2. Dynamic weights computation
        raw_w_app = self.weights["appearance"] * gamma_app * gamma_det
        raw_w_temp = self.weights["temporal"] * gamma_temp
        raw_w_trans = self.weights["topology"] * gamma_trans
        raw_w_motion = self.weights["motion"] * s_motion

        sum_w = raw_w_app + raw_w_temp + raw_w_trans + raw_w_motion + 1e-6
        alpha_app = raw_w_app / sum_w
        alpha_temp = raw_w_temp / sum_w
        alpha_trans = raw_w_trans / sum_w
        alpha_motion = raw_w_motion / sum_w

        adaptive_score = (
            alpha_app * s_app +
            alpha_temp * s_temp +
            alpha_trans * s_trans +
            alpha_motion * s_motion
        )

        return {
            "total_score": float(np.clip(adaptive_score, 0.0, 1.0)),
            "s_app": s_app,
            "s_temp": s_temp,
            "s_trans": s_trans,
            "s_motion": s_motion,
            "alpha_app": float(alpha_app),
            "alpha_temp": float(alpha_temp),
            "alpha_trans": float(alpha_trans),
            "alpha_motion": float(alpha_motion)
        }
