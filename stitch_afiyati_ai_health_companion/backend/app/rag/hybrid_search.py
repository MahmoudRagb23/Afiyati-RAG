from __future__ import annotations

import time

from app.core.conditions import SUPPORTED_CONDITIONS, supported_conditions
from app.rag.bm25 import BM25Index, lexical_tokens
from app.rag.vector_store import LocalVectorStore
from app.services.ollama_service import OllamaError, OllamaService


class HybridRetriever:
    def __init__(self, vectors: LocalVectorStore, bm25: BM25Index, ollama: OllamaService):
        self.vectors = vectors
        self.bm25 = bm25
        self.ollama = ollama

    async def retrieve(
        self,
        queries: list[str],
        conditions: list[str],
        candidate_k: int = 15,
        strategy: str = "hybrid",
        embedding_keep_alive: str | int = 0,
    ) -> tuple[list[dict], dict]:
        started = time.perf_counter()
        fused: dict[str, dict] = {}
        dense_latency = 0.0
        dense_error = None
        search_conditions = supported_conditions(conditions) or list(SUPPORTED_CONDITIONS)
        dense_results: list[list[dict]] = [[] for _ in queries]
        if strategy in {"dense", "hybrid"} and self.vectors.count():
            try:
                vectors, dense_latency = await self.ollama.embed(
                    queries, keep_alive=embedding_keep_alive
                )
                dense_results = [
                    self.vectors.search(vector, candidate_k, search_conditions) for vector in vectors
                ]
            except (OllamaError, RuntimeError) as exc:
                dense_error = str(exc)
        for query_index, query in enumerate(queries):
            dense = dense_results[query_index]
            lexical = self.bm25.search(query, candidate_k, search_conditions) if strategy in {"bm25", "hybrid"} else []
            for method, results in (("dense", dense), ("bm25", lexical)):
                for rank, result in enumerate(results, start=1):
                    chunk_id = result["metadata"]["chunk_id"]
                    entry = fused.setdefault(chunk_id, {**result, "rrf_score": 0.0, "methods": set()})
                    entry["rrf_score"] += 1.0 / (60 + rank)
                    entry["methods"].add(method)
        ranked = sorted(fused.values(), key=lambda item: item["rrf_score"], reverse=True)
        for item in ranked:
            item["methods"] = sorted(item["methods"])
            item["score"] = item.pop("rrf_score")
        return ranked[:candidate_k], {
            "method": strategy,
            "dense_latency_ms": round(dense_latency, 2),
            "retrieval_latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "dense_error": dense_error,
        }


def rerank(query: str, candidates: list[dict], limit: int = 5) -> tuple[list[dict], float]:
    started = time.perf_counter()
    query_terms = set(lexical_tokens(query))
    for candidate in candidates:
        terms = set(lexical_tokens(candidate["text"]))
        overlap = len(query_terms & terms) / max(1, len(query_terms))
        candidate["rerank_score"] = round(candidate["score"] + 0.025 * overlap, 6)
    ranked = sorted(candidates, key=lambda item: item["rerank_score"], reverse=True)[:limit]
    return ranked, (time.perf_counter() - started) * 1000
