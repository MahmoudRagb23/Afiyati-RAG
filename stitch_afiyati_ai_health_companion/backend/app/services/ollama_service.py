from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.core.config import Settings


class OllamaError(RuntimeError):
    pass


class OllamaService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.settings.ollama_base_url}/api/tags")
                response.raise_for_status()
            return [item["name"] for item in response.json().get("models", [])]
        except (httpx.HTTPError, KeyError) as exc:
            raise OllamaError(f"Ollama is unavailable: {exc}") from exc

    async def embed(
        self,
        texts: list[str],
        model: str | None = None,
        keep_alive: str | int = 0,
    ) -> tuple[list[list[float]], float]:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.settings.ollama_base_url}/api/embed",
                    json={
                        "model": model or self.settings.embedding_model,
                        "input": texts,
                        "truncate": True,
                        "keep_alive": keep_alive,
                    },
                )
                response.raise_for_status()
            embeddings = response.json().get("embeddings")
            if not embeddings or len(embeddings) != len(texts):
                raise OllamaError("Ollama returned an invalid embedding response")
            return embeddings, (time.perf_counter() - started) * 1000
        except httpx.HTTPError as exc:
            raise OllamaError(f"Embedding model unavailable: {exc}") from exc

    async def generate_json(
        self, prompt: str, schema: dict[str, Any], model: str | None = None
    ) -> tuple[dict[str, Any], float]:
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.settings.generation_timeout_seconds) as client:
                response = await client.post(
                    f"{self.settings.ollama_base_url}/api/generate",
                    json={
                        "model": model or self.settings.generation_model,
                        "prompt": prompt,
                        "stream": False,
                        "think": False,
                        "format": schema,
                        "keep_alive": "2m",
                        "options": {
                            "temperature": 0.1,
                            "num_ctx": self.settings.generation_context_tokens,
                            "num_predict": self.settings.generation_max_tokens,
                        },
                    },
                )
                response.raise_for_status()
            raw = response.json().get("response", "")
            return json.loads(raw), (time.perf_counter() - started) * 1000
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise OllamaError(f"Generation failed: {exc}") from exc
