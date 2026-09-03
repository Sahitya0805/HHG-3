"""Tests for evidence-based reverse-search candidate processing."""

from pathlib import Path

from backend.face.detector import FaceDetector
from backend.face.encoder import FaceEncoder
from backend.search.result_parser import ResultParser


def test_result_parser_scores_downloaded_candidate_image(monkeypatch):
    sample_bytes = Path("samples/demo_face.jpg").read_bytes()
    detector = FaceDetector()
    encoder = FaceEncoder()
    img = detector.load_image(sample_bytes)
    face = detector.detect_faces(img)
    input_embedding = encoder.generate_embedding(face["primary_face_crop"])["embedding"]

    parser = ResultParser()
    monkeypatch.setattr(parser, "_download_image_bytes", lambda image_url: sample_bytes)

    candidates = parser.process_candidates(
        raw_results=[
            {
                "url": "https://instagram.com/p/public-event-99",
                "title": "Hackathon Demo Post",
                "source": "Instagram",
                "image_url": "https://example.com/demo_face.jpg",
                "snippet": "Testing blockchain immutability",
            }
        ],
        input_embedding=input_embedding,
        input_crop_b64=face["primary_crop_b64"],
    )

    assert len(candidates) == 1
    assert candidates[0]["similarity"] > 0.99
    assert candidates[0]["is_match"] is True
    assert candidates[0]["match_evidence"] == "cosine_similarity_of_face_embeddings"
    assert candidates[0]["image_url"] == "https://example.com/demo_face.jpg"


def test_result_parser_rejects_candidate_without_downloadable_image(monkeypatch):
    parser = ResultParser()
    monkeypatch.setattr(parser, "_download_image_bytes", lambda image_url: None)

    candidates = parser.process_candidates(
        raw_results=[
            {
                "url": "https://example.com/no-image",
                "title": "No Image",
                "source": "Web",
                "image_url": "https://example.com/missing.jpg",
                "snippet": "",
            }
        ],
        input_embedding=[0.05] * 512,
    )

    assert candidates == []
