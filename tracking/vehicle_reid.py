"""
Vehicle Re-Identification (ReID) Module.

Extracts robust visual appearance embeddings from vehicle bounding boxes using:
1. Pretrained ResNet-50 CNN (ImageNet weights) with global average pooling and L2 normalization.
2. Spatial-part multi-bin HSV color histogram representation (roof, body, wheels).
3. Dynamic Appearance Gallery: Maintains diverse historical embeddings of the target vehicle.
4. Cosine Similarity Matching: Computes similarity against the target gallery.
"""

import cv2
import numpy as np
from typing import List, Optional, Tuple, Dict, Any

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
import torchvision.transforms as T


class VehicleReIDExtractor:
    """
    Appearance feature extractor and gallery manager for vehicle re-identification.
    """

    def __init__(self,
                 backbone: str = "resnet50",
                 embedding_dim: int = 2048,
                 device: str = "cuda",
                 gallery_size: int = 10,
                 ema_alpha: float = 0.10):
        self.backbone_name = backbone.lower()
        self.embedding_dim = embedding_dim
        self.gallery_size = gallery_size
        self.ema_alpha = ema_alpha

        if device == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.model = None
        self._initialize_backbone()

        # Image preprocessing pipeline
        self.transform = T.Compose([
            T.ToPILImage(),
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        # Target appearance gallery: list of normalized embedding vectors (numpy arrays)
        self.gallery: List[np.ndarray] = []
        # Representative running average embedding
        self.running_embedding: Optional[np.ndarray] = None

    def _initialize_backbone(self):
        """Loads pretrained deep backbone."""
        print(f"[*] Initializing VehicleReID backbone: '{self.backbone_name}' on device: {self.device}")

        if self.backbone_name == "resnet50":
            try:
                base = models.resnet50(weights="DEFAULT")
            except Exception:
                base = models.resnet50(weights=None)
            base.fc = nn.Identity()  # Extract 2048-d feature vector
            self.model = base.to(self.device)
            self.model.eval()

        elif self.backbone_name == "mobilenet_v3":
            try:
                base = models.mobilenet_v3_large(weights="DEFAULT")
            except Exception:
                base = models.mobilenet_v3_large(weights=None)
            base.classifier = nn.Identity()
            self.model = base.to(self.device)
            self.model.eval()

        else:
            raise ValueError(f"Unsupported ReID backbone: {self.backbone_name}")

    def extract_embedding(self, frame: np.ndarray, bbox: List[int]) -> Optional[np.ndarray]:
        """
        Extracts L2-normalized feature embedding from vehicle bounding box crop.
        Returns 1D numpy array of shape (embedding_dim + color_dim,).
        """
        H, W = frame.shape[:2]
        x, y, w, h = [int(v) for v in bbox]

        # Boundary checks
        x = max(0, min(x, W - 1))
        y = max(0, min(y, H - 1))
        w = max(5, min(w, W - x))
        h = max(5, min(h, H - y))

        crop = frame[y:y + h, x:x + w]
        if crop.size == 0 or crop.shape[0] < 5 or crop.shape[1] < 5:
            return None

        # 1. Deep CNN feature
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        tensor = self.transform(rgb).unsqueeze(0).to(self.device)

        with torch.no_grad():
            feat = self.model(tensor)
            feat = F.normalize(feat, p=2, dim=1)
            cnn_emb = feat.squeeze(0).cpu().numpy()

        # 2. Spatial-Part Color Histogram (3 horizontal stripes: upper, middle, lower)
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        h_stripes = np.array_split(hsv, 3, axis=0)
        hist_parts = []
        for stripe in h_stripes:
            hist_h = cv2.calcHist([stripe], [0], None, [16], [0, 180])
            hist_s = cv2.calcHist([stripe], [1], None, [8], [0, 256])
            hist_v = cv2.calcHist([stripe], [2], None, [8], [0, 256])
            part_vec = np.concatenate([hist_h.flatten(), hist_s.flatten(), hist_v.flatten()])
            norm = np.linalg.norm(part_vec) + 1e-6
            hist_parts.append(part_vec / norm)

        color_emb = np.concatenate(hist_parts)
        color_emb = color_emb / (np.linalg.norm(color_emb) + 1e-6)

        # 3. Fused Appearance Vector
        # Weighted combination: 80% deep CNN representation, 20% spatial color
        fused = np.concatenate([0.80 * cnn_emb, 0.20 * color_emb])
        fused = fused / (np.linalg.norm(fused) + 1e-6)
        return fused

    def update_target_gallery(self, embedding: np.ndarray, confidence: float = 1.0):
        """
        Adds high-confidence embedding to gallery and updates running embedding.
        """
        if embedding is None:
            return

        if self.running_embedding is None:
            self.running_embedding = embedding.copy()
            self.gallery.append(embedding.copy())
            return

        # Update running embedding via EMA
        self.running_embedding = (1.0 - self.ema_alpha) * self.running_embedding + self.ema_alpha * embedding
        self.running_embedding /= (np.linalg.norm(self.running_embedding) + 1e-6)

        # Gallery diversity check: Only add if sufficiently distinct from existing gallery items
        min_sim = 1.0
        for g in self.gallery:
            sim = float(np.dot(embedding, g))
            if sim < min_sim:
                min_sim = sim

        # If novel viewpoint or lighting (sim < 0.95), add to gallery
        if min_sim < 0.95 or len(self.gallery) < self.gallery_size:
            if len(self.gallery) >= self.gallery_size:
                self.gallery.pop(0)  # Evict oldest
            self.gallery.append(embedding.copy())

    def compute_similarity(self, candidate_embedding: np.ndarray) -> float:
        """
        Computes maximum cosine similarity between candidate embedding and target gallery.
        """
        if candidate_embedding is None or not self.gallery:
            return 0.0

        sims = [float(np.dot(candidate_embedding, g)) for g in self.gallery]
        # Return composite: 70% max gallery match + 30% running average match
        max_sim = max(sims)
        avg_sim = float(np.dot(candidate_embedding, self.running_embedding)) if self.running_embedding is not None else max_sim
        score = 0.70 * max_sim + 0.30 * avg_sim
        return float(np.clip(score, 0.0, 1.0))

    def reset_gallery(self):
        """Resets the gallery and running appearance state."""
        self.gallery.clear()
        self.running_embedding = None
