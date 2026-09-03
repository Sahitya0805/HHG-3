"""Unit tests for face detection, embedding generation, and cosine similarity matching."""

import os
import cv2
import numpy as np
import pytest
from backend.face.detector import FaceDetector
from backend.face.encoder import FaceEncoder
from backend.face.matcher import FaceMatcher


def test_face_detector_and_encoder():
    detector = FaceDetector()
    encoder = FaceEncoder(embedding_dim=512)

    sample_path = "samples/demo_face.jpg"
    assert os.path.exists(sample_path), "Sample demo face image must exist"

    with open(sample_path, "rb") as f:
        img_bytes = f.read()

    img_bgr = detector.load_image(img_bytes)
    res = detector.detect_faces(img_bgr)

    assert res["face_detected"] is True
    assert res["faces_found"] >= 1
    assert res["primary_face_crop"] is not None
    assert res["primary_crop_b64"].startswith("data:image/jpeg;base64,")

    # Embedding generation
    emb_res = encoder.generate_embedding_from_landmarks(
        img_bgr,
        res.get("primary_landmarks"),
    )
    assert emb_res["embedding_generated"] is True
    assert emb_res["embedding_dimensions"] == 512
    assert len(emb_res["embedding"]) == 512
    assert pytest.approx(emb_res["norm"], 0.01) == 1.0


def test_arcface_encoder_status_reports_cleanly():
    encoder = FaceEncoder(embedding_dim=512)
    assert isinstance(encoder.model_name, str)
    assert isinstance(encoder.is_arcface_model(), bool)


def test_face_no_detection():
    detector = FaceDetector()
    # Blank solid image
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    res = detector.detect_faces(blank)
    assert res["face_detected"] is False
    assert res["faces_found"] == 0
    assert "No" in res["error"] and "face detected" in res["error"]


def test_face_cosine_similarity():
    matcher = FaceMatcher()
    vec1 = [0.5, 0.5, 0.5, 0.5]
    vec2 = [0.5, 0.5, 0.5, 0.5]
    vec_diff = [-0.5, 0.5, -0.5, 0.5]

    # Identical vector similarity should be 1.0
    sim_identical = matcher.cosine_similarity(vec1, vec2)
    assert pytest.approx(sim_identical, 0.001) == 1.0

    eval_strong = matcher.evaluate_match(0.94)
    assert eval_strong["category"] == "STRONG_MATCH"
    assert eval_strong["is_match"] is True

    eval_possible = matcher.evaluate_match(0.85)
    assert eval_possible["category"] == "POSSIBLE_MATCH"

    eval_reject = matcher.evaluate_match(0.65)
    assert eval_reject["category"] == "REJECT"
    assert eval_reject["is_match"] is False
