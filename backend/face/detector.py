"""Advanced multi-scale face detection & alignment module."""

import os
import cv2
import math
import numpy as np
import base64
from typing import Dict, Any, List, Optional, Tuple


class FaceDetector:
    """
    High-accuracy face detection and alignment engine.
    Uses YuNet deep neural network with multi-scale image pyramids,
    CLAHE lighting normalization, and facial landmark alignment.
    """

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.yunet_model = os.path.join(models_dir, "face_detection_yunet_2023mar.onnx")
        self.cascade_default_path = os.path.join(models_dir, "haarcascade_frontalface_default.xml")
        self.cascade_alt_path = os.path.join(models_dir, "haarcascade_frontalface_alt2.xml")
        self.cascade_profile_path = os.path.join(models_dir, "haarcascade_profileface.xml")

        self.yunet = None
        if os.path.exists(self.yunet_model) and hasattr(cv2, "FaceDetectorYN"):
            try:
                self.yunet = cv2.FaceDetectorYN.create(
                    model=self.yunet_model,
                    config="",
                    input_size=(320, 320),
                    score_threshold=0.30,
                    nms_threshold=0.3,
                    top_k=5000,
                )
            except Exception:
                self.yunet = None

        self.cascade_alt = None
        if os.path.exists(self.cascade_alt_path) and hasattr(cv2, "CascadeClassifier"):
            try:
                self.cascade_alt = cv2.CascadeClassifier(self.cascade_alt_path)
            except Exception:
                self.cascade_alt = None

        self.cascade_default = None
        if os.path.exists(self.cascade_default_path) and hasattr(cv2, "CascadeClassifier"):
            try:
                self.cascade_default = cv2.CascadeClassifier(self.cascade_default_path)
            except Exception:
                self.cascade_default = None

    def load_image(self, image_bytes: bytes) -> np.ndarray:
        """Decode raw image bytes into an OpenCV BGR numpy array."""
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes into valid image.")
        return img

    def _enhance_lighting(self, img_bgr: np.ndarray) -> np.ndarray:
        """Applies CLAHE (Contrast Limited Adaptive Histogram Equalization) in LAB space."""
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        enhanced_lab = cv2.merge((cl, a, b))
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

    def _align_face(self, img_bgr: np.ndarray, landmarks: List[List[int]], box: List[int]) -> np.ndarray:
        """
        Aligns face horizontally based on eye landmarks and crops with proportional margins.
        """
        x, y, w, h = box
        img_h, img_w = img_bgr.shape[:2]

        if len(landmarks) >= 2:
            # Right eye and Left eye landmarks
            r_eye, l_eye = landmarks[0], landmarks[1]
            dx = l_eye[0] - r_eye[0]
            dy = l_eye[1] - r_eye[1]
            angle = math.degrees(math.atan2(dy, dx))

            # Limit rotation to reasonable portrait head tilt (-35 to 35 degrees)
            if -35.0 <= angle <= 35.0 and abs(angle) > 1.5:
                center = ((r_eye[0] + l_eye[0]) // 2, (r_eye[1] + l_eye[1]) // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(img_bgr, M, (img_w, img_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            else:
                rotated = img_bgr
        else:
            rotated = img_bgr

        # Proportional padding for clean portrait crop
        pad_top = int(h * 0.25)
        pad_bottom = int(h * 0.20)
        pad_sides = int(w * 0.20)

        x1 = max(0, x - pad_sides)
        y1 = max(0, y - pad_top)
        x2 = min(img_w, x + w + pad_sides)
        y2 = min(img_h, y + h + pad_bottom)

        return rotated[y1:y2, x1:x2]

    def detect_faces(self, img_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Multi-scale, multi-exposure face detection.
        Returns detection metadata, confidence score, bounding boxes, landmarks, and aligned crops.
        """
        img_h, img_w = img_bgr.shape[:2]
        detected_candidates = []

        # Multi-scale pyramid scales to test
        scales = [1.0]
        if max(img_w, img_h) > 900:
            scales = [640.0 / max(img_w, img_h), 1.0, 0.5]
        elif max(img_w, img_h) < 400:
            scales = [1.0, 1.5, 2.0]
        else:
            scales = [1.0, 0.75, 1.25]

        # 1. Test original and CLAHE lighting enhanced variations
        variations = [img_bgr, self._enhance_lighting(img_bgr)]

        if self.yunet is not None:
            for v_img in variations:
                if detected_candidates:
                    break
                for s in scales:
                    target_w = max(32, int(img_w * s))
                    target_h = max(32, int(img_h * s))
                    scaled_img = cv2.resize(v_img, (target_w, target_h), interpolation=cv2.INTER_AREA if s < 1.0 else cv2.INTER_LINEAR)
                    
                    self.yunet.setInputSize((target_w, target_h))
                    _, detections = self.yunet.detect(scaled_img)
                    
                    if detections is not None and len(detections) > 0:
                        for det in detections:
                            confidence = float(det[-1])
                            if confidence >= 0.32:
                                fx = max(0, int(det[0] / s))
                                fy = max(0, int(det[1] / s))
                                fw = min(img_w - fx, int(det[2] / s))
                                fh = min(img_h - fy, int(det[3] / s))

                                # Verify valid aspect ratio (faces typically between 0.65 and 1.8)
                                aspect = float(fh) / max(1, fw)
                                if 0.55 <= aspect <= 2.2 and fw > 20 and fh > 20:
                                    landmarks = [
                                        [int(det[4] / s), int(det[5] / s)],
                                        [int(det[6] / s), int(det[7] / s)],
                                        [int(det[8] / s), int(det[9] / s)],
                                        [int(det[10] / s), int(det[11] / s)],
                                        [int(det[12] / s), int(det[13] / s)],
                                    ]
                                    detected_candidates.append({
                                        "box": [fx, fy, fw, fh],
                                        "confidence": round(confidence, 3),
                                        "landmarks": landmarks,
                                        "method": f"YuNet (Scale {round(s, 2)})",
                                    })
                        if detected_candidates:
                            break

        # 2. Complementary: Multi-scale Cascades if deep network didn't find a face
        if not detected_candidates and (self.cascade_alt or self.cascade_default):
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            
            cascade_res = []
            if self.cascade_alt and not self.cascade_alt.empty():
                cascade_res = self.cascade_alt.detectMultiScale(
                    gray, scaleFactor=1.06, minNeighbors=3, minSize=(35, 35)
                )
            if len(cascade_res) == 0 and self.cascade_default and not self.cascade_default.empty():
                cascade_res = self.cascade_default.detectMultiScale(
                    gray, scaleFactor=1.08, minNeighbors=3, minSize=(35, 35)
                )

            for f in cascade_res:
                fx, fy, fw, fh = int(f[0]), int(f[1]), int(f[2]), int(f[3])
                detected_candidates.append({
                    "box": [fx, fy, fw, fh],
                    "confidence": 0.85,
                    "landmarks": [],
                    "method": "Haar Cascade",
                })

        num_faces = len(detected_candidates)
        if num_faces == 0:
            return {
                "face_detected": False,
                "faces_found": 0,
                "boxes": [],
                "primary_face_crop": None,
                "primary_crop_b64": None,
                "annotated_image_b64": self._encode_image_b64(img_bgr),
                "error": "No human face detected. Please upload an image with a visible face.",
            }

        # Select primary face (highest confidence & prominent area)
        detected_candidates.sort(key=lambda f: f["confidence"] * math.sqrt(f["box"][2] * f["box"][3]), reverse=True)
        primary = detected_candidates[0]
        x, y, w, h = primary["box"]

        # Generate aligned crop
        aligned_crop = self._align_face(img_bgr, primary.get("landmarks", []), [x, y, w, h])

        # Create high-visibility visual annotation
        annotated = img_bgr.copy()
        for idx, f_info in enumerate(detected_candidates):
            fx, fy, fw, fh = f_info["box"]
            color = (0, 255, 0) if idx == 0 else (0, 165, 255)
            # Bounding box
            cv2.rectangle(annotated, (fx, fy), (fx + fw, fy + fh), color, 2)
            
            # Corner accents
            corner_len = int(min(fw, fh) * 0.18)
            cv2.line(annotated, (fx, fy), (fx + corner_len, fy), (0, 255, 255), 3)
            cv2.line(annotated, (fx, fy), (fx, fy + corner_len), (0, 255, 255), 3)
            cv2.line(annotated, (fx + fw, fy), (fx + fw - corner_len, fy), (0, 255, 255), 3)
            cv2.line(annotated, (fx + fw, fy), (fx + fw, fy + corner_len), (0, 255, 255), 3)

            # Confidence label tag
            conf_pct = int(f_info["confidence"] * 100)
            label = f"Face ({conf_pct}%)" if idx == 0 else f"Face #{idx+1} ({conf_pct}%)"
            
            # Label background box
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(annotated, (fx, max(0, fy - 20)), (fx + text_w + 10, fy), (15, 23, 42), -1)
            cv2.putText(
                annotated,
                label,
                (fx + 5, max(12, fy - 5)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (34, 211, 238),
                1,
                cv2.LINE_AA,
            )

            # Draw facial landmarks with glowing dots
            for lx, ly in f_info.get("landmarks", []):
                cv2.circle(annotated, (lx, ly), 4, (0, 255, 255), -1)
                cv2.circle(annotated, (lx, ly), 2, (15, 23, 42), -1)

        boxes = [f["box"] for f in detected_candidates]

        return {
            "face_detected": True,
            "faces_found": num_faces,
            "boxes": boxes,
            "primary_box": [x, y, w, h],
            "confidence": primary["confidence"],
            "confidence_percent": round(primary["confidence"] * 100, 1),
            "primary_face_crop": aligned_crop,
            "primary_crop_b64": self._encode_image_b64(aligned_crop),
            "annotated_image_b64": self._encode_image_b64(annotated),
            "detection_method": primary["method"],
            "warning": "Multiple faces detected. Selected the primary face." if num_faces > 1 else None,
        }

    def _encode_image_b64(self, img: np.ndarray) -> str:
        """Encode OpenCV image to base64 jpeg."""
        if img is None or img.size == 0:
            return ""
        success, buffer = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if not success:
            return ""
        return "data:image/jpeg;base64," + base64.b64encode(buffer).decode("utf-8")
