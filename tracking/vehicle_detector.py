"""
Vehicle Detection Module.

Implements deep-learning vehicle detection supporting COCO vehicle classes:
- car
- bus
- truck
- motorcycle

Supports multiple configurable backends:
1. 'ssdlite': Pretrained SSDLite MobileNetV3 (high-speed, real-time CPU/GPU).
2. 'fasterrcnn': Pretrained Faster R-CNN MobileNetV3 FPN.
3. 'yolo': Ultralytics YOLO (if available).
4. 'opencv': OpenCV DNN / Background Subtractor fallback.
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

import torch
import torchvision.transforms as T
import torchvision.models.detection as detection


COCO_VEHICLE_CLASSES = {
    3: "car",
    4: "motorcycle",
    6: "bus",
    8: "truck"
}


class VehicleDetector:
    """
    Modular vehicle detector for surveillance traffic streams.
    """

    def __init__(self,
                 backend: str = "ssdlite",
                 confidence_threshold: float = 0.40,
                 device: str = "cuda",
                 nms_threshold: float = 0.45):
        self.backend_name = backend.lower()
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold

        # Device selection with fallback
        if device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.model = None
        self._initialize_backend()

    def _initialize_backend(self):
        """Initializes the chosen detection backend."""
        print(f"[*] Initializing VehicleDetector backend: '{self.backend_name}' on device: {self.device}")

        if self.backend_name == "ssdlite":
            try:
                self.model = detection.ssdlite320_mobilenet_v3_large(weights="DEFAULT")
                self.model.to(self.device)
                self.model.eval()
            except Exception as e:
                print(f"[!] Warning: Could not initialize SSDLite with weights ({e}). Initializing architecture.")
                self.model = detection.ssdlite320_mobilenet_v3_large(weights=None)
                self.model.to(self.device)
                self.model.eval()

        elif self.backend_name == "fasterrcnn":
            try:
                self.model = detection.fasterrcnn_mobilenet_v3_large_fpn(weights="DEFAULT")
                self.model.to(self.device)
                self.model.eval()
            except Exception as e:
                print(f"[!] Falling back to SSDLite due to: {e}")
                self.backend_name = "ssdlite"
                self._initialize_backend()

        elif self.backend_name == "yolo":
            try:
                from ultralytics import YOLO
                self.model = YOLO("yolov8n.pt")
            except Exception as e:
                print(f"[!] Ultralytics YOLO not available ({e}). Falling back to SSDLite.")
                self.backend_name = "ssdlite"
                self._initialize_backend()

        elif self.backend_name == "opencv":
            self.model = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=16, detectShadows=True)

        else:
            raise ValueError(f"Unsupported detector backend: {self.backend_name}")

    def detect(self,
               frame: np.ndarray,
               roi_mask: Optional[np.ndarray] = None) -> List[Dict[str, Any]]:
        """
        Runs vehicle detection on frame.
        Returns list of detections: [ { "bbox": [x, y, w, h], "confidence": conf, "class_name": class } ]
        """
        if self.model is None:
            return []

        H, W = frame.shape[:2]
        detections = []

        if self.backend_name in ["ssdlite", "fasterrcnn"]:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            tensor = T.functional.to_tensor(rgb).unsqueeze(0).to(self.device)

            with torch.no_grad():
                preds = self.model(tensor)[0]

            boxes = preds["boxes"].detach().cpu().numpy()
            labels = preds["labels"].detach().cpu().numpy()
            scores = preds["scores"].detach().cpu().numpy()

            raw_boxes = []
            raw_scores = []
            raw_classes = []

            for b, l, s in zip(boxes, labels, scores):
                if s >= self.confidence_threshold and l in COCO_VEHICLE_CLASSES:
                    x1, y1, x2, y2 = [int(v) for v in b]
                    x1 = max(0, min(x1, W - 1))
                    y1 = max(0, min(y1, H - 1))
                    w = max(10, min(x2 - x1, W - x1))
                    h = max(10, min(y2 - y1, H - y1))

                    # Apply ROI mask if present
                    if roi_mask is not None:
                        cx, cy = int(x1 + w / 2), int(y1 + h / 2)
                        if cx < roi_mask.shape[1] and cy < roi_mask.shape[0]:
                            if roi_mask[cy, cx] == 0:
                                continue

                    raw_boxes.append([x1, y1, w, h])
                    raw_scores.append(float(s))
                    raw_classes.append(COCO_VEHICLE_CLASSES[l])

            # Apply OpenCV NMS
            if raw_boxes:
                indices = cv2.dnn.NMSBoxes(raw_boxes, raw_scores, self.confidence_threshold, self.nms_threshold)
                if len(indices) > 0:
                    for i in indices.flatten():
                        detections.append({
                            "bbox": raw_boxes[i],
                            "confidence": raw_scores[i],
                            "class_name": raw_classes[i]
                        })

        elif self.backend_name == "opencv":
            # Motion-based contour candidate detector
            fg_mask = self.model.apply(frame)
            if roi_mask is not None:
                fg_mask = cv2.bitwise_and(fg_mask, fg_mask, mask=roi_mask)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            cleaned = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 1200:  # Vehicle scale threshold
                    x, y, w, h = cv2.boundingRect(cnt)
                    detections.append({
                        "bbox": [x, y, w, h],
                        "confidence": 0.65,
                        "class_name": "vehicle"
                    })

        return detections
