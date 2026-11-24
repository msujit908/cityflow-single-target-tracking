"""
Visualization and Output Video Generation Module.

Generates:
1. Annotated MP4 video for each camera stream.
2. Multi-camera synchronized dashboard MP4 video (side-by-side or 2x2 grid).
3. Target spatial trajectory plots across cameras.
4. Baseline comparison bar charts (IoU, IDF1, Reacquisition Rate, Latency, FPS).
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ensure project root is in path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import cv2
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from data.cityflow_loader import CityFlowLoader


class Visualizer:
    """
    Renders tracking overlays, HUD banners, multi-camera dashboard videos, and comparative plots.
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.colors = {
            "ACTIVE": (0, 255, 0),         # Vibrant Green
            "REACQUIRED": (0, 255, 255),    # Yellow
            "SEARCHING": (0, 165, 255),     # Orange
            "LOST": (0, 0, 255),           # Red
            "GT": (255, 0, 255)            # Magenta for GT reference
        }

    def render_annotated_camera_video(self,
                                     method_name: str,
                                     camera_id: str,
                                     output_path: Optional[str] = None) -> str:
        """
        Renders annotated video for an individual camera stream.
        """
        output_path = output_path or f"outputs/videos/tracking_{method_name}_{camera_id}.mp4"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        tracking_csv = f"outputs/tracking_results/tracking_{method_name}.csv"
        if not os.path.exists(tracking_csv):
            raise FileNotFoundError(f"Tracking CSV not found: {tracking_csv}")

        df = pd.read_csv(tracking_csv)
        # Filter for this camera or overall
        pred_index = {}
        for _, row in df.iterrows():
            pred_index[(row["camera_id"], int(row["frame_id"]))] = row

        with CityFlowLoader(config_path=self.config_path) as loader:
            info = loader.get_video_info(camera_id)
            W, H = info["width"], info["height"]
            fps = info["fps"]
            total_frames = info["frame_count"]

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (W, H))

            for fid in range(1, total_frames + 1):
                frame = loader.get_frame(camera_id, fid)
                if frame is None:
                    continue

                annotated = frame.copy()

                # Check if target prediction exists for this camera & frame
                pred = pred_index.get((camera_id, fid))
                if pred is not None and pred["tracking_status"] in ["ACTIVE", "REACQUIRED"]:
                    bx = int(pred["bbox_x"])
                    by = int(pred["bbox_y"])
                    bw = int(pred["bbox_width"])
                    bh = int(pred["bbox_height"])
                    status = pred["tracking_status"]
                    conf = float(pred["confidence"])

                    if bw > 0 and bh > 0:
                        col = self.colors.get(status, (0, 255, 0))
                        # Bounding box
                        cv2.rectangle(annotated, (bx, by), (bx + bw, by + bh), col, 4)

                        # Target pill label above bbox
                        label = f"TARGET_001 [{conf:.2f}]"
                        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                        cv2.rectangle(annotated, (bx, max(0, by - 30)), (bx + tw + 10, by), col, -1)
                        cv2.putText(annotated, label, (bx + 5, by - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)

                # HUD Overlay in top-left
                hud_bg = annotated.copy()
                cv2.rectangle(hud_bg, (30, 30), (520, 230), (15, 15, 15), -1)
                cv2.addWeighted(hud_bg, 0.75, annotated, 0.25, 0, annotated)

                curr_status = pred["tracking_status"] if pred is not None else "LOST"
                curr_conf = float(pred["confidence"]) if pred is not None else 0.0

                hud_lines = [
                    f"GLOBAL TARGET: VEHICLE_{int(df['global_target_id'].iloc[0]):03d}",
                    f"CAMERA: {camera_id.upper()}",
                    f"FRAME: {fid:06d} / {total_frames:06d}",
                    f"STATUS: {curr_status}",
                    f"CONFIDENCE: {curr_conf:.2f}"
                ]

                for i, text in enumerate(hud_lines):
                    col = self.colors.get(curr_status, (255, 255, 255)) if "STATUS" in text else (255, 255, 255)
                    cv2.putText(annotated, text, (45, 65 + i * 32), cv2.FONT_HERSHEY_SIMPLEX, 0.75, col, 2, cv2.LINE_AA)

                # Show transition banner if reacquired or searching
                if pred is not None and pred["tracking_status"] == "REACQUIRED":
                    cv2.rectangle(annotated, (W // 2 - 350, 40), (W // 2 + 350, 110), (0, 255, 255), -1)
                    cv2.putText(annotated, "VEHICLE_001: CAMERA 1 -> CAMERA 2 [REACQUIRED]", (W // 2 - 330, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 0), 3, cv2.LINE_AA)

                out.write(annotated)

            out.release()
            print(f"[+] Rendered single-camera video to: {output_path}")
            return output_path

    def render_multi_camera_dashboard(self,
                                      method_name: str,
                                      output_path: Optional[str] = None) -> str:
        """
        Renders synchronized multi-camera dashboard video showing all cameras simultaneously.
        """
        output_path = output_path or f"outputs/videos/dashboard_{method_name}.mp4"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        tracking_csv = f"outputs/tracking_results/tracking_{method_name}.csv"
        df = pd.read_csv(tracking_csv)
        pred_index = {(row["camera_id"], int(row["frame_id"])): row for _, row in df.iterrows()}

        with CityFlowLoader(config_path=self.config_path) as loader:
            cams = loader.get_camera_ids()
            if len(cams) < 2:
                raise ValueError("At least 2 cameras required for multi-camera dashboard.")

            cam1, cam2 = cams[0], cams[1]
            total_frames = min(loader.get_video_info(cam1)["frame_count"], loader.get_video_info(cam2)["frame_count"])
            fps = loader.get_video_info(cam1)["fps"]

            # Output dashboard dimensions: 1920x600 (header 80px + two 960x520 views)
            dash_w, dash_h = 1920, 600
            pane_w, pane_h = 960, 520
            header_h = 80

            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            out = cv2.VideoWriter(output_path, fourcc, fps, (dash_w, dash_h))

            for fid in range(1, total_frames + 1):
                f1 = loader.get_frame(cam1, fid)
                f2 = loader.get_frame(cam2, fid)
                if f1 is None or f2 is None:
                    continue

                # Annotate view 1
                p1 = pred_index.get((cam1, fid))
                if p1 is not None and p1["tracking_status"] in ["ACTIVE", "REACQUIRED"]:
                    bx, by, bw, bh = int(p1["bbox_x"]), int(p1["bbox_y"]), int(p1["bbox_width"]), int(p1["bbox_height"])
                    if bw > 0 and bh > 0:
                        cv2.rectangle(f1, (bx, by), (bx + bw, by + bh), (0, 255, 0), 6)
                        cv2.putText(f1, "VEHICLE_001 [TRACKING]", (bx, max(30, by - 10)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                # Annotate view 2
                p2 = pred_index.get((cam2, fid))
                if p2 is not None and p2["tracking_status"] in ["ACTIVE", "REACQUIRED"]:
                    bx, by, bw, bh = int(p2["bbox_x"]), int(p2["bbox_y"]), int(p2["bbox_width"]), int(p2["bbox_height"])
                    if bw > 0 and bh > 0:
                        col = (0, 255, 255) if p2["tracking_status"] == "REACQUIRED" else (0, 255, 0)
                        cv2.rectangle(f2, (bx, by), (bx + bw, by + bh), col, 6)
                        cv2.putText(f2, f"VEHICLE_001 [{p2['tracking_status']}]", (bx, max(30, by - 10)), cv2.FONT_HERSHEY_SIMPLEX, 1.2, col, 3)

                # Resize to dashboard pane size
                p1_resized = cv2.resize(f1, (pane_w, pane_h))
                p2_resized = cv2.resize(f2, (pane_w, pane_h))

                # Camera labels in panes
                cv2.putText(p1_resized, f"CAMERA: {cam1.upper()}", (25, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
                cv2.putText(p2_resized, f"CAMERA: {cam2.upper()}", (25, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)

                # Combine into dashboard canvas
                canvas = np.zeros((dash_h, dash_w, 3), dtype=np.uint8)

                # Header bar
                header_text = f"Single-Target Multi-Camera Vehicle Tracking (CityFlow S01) | Target: VEHICLE_001 | Frame: {fid:03d}/{total_frames:03d}"
                cv2.rectangle(canvas, (0, 0), (dash_w, header_h), (20, 20, 20), -1)
                cv2.putText(canvas, header_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (255, 255, 255), 2, cv2.LINE_AA)

                # Status pill in header
                is_p1_active = (p1 is not None and str(p1["tracking_status"]) in ["ACTIVE", "REACQUIRED"])
                is_p2_active = (p2 is not None and str(p2["tracking_status"]) in ["ACTIVE", "REACQUIRED"])
                active_cam = cam1 if is_p1_active else (cam2 if is_p2_active else "SEARCHING")
                status_text = f"STATUS: {active_cam.upper()}"
                cv2.rectangle(canvas, (dash_w - 300, 15), (dash_w - 30, 65), (0, 120, 0) if active_cam != "SEARCHING" else (0, 140, 255), -1)
                cv2.putText(canvas, status_text, (dash_w - 280, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

                # Place camera panes
                canvas[header_h:header_h + pane_h, 0:pane_w] = p1_resized
                canvas[header_h:header_h + pane_h, pane_w:pane_w * 2] = p2_resized

                # Dividing line
                cv2.line(canvas, (pane_w, header_h), (pane_w, dash_h), (100, 100, 100), 2)

                out.write(canvas)

            out.release()
            print(f"[+] Rendered Multi-Camera Dashboard Video to: {output_path}")
            return output_path

    def plot_target_trajectories(self,
                                 method_name: str,
                                 output_path: Optional[str] = None) -> str:
        """
        Plots spatial 2D trajectory of the target across camera views.
        """
        output_path = output_path or f"outputs/plots/target_trajectory_{method_name}.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        tracking_csv = f"outputs/tracking_results/tracking_{method_name}.csv"
        df = pd.read_csv(tracking_csv)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(f"Target Vehicle 1 Spatial Trajectories Across Cameras ({method_name})", fontsize=14, fontweight="bold")

        # Camera 1 Trajectory
        df_c1 = df[(df["camera_id"] == "c001") & (df["bbox_width"] > 0)]
        if not df_c1.empty:
            cx1 = df_c1["bbox_x"] + df_c1["bbox_width"] / 2.0
            cy1 = df_c1["bbox_y"] + df_c1["bbox_height"] / 2.0
            sc1 = ax1.scatter(cx1, cy1, c=df_c1["frame_id"], cmap="cool", s=40, edgecolors="k", linewidth=0.5)
            ax1.plot(cx1, cy1, color="blue", linestyle="--", alpha=0.6)
            ax1.set_title("Camera c001 View (Entrance & Traversal)")
            ax1.set_xlim(0, 1920)
            ax1.set_ylim(1080, 0)
            ax1.set_xlabel("X (pixels)")
            ax1.set_ylabel("Y (pixels)")
            plt.colorbar(sc1, ax=ax1, label="Frame ID")
        else:
            ax1.text(0.5, 0.5, "No tracking data in c001", ha="center", va="center")

        # Camera 2 Trajectory
        df_c2 = df[(df["camera_id"] == "c002") & (df["bbox_width"] > 0)]
        if not df_c2.empty:
            cx2 = df_c2["bbox_x"] + df_c2["bbox_width"] / 2.0
            cy2 = df_c2["bbox_y"] + df_c2["bbox_height"] / 2.0
            sc2 = ax2.scatter(cx2, cy2, c=df_c2["frame_id"], cmap="Wistia", s=40, edgecolors="k", linewidth=0.5)
            ax2.plot(cx2, cy2, color="orange", linestyle="--", alpha=0.6)
            ax2.set_title("Camera c002 View (Reacquisition & Transit)")
            ax2.set_xlim(0, 1920)
            ax2.set_ylim(1080, 0)
            ax2.set_xlabel("X (pixels)")
            ax2.set_ylabel("Y (pixels)")
            plt.colorbar(sc2, ax=ax2, label="Frame ID")
        else:
            ax2.text(0.5, 0.5, "Target Not Reacquired in c002", ha="center", va="center", color="red", fontweight="bold")

        plt.tight_layout()
        plt.savefig(output_path, dpi=200)
        plt.close()
        print(f"[+] Target trajectory plot saved: {output_path}")
        return output_path

    def plot_baseline_comparisons(self,
                                 metrics_csv: str = "outputs/reports/benchmark_metrics.csv",
                                 output_path: str = "outputs/plots/baseline_comparison.png") -> str:
        """
        Generates comprehensive comparative bar charts for all baselines and proposed method.
        """
        if not os.path.exists(metrics_csv):
            raise FileNotFoundError(f"Metrics CSV not found: {metrics_csv}")

        df = pd.read_csv(metrics_csv)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle("M.Tech Video Analytics: Multi-Camera Tracking Benchmark Comparison", fontsize=15, fontweight="bold")

        clean_labels = [m.replace("_", " ").title() for m in df["method"]]
        palette = sns.color_palette("Set2", len(df))

        # 1. Mean IoU
        sns.barplot(x=clean_labels, y=df["mean_iou"], ax=axes[0, 0], palette=palette)
        axes[0, 0].set_title("Mean Bounding-Box IoU")
        axes[0, 0].set_ylabel("IoU")
        axes[0, 0].set_ylim(0, 1.0)
        for i, v in enumerate(df["mean_iou"]):
            axes[0, 0].text(i, v + 0.02, f"{v:.3f}", ha="center", fontweight="bold")

        # 2. Identification F1 (IDF1)
        sns.barplot(x=clean_labels, y=df["idf1"], ax=axes[0, 1], palette=palette)
        axes[0, 1].set_title("Identification F1 (IDF1)")
        axes[0, 1].set_ylabel("IDF1 Score")
        axes[0, 1].set_ylim(0, 1.0)
        for i, v in enumerate(df["idf1"]):
            axes[0, 1].text(i, v + 0.02, f"{v:.3f}", ha="center", fontweight="bold")

        # 3. Target Reacquisition Rate (%)
        reacq_pct = df["reacquisition_rate"] * 100.0
        sns.barplot(x=clean_labels, y=reacq_pct, ax=axes[1, 0], palette=palette)
        axes[1, 0].set_title("Target Reacquisition Rate (%)")
        axes[1, 0].set_ylabel("Reacquisition Success (%)")
        axes[1, 0].set_ylim(0, 115)
        for i, v in enumerate(reacq_pct):
            axes[1, 0].text(i, v + 3, f"{v:.1f}%", ha="center", fontweight="bold")

        # 4. Processing Throughput (FPS)
        sns.barplot(x=clean_labels, y=df["fps"], ax=axes[1, 1], palette=palette)
        axes[1, 1].set_title("Processing Throughput (FPS)")
        axes[1, 1].set_ylabel("Frames Per Second")
        for i, v in enumerate(df["fps"]):
            axes[1, 1].text(i, v + 1.0, f"{v:.1f}", ha="center", fontweight="bold")

        for ax in axes.flat:
            ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha="right")

        plt.tight_layout()
        plt.savefig(output_path, dpi=200)
        plt.close()
        print(f"[+] Baseline comparison plot saved: {output_path}")
        return output_path


if __name__ == "__main__":
    vis = Visualizer()
    vis.render_annotated_camera_video("proposed_adaptive", "c001")
    vis.render_annotated_camera_video("proposed_adaptive", "c002")
    vis.render_multi_camera_dashboard("proposed_adaptive")
    vis.plot_target_trajectories("proposed_adaptive")
    vis.plot_baseline_comparisons()
