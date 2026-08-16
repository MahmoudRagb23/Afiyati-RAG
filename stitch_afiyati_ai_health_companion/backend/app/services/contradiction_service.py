from __future__ import annotations

from itertools import combinations

from app.rag.bm25 import lexical_tokens


POSITIVE = {"recommend", "recommended", "should", "advise", "consider", "ينصح", "يوصى"}
NEGATIVE = {"avoid", "not", "contraindicated", "shouldn't", "لا", "تجنب", "غير"}


def detect_guideline_differences(chunks: list[dict]) -> list[dict]:
    """Flag possible differences for display; never infer which source is correct."""
    differences: list[dict] = []
    for left, right in combinations(chunks, 2):
        left_meta = left["metadata"]
        right_meta = right["metadata"]
        if left_meta.get("organization") == right_meta.get("organization"):
            continue
        left_terms = set(lexical_tokens(left["text"]))
        right_terms = set(lexical_tokens(right["text"]))
        shared = left_terms & right_terms
        if len(shared) < 4:
            continue
        left_positive = bool(left_terms & POSITIVE)
        right_positive = bool(right_terms & POSITIVE)
        left_negative = bool(left_terms & NEGATIVE)
        right_negative = bool(right_terms & NEGATIVE)
        if (left_positive and right_negative) or (right_positive and left_negative):
            differences.append(
                {
                    "label": "Potential Guideline Difference",
                    "source_a": left_meta.get("guideline_title"),
                    "source_b": right_meta.get("guideline_title"),
                    "chunk_a": left_meta.get("chunk_id"),
                    "chunk_b": right_meta.get("chunk_id"),
                    "shared_terms": sorted(shared)[:12],
                }
            )
    return differences

