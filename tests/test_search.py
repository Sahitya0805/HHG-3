"""Tests for evidence-based reverse-search candidate processing."""

from pathlib import Path

from backend.face.detector import FaceDetector
from backend.face.encoder import FaceEncoder
from backend.search.reverse_search import ReverseSearchOrchestrator
from backend.search.result_parser import ResultParser


def test_result_parser_scores_downloaded_candidate_image(monkeypatch):
    sample_bytes = Path("samples/demo_face.jpg").read_bytes()
    detector = FaceDetector()
    encoder = FaceEncoder()
    img = detector.load_image(sample_bytes)
    face = detector.detect_faces(img)
    input_embedding = encoder.generate_embedding_from_landmarks(
        img,
        face.get("primary_landmarks"),
    )["embedding"]

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


def test_result_parser_extracts_public_page_images(monkeypatch):
    parser = ResultParser()
    html = """
    <html><head>
      <meta property="og:image" content="/og.jpg">
      <meta name="twitter:image" content="https://cdn.example.com/twitter.jpg">
      <script type="application/ld+json">
        {"@type":"VideoObject","thumbnailUrl":"https://cdn.example.com/video.jpg","image":["/jsonld.jpg"]}
      </script>
    </head><body>
      <video poster="/poster.jpg"></video>
      <img src="/avatar.jpg">
    </body></html>
    """

    class FakeResponse:
        text = html

        def raise_for_status(self):
            return None

    monkeypatch.setattr("backend.search.result_parser.requests.get", lambda *args, **kwargs: FakeResponse())

    images = parser.extract_page_images("https://example.com/profile")

    assert "https://example.com/og.jpg" in images
    assert "https://cdn.example.com/twitter.jpg" in images
    assert "https://cdn.example.com/video.jpg" in images
    assert "https://example.com/jsonld.jpg" in images
    assert "https://example.com/poster.jpg" in images
    assert "https://example.com/avatar.jpg" in images


def test_result_parser_reports_rejected_candidates(monkeypatch):
    parser = ResultParser()
    monkeypatch.setattr(parser, "_download_image_bytes", lambda image_url: None)

    result = parser.process_candidates_with_rejections(
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
        strict_face_match=False,
    )

    assert result["verified_candidates"] == []
    assert result["rejected_candidates"][0]["reason"] == "blocked_or_unusable_image"


def test_strict_arcface_rejects_fallback_input():
    parser = ResultParser()

    result = parser.process_candidates_with_rejections(
        raw_results=[],
        input_embedding=[0.05] * 512,
        input_embedding_model="opencv-structural-fallback",
        strict_face_match=True,
    )

    assert result["verified_candidates"] == []
    assert result["rejected_candidates"][0]["reason"] == "arcface_required"


def test_orchestrator_runs_full_image_face_crop_and_hint_providers(monkeypatch):
    class FakeLens:
        def __init__(self):
            self.calls = []

        def search(self, image_bytes: bytes, filename: str = "query.jpg", search_query=None):
            self.calls.append(filename)
            return [
                {
                    "url": f"https://example.com/{filename}",
                    "title": "Lens Result",
                    "source": "Google Lens",
                    "image_url": f"https://example.com/{filename}.jpg",
                    "snippet": "",
                }
            ]

    class FakeWeb:
        def search(self, image_bytes: bytes, filename: str = "query.jpg", search_query=None, **kwargs):
            return [
                {
                    "url": "https://github.com/demo",
                    "title": "GitHub Profile",
                    "source": "GitHub",
                    "image_url": "https://example.com/avatar.jpg",
                    "snippet": "",
                }
            ]

    lens = FakeLens()
    orchestrator = ReverseSearchOrchestrator(provider=lens)
    orchestrator.web_provider = FakeWeb()
    monkeypatch.setattr(
        orchestrator.parser,
        "process_candidates_with_rejections",
        lambda **kwargs: {"verified_candidates": [], "rejected_candidates": []},
    )

    response = orchestrator.search_and_match(
        image_bytes=b"full-image",
        input_embedding=[0.1] * 512,
        input_crop_b64="ZmFjZS1jcm9w",
        search_hint="demo user",
        strict_face_match=False,
    )

    assert lens.calls == ["query.jpg", "face-crop.jpg"]
    assert response["total_candidates"] == 3
    assert any(item["provider"] == "SerpApiPublicWebProfilesVideos" for item in response["provider_results"])
