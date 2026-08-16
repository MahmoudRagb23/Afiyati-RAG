from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.safety import classify_safety
from app.rag.bm25 import BM25Index
from app.rag.chunker import section_aware_chunks
from app.rag.hybrid_search import HybridRetriever
from app.rag.query_analysis import analyze_query, rewrite_queries
from app.rag.validate_guidelines import validate
from app.rag.vector_store import LocalVectorStore
from app.services.citation_service import citation_from_chunk, validate_citations, verify_claims
from app.services.contradiction_service import detect_guideline_differences
from app.services.ollama_service import OllamaService


def sample_chunk(chunk_id: str, text: str, condition: str = "hypertension") -> dict:
    return {
        "text": text,
        "parent_text": text,
        "metadata": {
            "chunk_id": chunk_id,
            "parent_id": "parent-1",
            "condition": condition,
            "organization": "nice",
            "guideline_id": "NG136",
            "guideline_title": "Hypertension in adults",
            "publication_year": 2023,
            "guideline_version": "2023",
            "language": "en",
            "section_title": "Lifestyle",
            "subsection_title": None,
            "page_number": 27,
            "source_filename": "ng136.pdf",
            "source_url": "https://example.test/ng136",
        },
    }


def test_section_aware_parent_child_metadata():
    pages = [{"page_number": 7, "text": "1.1 Lifestyle recommendations\nReduce dietary sodium where appropriate.\nDiscuss physical activity."}]
    chunks = section_aware_chunks(
        pages,
        {"condition": "hypertension", "organization": "nice", "guideline_id": "NG136", "title": "Hypertension", "source_filename": "ng136.pdf"},
        child_tokens=10,
        parent_tokens=20,
        overlap=2,
    )
    assert chunks
    metadata = chunks[0]["metadata"]
    assert metadata["page_number"] == 7
    assert metadata["section_title"] == "1.1 Lifestyle recommendations"
    assert metadata["parent_id"]
    assert metadata["chunk_id"]


def test_chunks_never_cross_pdf_page_boundaries():
    pages = [
        {"page_number": 4, "text": "1.2 Lifestyle\nReduce sodium where appropriate."},
        {"page_number": 5, "text": "Continue individualized dietary counseling."},
    ]
    chunks = section_aware_chunks(
        pages,
        {
            "condition": "hypertension",
            "organization": "nice",
            "guideline_id": "NG136",
            "title": "Hypertension",
            "source_filename": "ng136.pdf",
        },
        child_tokens=50,
        parent_tokens=80,
        overlap=5,
    )
    assert {item["metadata"]["page_number"] for item in chunks} == {4, 5}
    assert all("Reduce sodium" not in item["text"] for item in chunks if item["metadata"]["page_number"] == 5)


def test_bilingual_query_rewrite_adds_retrieval_vocabulary():
    analysis = analyze_query("ما كمية البوتاسيوم الآمنة لي؟", ["chronic_kidney_disease"])
    rewritten = rewrite_queries("ما كمية البوتاسيوم الآمنة لي؟", analysis)
    assert analysis["topic"] == "potassium"
    assert any("dietary potassium" in value for value in rewritten)


def test_bm25_exact_term_and_hybrid_fallback(tmp_path: Path):
    index = BM25Index(tmp_path / "chunks.json")
    chunks = [
        sample_chunk("11111111-1111-4111-8111-111111111111", "HbA1c target and metformin guidance", "type_2_diabetes"),
        sample_chunk("22222222-2222-4222-8222-222222222222", "dietary sodium and blood pressure"),
    ]
    index.save(chunks)
    result = index.search("HbA1c", limit=2)
    assert result[0]["metadata"]["condition"] == "type_2_diabetes"

    class EmptyVectors:
        def count(self): return 0

    retriever = HybridRetriever(EmptyVectors(), index, object())
    hybrid, timings = asyncio.run(retriever.retrieve(["HbA1c"], [], strategy="hybrid"))
    assert hybrid[0]["metadata"]["chunk_id"] == chunks[0]["metadata"]["chunk_id"]
    assert hybrid[0]["methods"] == ["bm25"]
    assert timings["method"] == "hybrid"


def test_dense_rewrites_are_embedded_in_one_batch():
    first = sample_chunk("11111111-1111-4111-8111-111111111111", "sodium blood pressure")
    second = sample_chunk("22222222-2222-4222-8222-222222222222", "coffee caffeine")

    class StubVectors:
        def count(self):
            return 2

        def search(self, vector, limit, conditions):
            return [{**(first if vector[0] == 1.0 else second), "score": 0.9}]

    class StubOllama:
        calls = 0

        async def embed(self, texts, keep_alive=0):
            self.calls += 1
            assert texts == ["sodium", "coffee"]
            assert keep_alive == "2m"
            return [[1.0, 0.0], [0.0, 1.0]], 12.0

    ollama = StubOllama()
    retriever = HybridRetriever(StubVectors(), BM25Index(Path("missing.json")), ollama)
    results, timings = asyncio.run(
        retriever.retrieve(
            ["sodium", "coffee"], [], strategy="dense", embedding_keep_alive="2m"
        )
    )
    assert ollama.calls == 1
    assert len(results) == 2
    assert timings["dense_latency_ms"] == 12.0


def test_qdrant_local_storage_and_dense_search(tmp_path: Path):
    store = LocalVectorStore(tmp_path / "qdrant", "test_collection")
    chunks = [
        sample_chunk("11111111-1111-4111-8111-111111111111", "sodium blood pressure"),
        sample_chunk("22222222-2222-4222-8222-222222222222", "asthma inhaler", "asthma"),
    ]
    assert store.replace(chunks, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]) == 2
    results = store.search([0.9, 0.1, 0.0], limit=1)
    assert results[0]["metadata"]["chunk_id"] == chunks[0]["metadata"]["chunk_id"]
    store.close()


def test_citation_metadata_comes_from_retrieved_chunk():
    chunk = sample_chunk("11111111-1111-4111-8111-111111111111", "dietary sodium recommendation")
    citation = citation_from_chunk(chunk)
    assert citation["page"] == 27
    assert citation["document"] == "Hypertension in adults"
    validation = validate_citations([citation], [chunk])
    assert validation["valid"] == 1
    assert validation["total"] == 1


def test_cross_language_claim_is_not_falsely_marked_unsupported():
    evidence = [sample_chunk("11111111-1111-4111-8111-111111111111", "Regular physical activity is encouraged.")]
    claims = verify_claims(
        {"summary": "يُنصح بالنشاط البدني المنتظم.", "conditions_considered": []},
        evidence,
    )
    assert claims[0]["status"] == "NOT_EVALUATED_CROSS_LANGUAGE"
    assert claims[0]["lexical_support"] is None


def test_potential_guideline_difference_is_flagged_without_merging_consensus():
    left = sample_chunk(
        "11111111-1111-4111-8111-111111111111",
        "The guideline recommended adults consider reducing sodium intake for blood pressure management.",
    )
    right = sample_chunk(
        "22222222-2222-4222-8222-222222222222",
        "Adults should not avoid sodium without individual assessment for blood pressure management.",
    )
    right["metadata"]["organization"] = "who"
    right["metadata"]["guideline_title"] = "WHO guideline"
    differences = detect_guideline_differences([left, right])
    assert differences[0]["label"] == "Potential Guideline Difference"
    assert differences[0]["source_a"] != differences[0]["source_b"]


def test_guideline_validator_accepts_empty_library(tmp_path: Path):
    root = tmp_path / "guidelines"
    root.mkdir()
    (root / "manifest.json").write_text("[]", encoding="utf-8")
    report = validate(root)
    assert report["valid"] is True
    assert report["pdfs_found"] == 0


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("عندي ألم شديد في الصدر وضيق في التنفس", "POSSIBLE_EMERGENCY"),
        ("Should I stop my medication?", "CAUTION"),
        ("Should I stop metformin because I feel tired?", "CAUTION"),
        ("أزيد جرعة دواء الضغط لحد كام؟", "CAUTION"),
        ("I suddenly cannot speak clearly and one side is weak.", "POSSIBLE_EMERGENCY"),
        ("Give me legal advice", "OUT_OF_SCOPE"),
        ("هل الأرز مناسب؟", "ALLOWED"),
    ],
)
def test_safety_rules(question: str, expected: str):
    assert classify_safety(question).classification == expected


@pytest.mark.integration
def test_ollama_models_are_reachable():
    settings = Settings.from_env()
    models = asyncio.run(OllamaService(settings).models())
    normalized = {name.removesuffix(":latest") for name in models}
    assert "qwen3:8b" in normalized
    assert "qwen3-embedding:0.6b" in normalized
    assert "bge-m3" in normalized
    assert "nomic-embed-text" in normalized
