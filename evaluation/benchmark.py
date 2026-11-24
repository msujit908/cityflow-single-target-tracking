"""
Benchmarking and Baseline Comparison Module.

Executes controlled, reproducible single-target multi-camera tracking experiments:
1. Baseline 1: Local tracking within one camera only (no cross-camera handoff).
2. Baseline 2: Cross-camera matching using appearance similarity only.
3. Baseline 3: Appearance similarity plus camera transition constraints (static weights).
4. Proposed Method: Reliability-aware cross-camera association with adaptive confidence and target recovery.

Saves:
- outputs/tracking_results/tracking_<method>.csv
- outputs/tracking_results/transitions_<method>.csv
- outputs/reports/benchmark_metrics.csv
"""

import os
import sys
import time
from pathlib import Path

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from typing import Dict, List, Any, Optional

from data.cityflow_loader import CityFlowLoader
from tracking.local_tracker import CSRTTracker
from tracking.vehicle_detector import VehicleDetector
from tracking.vehicle_reid import VehicleReIDExtractor
from tracking.camera_association import CrossCameraAssociation
from tracking.target_manager import GlobalTargetManager, TargetStatus
from tracking.target_recovery import TargetRecoveryController
from evaluation.metrics import TrackingMetricsEvaluator


class BenchmarkRunner:
    """
    Executes and evaluates multi-camera tracking baselines.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.evaluator = TrackingMetricsEvaluator()

    def run_method(self,
                   method_name: str,
                   target_id: int = 1,
                   initial_camera: str = "c001") -> Dict[str, Any]:
        """
        Runs tracking experiment under a specific method configuration.
        """
        print(f"\n{'='*70}\n[>] Running Experiment: {method_name.upper()} (Target ID {target_id})\n{'='*70}")

        start_time = time.time()

        with CityFlowLoader(config_path=self.config_path) as loader:
            cam_ids = loader.get_camera_ids()
            init_data = loader.get_target_initialization(target_id=target_id, camera_id=initial_camera)
            if not init_data:
                raise ValueError(f"Target {target_id} not found in camera {initial_camera}")

            init_frame = init_data["frame_id"]
            init_bbox = init_data["bbox"]

            # Initialize components
            target_manager = GlobalTargetManager(
                global_target_id=target_id,
                initial_camera=initial_camera,
                initial_bbox=init_bbox,
                initial_frame=init_frame
            )

            local_tracker = CSRTTracker()
            detector = VehicleDetector(backend="ssdlite")
            reid_extractor = VehicleReIDExtractor(backbone="resnet50")

            # Configure association weights per method
            if method_name == "baseline1_local_only":
                weights = {"appearance": 1.0, "temporal": 0.0, "topology": 0.0, "motion": 0.0}
                use_adaptive = False
            elif method_name == "baseline2_appearance_only":
                weights = {"appearance": 1.0, "temporal": 0.0, "topology": 0.0, "motion": 0.0}
                use_adaptive = False
            elif method_name == "baseline3_static_fusion":
                weights = {"appearance": 0.40, "temporal": 0.25, "topology": 0.20, "motion": 0.15}
                use_adaptive = False
            elif method_name == "proposed_adaptive":
                weights = {"appearance": 0.40, "temporal": 0.25, "topology": 0.20, "motion": 0.15}
                use_adaptive = True
            else:
                raise ValueError(f"Unknown method name: {method_name}")

            association_engine = CrossCameraAssociation(weights=weights)

            recovery_controller = TargetRecoveryController(
                target_manager=target_manager,
                reid_extractor=reid_extractor,
                detector=detector,
                association_engine=association_engine,
                use_proposed_adaptive=use_adaptive
            )

            # Initialize tracker with initial frame
            first_frame_img = loader.get_frame(initial_camera, init_frame)
            local_tracker.init(first_frame_img, init_bbox)

            # Seed target appearance gallery
            first_emb = reid_extractor.extract_embedding(first_frame_img, init_bbox)
            if first_emb is not None:
                reid_extractor.update_target_gallery(first_emb, confidence=1.0)

            # Determine maximum frame count across cameras
            max_frames = max(loader.get_video_info(c)["frame_count"] for c in cam_ids)

            # Frame-by-frame simulation
            for fid in range(init_frame, max_frames + 1):
                curr_cam = target_manager.current_camera_id
                curr_status = target_manager.status

                if curr_status == TargetStatus.ACTIVE:
                    frame_img = loader.get_frame(curr_cam, fid)
                    if frame_img is None:
                        target_manager.mark_lost(curr_cam, fid)
                        target_manager.log_frame(fid, curr_cam, None, 0.0, TargetStatus.LOST)
                        continue

                    # Local detection to guide and assist single-object tracking
                    roi = loader.cameras[curr_cam]["roi_mask"]
                    dets = detector.detect(frame_img, roi_mask=roi)

                    ok, box, conf = local_tracker.update(frame_img, detections=dets)
                    if ok:
                        target_manager.log_frame(fid, curr_cam, box, conf, TargetStatus.ACTIVE)
                        # Periodically refresh appearance gallery
                        if fid % 5 == 0 and conf > 0.60:
                            emb = reid_extractor.extract_embedding(frame_img, box)
                            if emb is not None:
                                reid_extractor.update_target_gallery(emb, conf)
                    else:
                        # Target lost in current camera
                        target_manager.mark_lost(curr_cam, fid)
                        target_manager.log_frame(fid, curr_cam, None, 0.0, TargetStatus.LOST)

                elif curr_status in [TargetStatus.LOST, TargetStatus.SEARCHING]:
                    if method_name == "baseline1_local_only":
                        # Local-only baseline never recovers across cameras
                        target_manager.log_frame(fid, curr_cam, None, 0.0, TargetStatus.LOST)
                        continue

                    # Retrieve frames from candidate cameras
                    cand_frames = {}
                    for cid in cam_ids:
                        cand_frames[cid] = loader.get_frame(cid, fid)

                    roi_masks = {cid: loader.cameras[cid]["roi_mask"] for cid in cam_ids}

                    # Attempt target recovery
                    match = recovery_controller.search_and_recover(fid, cand_frames, roi_masks)
                    if match:
                        new_cam = match["camera_id"]
                        new_bbox = match["bbox"]
                        new_conf = match["confidence"]

                        # Reinitialize fresh local tracker in new camera
                        new_frame_img = cand_frames[new_cam]
                        local_tracker = CSRTTracker()
                        local_tracker.init(new_frame_img, new_bbox)

                        target_manager.log_frame(fid, new_cam, new_bbox, new_conf, TargetStatus.REACQUIRED)
                        # Switch back to ACTIVE for subsequent frames
                        target_manager.status = TargetStatus.ACTIVE
                    else:
                        target_manager.log_frame(fid, curr_cam, None, 0.0, target_manager.status)

            total_runtime = time.time() - start_time

            # Collect Ground Truth records for evaluation
            gt_records = [
                r for r in loader.annotation_parser.annotations if r["vehicle_id"] == target_id
            ]

            # Collect GT transitions
            gt_transitions = []
            v_timeline = loader.annotation_parser.get_vehicle_timeline(target_id)
            for i in range(len(v_timeline) - 1):
                gt_transitions.append({
                    "from_camera": v_timeline[i]["camera_id"],
                    "exit_frame": v_timeline[i]["last_frame"],
                    "to_camera": v_timeline[i + 1]["camera_id"],
                    "entry_frame": v_timeline[i + 1]["first_frame"]
                })

            # Evaluate performance
            metrics = self.evaluator.evaluate(
                ground_truth_records=gt_records,
                predicted_records=target_manager.tracking_history,
                transition_events_gt=gt_transitions,
                transition_events_pred=target_manager.transition_history,
                total_runtime_sec=total_runtime
            )

            metrics["method"] = method_name
            metrics["runtime_sec"] = total_runtime

            # Save tracking and transition CSVs
            os.makedirs("outputs/tracking_results", exist_ok=True)
            tracking_df = pd.DataFrame(target_manager.tracking_history)
            tracking_csv_path = f"outputs/tracking_results/tracking_{method_name}.csv"
            tracking_df.to_csv(tracking_csv_path, index=False)

            trans_df = pd.DataFrame(target_manager.transition_history)
            trans_csv_path = f"outputs/tracking_results/transitions_{method_name}.csv"
            trans_df.to_csv(trans_csv_path, index=False)

            print(f"[+] Tracking logs saved: {tracking_csv_path}")
            print(f"[+] Transitions saved: {trans_csv_path}")
            print(f"[+] Metrics Summary: Mean IoU={metrics['mean_iou']:.4f}, Success Rate={metrics['success_rate']:.4f}, IDF1={metrics['idf1']:.4f}, Reacq Rate={metrics['reacquisition_rate']:.2f}")

            return {
                "metrics": metrics,
                "tracking_history": target_manager.tracking_history,
                "transition_history": target_manager.transition_history
            }

    def run_all_benchmarks(self, target_id: int = 1) -> pd.DataFrame:
        """
        Runs all four methods and saves comparative benchmark reports.
        """
        methods = [
            "baseline1_local_only",
            "baseline2_appearance_only",
            "baseline3_static_fusion",
            "proposed_adaptive"
        ]

        results = []
        for m in methods:
            res = self.run_method(m, target_id=target_id)
            results.append(res["metrics"])

        df = pd.DataFrame(results)
        os.makedirs("outputs/reports", exist_ok=True)
        metrics_csv = "outputs/reports/benchmark_metrics.csv"
        df.to_csv(metrics_csv, index=False)
        print(f"\n[+] Full Benchmark Metrics saved to: {metrics_csv}")
        return df


if __name__ == "__main__":
    runner = BenchmarkRunner()
    runner.run_all_benchmarks(target_id=1)
