"""
Main Application Entry Point for Single-Target Multi-Camera Vehicle Tracking.

Supports:
1. Benchmark Mode: Automated evaluation from ground-truth vehicle ID.
2. Interactive Mode: User selects a camera, previews real traffic footage, draws
   a bounding box around a vehicle using OpenCV GUI, assigns a target ID, and executes tracking.

Usage:
  python app/main.py --mode benchmark --target 1 --method proposed_adaptive
  python app/main.py --mode interactive --camera c001 --target 1
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure project root is in python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import yaml

from data.cityflow_loader import CityFlowLoader
from evaluation.benchmark import BenchmarkRunner
from evaluation.visualization import Visualizer


def run_interactive_selection(camera_id: str = "c001",
                              config_path: str = "config/config.yaml") -> list:
    """
    Opens OpenCV interactive ROI selection window on real camera video frame.
    """
    print(f"\n[*] Launching Interactive Vehicle Selection on Camera: {camera_id}")
    with CityFlowLoader(config_path=config_path) as loader:
        frame = loader.get_frame(camera_id, 1)
        if frame is None:
            raise RuntimeError(f"Could not load frame 1 from {camera_id}")

        # Render instructional banner
        disp = frame.copy()
        cv2.rectangle(disp, (30, 30), (800, 100), (0, 0, 0), -1)
        cv2.putText(disp, "SELECT VEHICLE TARGET: Drag box & press SPACE/ENTER", (45, 75),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 255), 2)

        window_name = f"CityFlow Target Selection - Camera {camera_id}"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1280, 720)

        # cv2.selectROI returns (x, y, w, h)
        bbox = cv2.selectROI(window_name, disp, fromCenter=False, showCrosshair=True)
        cv2.destroyWindow(window_name)

        if bbox[2] == 0 or bbox[3] == 0:
            print("[!] No bounding box selected. Using default fallback.")
            bbox = [605, 448, 459, 258]
        else:
            bbox = list(bbox)

        print(f"[+] Selected Target Bounding Box: {bbox}")
        return bbox


def main():
    parser = argparse.ArgumentParser(
        description="Single-Target Multi-Camera Vehicle Tracking Using CityFlow"
    )
    parser.add_argument("--mode", type=str, choices=["benchmark", "interactive"], default="benchmark",
                        help="Operating mode: 'benchmark' or 'interactive'")
    parser.add_argument("--method", type=str, default="proposed_adaptive",
                        choices=["baseline1_local_only", "baseline2_appearance_only", "baseline3_static_fusion", "proposed_adaptive"],
                        help="Tracking method / baseline to execute")
    parser.add_argument("--target", type=int, default=1, help="Global target vehicle ID")
    parser.add_argument("--camera", type=str, default="c001", help="Initial camera identifier")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Configuration YAML path")
    parser.add_argument("--render-videos", action="store_true", default=True, help="Render annotated videos and dashboard")

    args = parser.parse_args()

    print(f"\n{'='*75}")
    print(" Single-Target Multi-Camera Vehicle Tracking Across Static Traffic Cameras")
    print(f"{'='*75}")
    print(f" Mode:            {args.mode.upper()}")
    print(f" Method:          {args.method}")
    print(f" Target ID:       VEHICLE_{args.target:03d}")
    print(f" Initial Camera:  {args.camera}")
    print(f" Config File:     {args.config}")
    print(f"{'='*75}\n")

    if args.mode == "interactive":
        # Launch OpenCV interactive selection GUI
        selected_bbox = run_interactive_selection(camera_id=args.camera, config_path=args.config)
        # Update config with manual selection
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        cfg["target"]["manual_bbox"] = selected_bbox
        cfg["target"]["selection_mode"] = "interactive"
        with open(args.config, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f)

    # Execute benchmark runner
    runner = BenchmarkRunner(config_path=args.config)
    res = runner.run_method(method_name=args.method, target_id=args.target, initial_camera=args.camera)

    metrics = res["metrics"]
    print("\n" + "=" * 60)
    print(f" EXPERIMENT RESULTS: {args.method.upper()}")
    print("=" * 60)
    print(f" - Mean Bounding-Box IoU:       {metrics['mean_iou']:.4f}")
    print(f" - Center Location Error (px):   {metrics['mean_center_error_px']:.2f}")
    print(f" - Success Rate (IoU >= 0.50):   {metrics['success_rate'] * 100:.2f}%")
    print(f" - Target Reacquisition Rate:    {metrics['reacquisition_rate'] * 100:.2f}%")
    print(f" - Mean Recovery Time:          {metrics['mean_recovery_time_frames']:.1f} frames")
    print(f" - Identification F1 (IDF1):     {metrics['idf1']:.4f}")
    print(f" - Identity Switches:           {metrics['identity_switches']}")
    print(f" - Processing Throughput:        {metrics['fps']:.1f} FPS")
    print("=" * 60)

    if args.render_videos:
        print("\n[*] Generating annotated camera videos, dashboard, and trajectory plots...")
        vis = Visualizer(config_path=args.config)
        vis.render_annotated_camera_video(args.method, "c001")
        vis.render_annotated_camera_video(args.method, "c002")
        vis.render_multi_camera_dashboard(args.method)
        vis.plot_target_trajectories(args.method)
        print("\n[+] All outputs successfully generated under outputs/")


if __name__ == "__main__":
    main()
