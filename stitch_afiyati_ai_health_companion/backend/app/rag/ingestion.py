from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from app.core.config import Settings
from app.rag.bm25 import BM25Index
from app.rag.chunker import section_aware_chunks
from app.rag.parser import PdfParsingError, parse_pdf
from app.rag.validate_guidelines import print_report, validate
from app.rag.vector_store import LocalVectorStore
from app.services.ollama_service import OllamaService


def _embedding_cache_key(model: str, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"{model}:{digest}"


def _load_embedding_cache(path: Path, model: str) -> dict[str, list[float]]:
    cached: dict[str, list[float]] = {}
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                try:
                    item = json.loads(line)
                    if item.get("model") == model and isinstance(item.get("vector"), list):
                        cached[item["key"]] = item["vector"]
                except (json.JSONDecodeError, KeyError):
                    continue
    except FileNotFoundError:
        pass
    return cached


async def ingest(settings: Settings, guidelines_path: Path | None = None) -> dict:
    root = (guidelines_path or settings.data_dir / "guidelines").resolve()
    report = validate(root)
    print_report(report)
    if not report["valid"]:
        raise RuntimeError("Guideline validation failed; no files were ingested")
    manifest_path = root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    if not manifest:
        return {"documents": 0, "chunks": 0, "message": "No manifest entries to ingest"}

    chunks: list[dict] = []
    parsed_documents = 0
    for item in manifest:
        if item.get("status", "current") != "current":
            continue
        path = root / item["file"]
        try:
            pages = parse_pdf(path)
        except PdfParsingError as exc:
            raise RuntimeError(str(exc)) from exc
        metadata = {**item, "source_filename": path.name}
        chunks.extend(
            section_aware_chunks(
                pages,
                metadata,
                child_tokens=settings.child_tokens,
                parent_tokens=settings.parent_tokens,
                overlap=settings.chunk_overlap,
            )
        )
        parsed_documents += 1
    if not chunks:
        return {"documents": parsed_documents, "chunks": 0, "message": "No extractable chunks"}

    # Build the lexical index first so the application retains a safe local
    # fallback even when Ollama or the embedding model is temporarily offline.
    BM25Index(settings.data_dir / "index" / "chunks.json").save(chunks)
    # Acquire the local Qdrant lock before expensive embedding work. This fails
    # fast with a clear message if a running backend still owns the store.
    store = LocalVectorStore(settings.qdrant_path, settings.qdrant_collection)
    if not store.available:
        raise RuntimeError(
            f"Vector store is unavailable before embedding: {store.error}. "
            "Stop the local backend and retry ingestion."
        )
    ollama = OllamaService(settings)
    vectors: list[list[float]] = []
    embedding_latency = 0.0
    cache_path = settings.data_dir / "index" / "embedding_cache.jsonl"
    cached_vectors = _load_embedding_cache(cache_path, settings.embedding_model)
    cache_hits = 0
    batch_size = max(1, settings.embedding_batch_size)
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    try:
        for start in range(0, len(chunks), batch_size):
            chunk_batch = chunks[start : start + batch_size]
            keys = [
                _embedding_cache_key(settings.embedding_model, item["text"])
                for item in chunk_batch
            ]
            batch_vectors: list[list[float] | None] = [cached_vectors.get(key) for key in keys]
            missing_positions = [
                index for index, vector in enumerate(batch_vectors) if vector is None
            ]
            cache_hits += len(batch_vectors) - len(missing_positions)
            if missing_positions:
                embedded, latency = await ollama.embed(
                    [chunk_batch[index]["text"] for index in missing_positions],
                    keep_alive="10m",
                )
                embedding_latency += latency
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                with cache_path.open("a", encoding="utf-8") as cache_stream:
                    for position, vector in zip(missing_positions, embedded, strict=True):
                        batch_vectors[position] = vector
                        key = keys[position]
                        cached_vectors[key] = vector
                        cache_stream.write(
                            json.dumps(
                                {
                                    "key": key,
                                    "model": settings.embedding_model,
                                    "vector": vector,
                                },
                                separators=(",", ":"),
                            )
                            + "\n"
                        )
                    cache_stream.flush()
            vectors.extend(vector for vector in batch_vectors if vector is not None)
            batch_number = start // batch_size + 1
            if batch_number == 1 or batch_number % 10 == 0 or batch_number == total_batches:
                print(
                    f"Embedding progress: {batch_number}/{total_batches} batches "
                    f"({len(vectors)}/{len(chunks)} chunks)",
                    flush=True,
                )
        stored = store.replace(chunks, vectors)
    finally:
        store.close()
    return {
        "documents": parsed_documents,
        "chunks": stored,
        "embedding_model": settings.embedding_model,
        "embedding_latency_ms": round(embedding_latency, 2),
        "embedding_cache_hits": cache_hits,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest validated Afiyati guideline PDFs")
    parser.add_argument("--path", type=Path)
    args = parser.parse_args()
    settings = Settings.from_env()
    settings.ensure_directories()
    try:
        result = asyncio.run(ingest(settings, args.path))
        print("\nINGESTION RESULT")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"\nINGESTION FAILED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
