from __future__ import annotations

import json
import re
from pathlib import Path

from rank_bm25 import BM25Okapi


def lexical_tokens(text: str) -> list[str]:
    normalized = text.lower().replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    return re.findall(r"[a-z0-9]+|[\u0600-\u06ff]+", normalized)


def _matches_condition(metadata_condition: str | list[str] | None, requested: list[str]) -> bool:
    """Support canonical single-condition metadata and legacy list metadata."""
    available = (
        {metadata_condition}
        if isinstance(metadata_condition, str)
        else set(metadata_condition or [])
    )
    return bool(available.intersection(requested))


class BM25Index:
    def __init__(self, index_path: Path):
        self.index_path = index_path
        self.chunks: list[dict] = []
        self.tokenized: list[list[str]] = []
        self.model: BM25Okapi | None = None
        self.reload()

    def reload(self) -> None:
        try:
            self.chunks = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            self.chunks = []
        self.tokenized = [lexical_tokens(chunk["text"]) for chunk in self.chunks]
        self.model = BM25Okapi(self.tokenized) if self.tokenized else None

    def save(self, chunks: list[dict]) -> None:
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
        self.reload()

    def search(self, query: str, limit: int = 15, conditions: list[str] | None = None) -> list[dict]:
        if not self.model:
            return []
        query_tokens = lexical_tokens(query)
        scores = self.model.get_scores(query_tokens)
        query_set = set(query_tokens)
        adjusted = [float(score) + 0.001 * len(query_set & set(self.tokenized[index])) for index, score in enumerate(scores)]
        ranked = sorted(range(len(adjusted)), key=lambda index: adjusted[index], reverse=True)
        results: list[dict] = []
        for index in ranked:
            chunk = self.chunks[index]
            if conditions and not _matches_condition(chunk["metadata"].get("condition"), conditions):
                continue
            if not query_set.intersection(self.tokenized[index]):
                continue
            results.append({**chunk, "score": adjusted[index]})
            if len(results) >= limit:
                break
        return results
