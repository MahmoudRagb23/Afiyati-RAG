from __future__ import annotations

import re

from app.rag.bm25 import lexical_tokens


ARABIC_PATTERN = re.compile(r"[\u0600-\u06ff]")


def citation_from_chunk(chunk: dict) -> dict:
    metadata = chunk["metadata"]
    return {
        "document": metadata.get("guideline_title") or metadata.get("source_filename", "Unknown guideline"),
        "organization": metadata.get("organization", "Unknown"),
        "section": metadata.get("section_title"),
        "page": metadata.get("page_number"),
        "chunk_id": metadata["chunk_id"],
        "source_url": metadata.get("source_url"),
    }


def validate_citations(citations: list[dict], retrieved: list[dict]) -> dict:
    retrieved_by_id = {item["metadata"]["chunk_id"]: item for item in retrieved}
    details: list[dict] = []
    valid = 0
    for citation in citations:
        chunk = retrieved_by_id.get(citation.get("chunk_id"))
        checks = {
            "citation_exists": bool(citation.get("chunk_id")),
            "chunk_exists": chunk is not None,
            "page_exists": bool(chunk and chunk["metadata"].get("page_number")),
            "chunk_was_retrieved": chunk is not None,
            "source_matches": bool(
                chunk
                and citation.get("document")
                in {
                    chunk["metadata"].get("guideline_title"),
                    chunk["metadata"].get("source_filename"),
                }
            ),
        }
        passed = all(checks.values())
        valid += int(passed)
        details.append({"chunk_id": citation.get("chunk_id"), "valid": passed, "checks": checks})
    return {"valid": valid, "total": len(citations), "details": details}


def verify_claims(answer: dict, evidence: list[dict]) -> list[dict]:
    claims = [answer.get("summary", "")]
    claims.extend(item.get("assessment", "") for item in answer.get("conditions_considered", []))
    evidence_terms = [set(lexical_tokens(item["text"])) for item in evidence]
    results: list[dict] = []
    stop = {"the", "and", "for", "with", "this", "that", "من", "في", "على", "إلى", "هذا", "هذه", "قد"}
    for claim in [value for value in claims if value.strip()]:
        claim_is_arabic = bool(ARABIC_PATTERN.search(claim))
        evidence_has_arabic = any(ARABIC_PATTERN.search(item["text"]) for item in evidence)
        if claim_is_arabic and not evidence_has_arabic:
            results.append(
                {
                    "claim": claim,
                    "status": "NOT_EVALUATED_CROSS_LANGUAGE",
                    "lexical_support": None,
                }
            )
            continue
        terms = set(lexical_tokens(claim)) - stop
        best = max((len(terms & source) / max(1, len(terms)) for source in evidence_terms), default=0.0)
        if best >= 0.18:
            label = "SUPPORTED"
        elif best >= 0.08:
            label = "PARTIALLY_SUPPORTED"
        else:
            label = "UNSUPPORTED"
        results.append({"claim": claim, "status": label, "lexical_support": round(best, 3)})
    return results
