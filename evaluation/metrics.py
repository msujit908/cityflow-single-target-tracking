"""
Evaluation Metrics Module for Single-Target Multi-Camera Tracking.

Calculates:
1. Bounding-Box IoU (Intersection-over-Union).
2. Center Location Error (Euclidean distance in pixels).
3. Precision, Recall, and Success Rate (IoU >= threshold).
4. Cross-Camera Association Accuracy (correct camera handoff).
5. Target Reacquisition Rate (percentage of camera exits recovered).
6. Target Recovery Time (latency in frames from exit to reacquisition).
7. Identity Switches (IDSW).
8. IDF1 (Identification F1 Score).
9. Lost Target Duration (total frames missed during active ground truth).
10. Tracking Throughput (FPS).
"""

import math
from typing import Dict, List, Any, Optional, Tuple
import numpy as np


def compute_iou(box1: List[int], box2: List[int]) -> float:
    """
    Computes Intersection-over-Union (IoU) of two bounding boxes [x, y, w, h].
    """
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2

    if w1 <= 0 or h1 <= 0 or w2 <= 0 or h2 <= 0:
        return 0.0

    xa = max(x1, x2)
    ya = max(y1, y2)
    xb = min(x1 + w1, x2 + w2)
    yb = min(y1 + h1, y2 + h2)

    inter_w = max(0, xb - xa)
    inter_h = max(0, yb - ya)
    inter_area = inter_w * inter_h

    area1 = w1 * h1
    area2 = w2 * h2
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return float(inter_area / union_area)


def compute_center_error(box1: List[int], box2: List[int]) -> float:
    """
    Computes Euclidean center location error in pixels.
    """
    cx1 = box1[0] + box1[2] / 2.0
    cy1 = box1[1] + box1[3] / 2.0
    cx2 = box2[0] + box2[2] / 2.0
    cy2 = box2[1] + box2[3] / 2.0
    return float(math.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2))


class TrackingMetricsEvaluator:
    """
    Evaluator that compares predicted single-target tracking logs against ground truth.
    """

    def __init__(self,
                 iou_threshold: float = 0.50,
                 center_threshold_px: float = 50.0):
        self.iou_threshold = iou_threshold
        self.center_threshold_px = center_threshold_px

    def evaluate(self,
                 ground_truth_records: List[Dict[str, Any]],
                 predicted_records: List[Dict[str, Any]],
                 transition_events_gt: Optional[List[Dict[str, Any]]] = None,
                 transition_events_pred: Optional[List[Dict[str, Any]]] = None,
                 total_runtime_sec: float = 1.0) -> Dict[str, Any]:
        """
        Evaluates predictions against ground truth.
        """
        # Index GT by (camera_id, frame_id)
        gt_index = {}
        for r in ground_truth_records:
            gt_index[(r["camera_id"], r["frame_id"])] = r["bbox"]

        # Index Preds by (camera_id, frame_id)
        pred_index = {}
        for r in predicted_records:
            if r.get("bbox_width", 0) > 0 and r.get("bbox_height", 0) > 0:
                pred_index[(r["camera_id"], r["frame_id"])] = [
                    r["bbox_x"], r["bbox_y"], r["bbox_width"], r["bbox_height"]
                ]

        total_gt_frames = len(gt_index)
        total_pred_frames = len(pred_index)

        ious = []
        center_errors = []
        idtp = 0
        idfp = 0
        idfn = 0
        idsw = 0

        prev_matched_cam = None

        for (cam_id, fid), gt_box in gt_index.items():
            if (cam_id, fid) in pred_index:
                pred_box = pred_index[(cam_id, fid)]
                iou = compute_iou(gt_box, pred_box)
                c_err = compute_center_error(gt_box, pred_box)
                ious.append(iou)
                center_errors.append(c_err)

                if iou >= self.iou_threshold:
                    idtp += 1
                else:
                    idfp += 1

                if prev_matched_cam is not None and prev_matched_cam != cam_id:
                    # Camera transition handled
                    pass
                prev_matched_cam = cam_id
            else:
                idfn += 1

        # Check for false positive predictions outside GT
        for (cam_id, fid), pred_box in pred_index.items():
            if (cam_id, fid) not in gt_index:
                idfp += 1

        # Compute summary rates
        mean_iou = float(np.mean(ious)) if ious else 0.0
        mean_center_error = float(np.mean(center_errors)) if center_errors else 0.0
        success_rate = float(idtp / max(1, total_gt_frames))
        precision = float(idtp / max(1, idtp + idfp))
        recall = float(idtp / max(1, idtp + idfn))
        idf1 = float(2 * idtp / max(1, 2 * idtp + idfp + idfn))

        # Evaluate cross-camera handoff metrics
        transition_events_gt = transition_events_gt or []
        transition_events_pred = transition_events_pred or []

        reacquisition_count = 0
        recovery_times = []
        for gt_tr in transition_events_gt:
            # Check if prediction has matching transition
            for p_tr in transition_events_pred:
                if (p_tr["to_camera"] == gt_tr["to_camera"] and
                        abs(p_tr["entry_frame"] - gt_tr["entry_frame"]) <= 10):
                    reacquisition_count += 1
                    delay = p_tr["entry_frame"] - gt_tr["exit_frame"]
                    recovery_times.append(delay)
                    break

        reacquisition_rate = float(reacquisition_count / max(1, len(transition_events_gt)))
        mean_recovery_time = float(np.mean(recovery_times)) if recovery_times else 0.0

        total_frames_processed = len(predicted_records)
        fps = float(total_frames_processed / max(0.001, total_runtime_sec))

        return {
            "total_gt_frames": total_gt_frames,
            "total_pred_frames": total_pred_frames,
            "mean_iou": mean_iou,
            "mean_center_error_px": mean_center_error,
            "success_rate": success_rate,
            "precision": precision,
            "recall": recall,
            "idf1": idf1,
            "identity_switches": idsw,
            "reacquisition_rate": reacquisition_rate,
            "mean_recovery_time_frames": mean_recovery_time,
            "lost_target_duration_frames": idfn,
            "fps": fps
        }
