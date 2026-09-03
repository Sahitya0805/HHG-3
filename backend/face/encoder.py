"""Face embedding generation module producing normalized 512-dimensional representations."""

import cv2
import numpy as np
from typing import List, Dict, Any


class FaceEncoder:
    """Generates normalized 512-dimensional face embeddings.

    InsightFace/ArcFace is preferred when installed. The OpenCV feature encoder is
    retained as a deterministic fallback for local tests and constrained demos.
    """

    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim
        self.model_name = "opencv-structural-fallback"
        self._insightface = None

        try:
            from insightface.app import FaceAnalysis

            app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(640, 640))
            self._insightface = app
            self.model_name = "insightface-arcface-buffalo_l"
        except Exception:
            self._insightface = None

    def generate_embedding(self, face_crop_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Extract normalized 512-dim facial representation from cropped face image.
        Uses ArcFace when available; otherwise uses multi-region spatial histogram
        and frequency transform features for a reproducible fallback.
        """
        if face_crop_bgr is None or face_crop_bgr.size == 0:
            raise ValueError("Invalid face crop provided for embedding.")

        if self._insightface is not None:
            rgb = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2RGB)
            faces = self._insightface.get(rgb)
            if faces:
                face = max(
                    faces,
                    key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]),
                )
                embedding = np.array(face.embedding, dtype=np.float32)
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

                if len(embedding) != self.embedding_dim:
                    embedding = np.resize(embedding, self.embedding_dim)

                embedding_list = [float(round(val, 6)) for val in embedding]
                return {
                    "embedding_generated": True,
                    "embedding_dimensions": len(embedding_list),
                    "norm": float(round(np.linalg.norm(embedding), 4)),
                    "embedding": embedding_list,
                    "sample_vector": embedding_list[:8],
                    "model": self.model_name,
                }

        # Standardize face dimensions to 160x160
        target_size = (160, 160)
        resized = cv2.resize(face_crop_bgr, target_size, interpolation=cv2.INTER_AREA)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # 1. Multi-scale block spatial features
        blocks = 8  # 8x8 grid -> 64 spatial cells
        cell_h, cell_w = target_size[0] // blocks, target_size[1] // blocks
        spatial_features = []

        for r in range(blocks):
            for c in range(blocks):
                cell = gray[r * cell_h : (r + 1) * cell_h, c * cell_w : (c + 1) * cell_w]
                mean = np.mean(cell) / 255.0
                std = np.std(cell) / 255.0
                grad_x = cv2.Sobel(cell, cv2.CV_64F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(cell, cv2.CV_64F, 0, 1, ksize=3)
                mag_mean = np.mean(np.sqrt(grad_x**2 + grad_y**2)) / 255.0
                spatial_features.extend([mean, std, mag_mean])

        # 64 cells * 3 = 192 features

        # 2. Discrete Cosine Transform (DCT) low & mid-frequency facial structure
        dct_matrix = cv2.dct(np.float32(gray) / 255.0)
        dct_features = dct_matrix[:16, :16].flatten()  # 256 features

        # 3. Central landmark region focus (eyes & mouth zone)
        center_zone = gray[40:120, 40:120]
        center_hist = cv2.calcHist([center_zone], [0], None, [64], [0, 256]).flatten()
        center_hist = center_hist / (np.sum(center_hist) + 1e-7)  # 64 features

        combined = np.concatenate([spatial_features, dct_features, center_hist])
        # Total = 192 + 256 + 64 = 512 features

        if len(combined) != self.embedding_dim:
            # Resize or pad if needed to exactly match target dimension
            combined = np.resize(combined, self.embedding_dim)

        # L2 Normalization (Unit vector)
        norm = np.linalg.norm(combined)
        if norm > 0:
            normalized_embedding = combined / norm
        else:
            normalized_embedding = combined

        embedding_list = [float(round(val, 6)) for val in normalized_embedding]

        return {
            "embedding_generated": True,
            "embedding_dimensions": len(embedding_list),
            "norm": float(round(np.linalg.norm(normalized_embedding), 4)),
            "embedding": embedding_list,
            "sample_vector": embedding_list[:8],  # Snippet for display
            "model": self.model_name,
        }
