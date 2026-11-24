"""
Unit and Integration Test Suite for CityFlow Single-Target Tracking Pipeline.
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.cityflow_loader import CityFlowLoader
from data.annotation_parser import CityFlowAnnotationParser
from tracking.local_tracker import CSRTTracker
from tracking.vehicle_detector import VehicleDetector
from tracking.vehicle_reid import VehicleReIDExtractor
from tracking.camera_association import CrossCameraAssociation
from tracking.target_manager import GlobalTargetManager, TargetStatus
from evaluation.metrics import compute_iou, compute_center_error, TrackingMetricsEvaluator


class TestCityFlowPipeline:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.config_path = "config/config.yaml"

    def test_cityflow_loader_initialization(self):
        """Tests that CityFlowLoader discovers real cameras and opens video streams."""
        with CityFlowLoader(config_path=self.config_path) as loader:
            cams = loader.get_camera_ids()
            assert len(cams) >= 2, f"Expected at least 2 cameras, found {cams}"
            assert "c001" in cams and "c002" in cams

            # Verify video stream properties
            info_c1 = loader.get_video_info("c001")
            assert info_c1["width"] == 1920
            assert info_c1["height"] == 1080
            assert info_c1["fps"] == 30.0
            assert info_c1["frame_count"] > 0

            # Test frame retrieval
            frame = loader.get_frame("c001", 1)
            assert frame is not None
            assert frame.shape == (1080, 1920, 3)

    def test_annotation_parser_unified_structure(self):
        """Tests that annotations are normalized into unified CityFlow structure."""
        parser = CityFlowAnnotationParser()
        gt_path = "sample_data/cityflow_sample/S01/c001/gt/gt.txt"
        records = parser.parse_camera_gt("c001", gt_path)
        assert len(records) > 0

        sample = records[0]
        assert "camera_id" in sample and sample["camera_id"] == "c001"
        assert "frame_id" in sample and sample["frame_id"] == 1
        assert "vehicle_id" in sample and sample["vehicle_id"] == 1
        assert "bbox" in sample and len(sample["bbox"]) == 4

        # Test index lookups
        bbox = parser.get_target_bbox("c001", 1, target_id=1)
        assert bbox is not None and len(bbox) == 4

    def test_local_tracker_csrt(self):
        """Tests local single-object tracker initialization and failure detection."""
        tracker = CSRTTracker()
        dummy_frame = np.ones((1080, 1920, 3), dtype=np.uint8) * 128
        # Draw distinctive rectangle
        dummy_frame[400:600, 500:700] = 200

        ok = tracker.init(dummy_frame, [500, 400, 200, 200])
        assert ok is True

        # Test update on identical frame
        ok, box, conf = tracker.update(dummy_frame)
        assert ok is True
        assert conf > 0.60

        # Test boundary failure detection (box reaches edge)
        dummy_frame_edge = np.zeros((1080, 1920, 3), dtype=np.uint8)
        ok_edge, box_edge, conf_edge = tracker.update(dummy_frame_edge)
        assert ok_edge is False

    def test_vehicle_reid_extractor(self):
        """Tests deep appearance embedding extraction and cosine similarity."""
        reid = VehicleReIDExtractor(backbone="resnet50", device="cpu")
        frame = np.ones((1080, 1920, 3), dtype=np.uint8) * 100
        # Simulated vehicle patch
        frame[300:500, 400:600] = [120, 110, 105]

        emb1 = reid.extract_embedding(frame, [400, 300, 200, 200])
        assert emb1 is not None
        assert isinstance(emb1, np.ndarray)
        assert abs(np.linalg.norm(emb1) - 1.0) < 1e-3  # L2 normalized

        # Update gallery
        reid.update_target_gallery(emb1, confidence=1.0)
        assert len(reid.gallery) == 1

        # Match against identical embedding
        sim_self = reid.compute_similarity(emb1)
        assert sim_self > 0.95

    def test_cross_camera_association_scoring(self):
        """Tests spatial-temporal and adaptive reliability scoring."""
        assoc = CrossCameraAssociation()

        # Gaussian travel delay consistency
        # Expected delay between c001 and c002 is 15 frames
        s_exact = assoc.compute_temporal_consistency("c001", "c002", travel_delay_frames=15)
        s_far = assoc.compute_temporal_consistency("c001", "c002", travel_delay_frames=80)
        assert s_exact > 0.90
        assert s_far < 0.10

        # Adaptive reliability scoring
        score_dict = assoc.compute_adaptive_reliability_score(
            appearance_sim=0.80,
            from_camera="c001",
            to_camera="c002",
            travel_delay=16,
            last_bbox=[605, 448, 459, 258],
            candidate_bbox=[576, 475, 226, 224],
            detection_confidence=0.90
        )
        assert "total_score" in score_dict
        assert 0.0 <= score_dict["total_score"] <= 1.0
        assert score_dict["total_score"] > 0.60

    def test_global_target_manager_state_machine(self):
        """Tests persistent state transitions: ACTIVE -> LOST -> SEARCHING -> REACQUIRED."""
        manager = GlobalTargetManager(global_target_id=1, initial_camera="c001", initial_bbox=[100, 100, 50, 50])
        assert manager.status == TargetStatus.ACTIVE

        manager.mark_lost("c001", frame_id=20)
        assert manager.status == TargetStatus.LOST
        assert manager.current_bbox is None

        manager.mark_searching(frame_id=25)
        assert manager.status == TargetStatus.SEARCHING

        manager.mark_reacquired(
            new_camera_id="c002",
            frame_id=35,
            bbox=[200, 200, 60, 60],
            confidence=0.92,
            association_score=0.85
        )
        assert manager.status == TargetStatus.REACQUIRED
        assert manager.current_camera_id == "c002"
        assert manager.global_target_id == 1  # ID persists!
        assert len(manager.transition_history) == 1

    def test_evaluation_metrics_math(self):
        """Tests IoU and center location error mathematical implementations."""
        box1 = [100, 100, 100, 100]
        box2 = [100, 100, 100, 100]
        assert compute_iou(box1, box2) == 1.0
        assert compute_center_error(box1, box2) == 0.0

        box3 = [150, 100, 100, 100]  # Overlaps 50x100 = 5000 px, Union = 15000 px
        assert abs(compute_iou(box1, box3) - (5000 / 15000)) < 1e-4
        assert compute_center_error(box1, box3) == 50.0
