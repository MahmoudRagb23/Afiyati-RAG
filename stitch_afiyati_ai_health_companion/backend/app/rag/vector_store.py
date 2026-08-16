from __future__ import annotations

from pathlib import Path

from qdrant_client import QdrantClient, models


class LocalVectorStore:
    def __init__(self, path: Path, collection: str):
        self.path = path
        self.collection = collection
        self.client: QdrantClient | None = None
        self.error: str | None = None
        try:
            path.mkdir(parents=True, exist_ok=True)
            self.client = QdrantClient(path=str(path))
        except Exception as exc:
            self.error = str(exc)

    @property
    def available(self) -> bool:
        return self.client is not None

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
            self.client = None

    def count(self) -> int:
        if not self.client:
            return 0
        try:
            return int(self.client.count(self.collection, exact=True).count)
        except Exception:
            return 0

    def replace(self, chunks: list[dict], vectors: list[list[float]]) -> int:
        if not self.client:
            raise RuntimeError(self.error or "Qdrant local store unavailable")
        if len(chunks) != len(vectors) or not vectors:
            raise ValueError("Chunks and vectors must be non-empty and aligned")
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=models.VectorParams(size=len(vectors[0]), distance=models.Distance.COSINE),
        )
        points = [
            models.PointStruct(
                id=chunk["metadata"]["chunk_id"],
                vector=vector,
                payload={"text": chunk["text"], "parent_text": chunk.get("parent_text"), **chunk["metadata"]},
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        for start in range(0, len(points), 64):
            self.client.upsert(self.collection, points=points[start : start + 64], wait=True)
        return len(points)

    def search(self, vector: list[float], limit: int = 15, conditions: list[str] | None = None) -> list[dict]:
        if not self.client or not self.client.collection_exists(self.collection):
            return []
        query_filter = None
        if conditions:
            query_filter = models.Filter(
                must=[models.FieldCondition(key="condition", match=models.MatchAny(any=conditions))]
            )
        result = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=query_filter,
            with_payload=True,
            limit=limit,
        ).points
        return [
            {
                "text": point.payload.get("text", ""),
                "parent_text": point.payload.get("parent_text"),
                "metadata": {key: value for key, value in point.payload.items() if key not in {"text", "parent_text"}},
                "score": float(point.score),
            }
            for point in result
        ]
