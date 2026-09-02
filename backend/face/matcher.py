"""Face matching and cosine similarity computation."""

import numpy as np
from typing import List, Dict, Any, Tuple


class FaceMatcher:
    """Computes similarity metrics and match verification classifications."""

    STRONG_MATCH_THRESHOLD = 0.90
    POSSIBLE_MATCH_THRESHOLD = 0.80

    @staticmethod
    def cosine_similarity(embedding_a: List[float], embedding_b: List[float]) -> float:
        """
        Calculates cosine similarity between two face embeddings.
        Returns value in range [0.0, 1.0].
        """
        a = np.array(embedding_a, dtype=np.float32)
        b = np.array(embedding_b, dtype=np.float32)

        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        dot = np.dot(a, b)
        cosine = dot / (norm_a * norm_b)
        # Bound between 0.0 and 1.0
        similarity = max(0.0, min(1.0, float(cosine)))
        return round(similarity, 4)

    @classmethod
    def evaluate_match(cls, similarity: float) -> Dict[str, Any]:
        """
        Classifies similarity score against demonstration thresholds:
        >= 0.90 -> Strong Match
        0.80 - 0.89 -> Possible Match
        < 0.80 -> Reject
        """
        if similarity >= cls.STRONG_MATCH_THRESHOLD:
            category = "STRONG_MATCH"
            label = "Strong Match"
            is_match = True
            color = "green"
        elif similarity >= cls.POSSIBLE_MATCH_THRESHOLD:
            category = "POSSIBLE_MATCH"
            label = "Possible Match"
            is_match = True
            color = "amber"
        else:
            category = "REJECT"
            label = "Low Similarity / No Match"
            is_match = False
            color = "red"

        return {
            "similarity": similarity,
            "similarity_percent": round(similarity * 100.0, 2),
            "category": category,
            "label": label,
            "is_match": is_match,
            "color": color,
            "thresholds": {
                "strong_match": cls.STRONG_MATCH_THRESHOLD,
                "possible_match": cls.POSSIBLE_MATCH_THRESHOLD,
            },
        }
