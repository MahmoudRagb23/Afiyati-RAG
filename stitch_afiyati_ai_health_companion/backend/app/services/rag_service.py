from __future__ import annotations

import json
import time
import uuid
from collections import OrderedDict

from pydantic import ValidationError

from app.core.config import Settings
from app.core.safety import (
    classify_safety,
    emergency_response,
    insufficient_evidence_response,
)
from app.rag.bm25 import BM25Index
from app.rag.hybrid_search import HybridRetriever, rerank
from app.rag.query_analysis import analyze_query, rewrite_queries
from app.rag.vector_store import LocalVectorStore
from app.schemas.api import AfiyatiAnswer
from app.services.citation_service import citation_from_chunk, validate_citations, verify_claims
from app.services.contradiction_service import detect_guideline_differences
from app.services.ollama_service import OllamaError, OllamaService


GENERATION_SCHEMA = {
    "type": "object",
    "required": [
        "summary",
        "recommendation_status",
        "conditions_considered",
        "warnings",
        "evidence_strength",
        "needs_professional_attention",
        "emergency",
        "cited_chunk_ids",
    ],
    "properties": {
        "summary": {"type": "string"},
        "recommendation_status": {
            "type": "string",
            "enum": ["suitable", "caution", "not_recommended", "insufficient_evidence"],
        },
        "conditions_considered": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["condition", "assessment"],
                "properties": {"condition": {"type": "string"}, "assessment": {"type": "string"}},
            },
        },
        "suggested_quantity": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "required": ["value", "basis", "certainty"],
                    "properties": {
                        "value": {"type": "string"},
                        "basis": {"type": "string"},
                        "certainty": {"type": "string"},
                    },
                },
            ]
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
        "evidence_strength": {"type": "string", "enum": ["strong", "moderate", "limited", "insufficient"]},
        "needs_professional_attention": {"type": "boolean"},
        "emergency": {"type": "boolean"},
        "cited_chunk_ids": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
        },
    },
}


class RAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ollama = OllamaService(settings)
        self.vectors = LocalVectorStore(settings.qdrant_path, settings.qdrant_collection)
        self.bm25 = BM25Index(settings.data_dir / "index" / "chunks.json")
        self.retriever = HybridRetriever(self.vectors, self.bm25, self.ollama)
        self.traces: OrderedDict[str, dict] = OrderedDict()

    def status(self) -> dict:
        return {
            "collection": self.settings.qdrant_collection,
            "vector_store_available": self.vectors.available,
            "vector_store_error": self.vectors.error,
            "indexed_chunks": self.vectors.count(),
            "bm25_chunks": len(self.bm25.chunks),
            "generation_model": self.settings.generation_model,
            "embedding_model": self.settings.embedding_model,
            "chunk_strategy": "section-aware + parent-child",
            "child_tokens": self.settings.child_tokens,
            "parent_tokens": self.settings.parent_tokens,
            "overlap": self.settings.chunk_overlap,
            "top_k": self.settings.top_k,
        }

    def _remember_trace(self, trace: dict) -> str:
        trace_id = str(uuid.uuid4())
        self.traces[trace_id] = trace
        while len(self.traces) > 100:
            self.traces.popitem(last=False)
        return trace_id

    def get_trace(self, trace_id: str) -> dict | None:
        return self.traces.get(trace_id)

    async def answer(self, question: str, conditions: list[str], mode: str = "chat") -> tuple[dict, dict]:
        total_started = time.perf_counter()
        safety = classify_safety(question)
        if safety.emergency:
            answer = emergency_response()
            trace = {
                "original_query": question,
                "safety": {
                    "classification": safety.classification,
                    "matched_rules": safety.matched_rules,
                    "emergency": safety.emergency,
                },
                "claims": [],
                "latency": {},
            }
            answer["trace_id"] = self._remember_trace(trace)
            return answer, trace
        if safety.classification == "OUT_OF_SCOPE":
            answer = insufficient_evidence_response(conditions)
            answer["safety_classification"] = "OUT_OF_SCOPE"
            trace = {
                "original_query": question,
                "safety": {
                    "classification": safety.classification,
                    "matched_rules": safety.matched_rules,
                    "emergency": safety.emergency,
                },
                "claims": [],
                "latency": {},
            }
            answer["trace_id"] = self._remember_trace(trace)
            return answer, trace

        analysis = analyze_query(question, conditions, mode)
        rewritten = rewrite_queries(question, analysis)
        candidates, retrieval_metrics = await self.retriever.retrieve(
            rewritten, analysis["conditions"], candidate_k=15, strategy="hybrid"
        )
        selected, rerank_latency = rerank(" ".join(rewritten), candidates, self.settings.top_k)
        guideline_differences = detect_guideline_differences(selected)
        if not selected:
            answer = insufficient_evidence_response(analysis["conditions"])
            answer["safety_classification"] = safety.classification
            trace = {
                "original_query": question,
                "rewritten_queries": rewritten,
                "analysis": analysis,
                "retrieval": retrieval_metrics,
                "retrieved_chunks": [],
                "reranked_chunks": [],
                "claims": [],
                "citation_validation": {"valid": 0, "total": 0, "details": []},
                "latency": {"end_to_end_ms": round((time.perf_counter() - total_started) * 1000, 2)},
            }
            answer["trace_id"] = self._remember_trace(trace)
            return answer, trace

        evidence_text = "\n\n".join(
            f"CHUNK {item['metadata']['chunk_id']}\n"
            f"SOURCE: {item['metadata'].get('guideline_title')} | {item['metadata'].get('organization')} | "
            f"PAGE {item['metadata'].get('page_number')} | SECTION {item['metadata'].get('section_title')}\n"
            f"{item.get('parent_text') or item['text']}"
            for item in selected
        )
        prompt = f"""You are Afiyati, an evidence-grounded chronic-disease lifestyle assistant.
Answer in the same language as the question. Use only the evidence below. Consider every registered condition.
Do not diagnose, change doses, suggest stopping prescribed medicine, or invent quantities. If evidence is not
enough for a safe recommendation, set recommendation_status to insufficient_evidence. Preserve uncertainty.
Never invent a source, page, guideline, or URL. Return only JSON matching the supplied schema.
If the evidence contains a potential guideline difference, describe each source separately and do not invent consensus.
For every factual recommendation, include only the supporting CHUNK identifiers in cited_chunk_ids.
Use no more than 3 identifiers and do not cite background or irrelevant chunks.

REGISTERED CONDITIONS: {json.dumps(analysis['conditions'], ensure_ascii=False)}
POTENTIAL GUIDELINE DIFFERENCES: {json.dumps(guideline_differences, ensure_ascii=False)}
QUESTION: {question}
EVIDENCE:
{evidence_text}
"""
        generation_latency = 0.0
        generation_error = None
        try:
            raw_answer, generation_latency = await self.ollama.generate_json(prompt, GENERATION_SCHEMA)
            selected_by_id = {item["metadata"]["chunk_id"]: item for item in selected}
            requested_ids = list(dict.fromkeys(raw_answer.pop("cited_chunk_ids", [])))
            cited_chunks = [selected_by_id[value] for value in requested_ids if value in selected_by_id]
            if raw_answer.get("recommendation_status") != "insufficient_evidence" and not cited_chunks:
                raise ValueError("Generated recommendation did not include a valid evidence citation")
            raw_answer["citations"] = [citation_from_chunk(item) for item in cited_chunks]
            raw_answer["safety_classification"] = safety.classification
            raw_answer["evidence"] = [
                {
                    "rank": index,
                    "document": item["metadata"].get("guideline_title"),
                    "organization": item["metadata"].get("organization"),
                    "section": item["metadata"].get("section_title"),
                    "page": item["metadata"].get("page_number"),
                    "chunk_id": item["metadata"]["chunk_id"],
                    "relevance": item.get("rerank_score"),
                    "excerpt": item["text"][:500],
                }
                for index, item in enumerate(selected, start=1)
            ]
            answer = AfiyatiAnswer.model_validate(raw_answer).model_dump()
        except (OllamaError, ValidationError, ValueError) as exc:
            generation_error = str(exc)
            answer = insufficient_evidence_response(analysis["conditions"])
            answer["warnings"].append("تعذر تشغيل نموذج الإجابة المحلي بأمان. حاول مرة أخرى بعد التحقق من Ollama.")

        claims = verify_claims(answer, selected) if answer.get("citations") else []
        evaluable_claims = [
            item for item in claims if item["status"] != "NOT_EVALUATED_CROSS_LANGUAGE"
        ]
        if evaluable_claims and sum(
            item["status"] == "UNSUPPORTED" for item in evaluable_claims
        ) > len(evaluable_claims) / 2:
            safe_answer = insufficient_evidence_response(analysis["conditions"])
            safe_answer["warnings"].append("تم حجب إجابة لأن التحقق الآلي لم يجد دعماً كافياً لادعاءاتها.")
            answer = safe_answer
            claims = verify_claims(answer, selected)
        evaluable_claims = [
            item for item in claims if item["status"] != "NOT_EVALUATED_CROSS_LANGUAGE"
        ]
        citation_validation = validate_citations(answer.get("citations", []), selected)
        trace = {
            "original_query": question,
            "rewritten_queries": rewritten,
            "analysis": analysis,
            "safety": {"classification": safety.classification, "matched_rules": safety.matched_rules},
            "retrieval": retrieval_metrics,
            "retrieved_chunks": candidates,
            "reranked_chunks": selected,
            "generation_evidence": [item["metadata"]["chunk_id"] for item in selected],
            "claims": claims,
            "citation_validation": citation_validation,
            "potential_guideline_differences": guideline_differences,
            "citation_coverage": {
                "supported": sum(item["status"] == "SUPPORTED" for item in claims),
                "total": len(evaluable_claims),
                "not_evaluated_cross_language": len(claims) - len(evaluable_claims),
            },
            "generation_error": generation_error,
            "latency": {
                **retrieval_metrics,
                "reranking_latency_ms": round(rerank_latency, 2),
                "generation_latency_ms": round(generation_latency, 2),
                "end_to_end_ms": round((time.perf_counter() - total_started) * 1000, 2),
            },
        }
        trace_id = self._remember_trace(trace)
        answer["trace_id"] = trace_id
        return answer, trace
