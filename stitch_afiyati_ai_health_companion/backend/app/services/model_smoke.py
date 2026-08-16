from __future__ import annotations

import asyncio
import json

from app.core.config import Settings
from app.services.ollama_service import OllamaService


async def main_async() -> dict:
    settings = Settings.from_env()
    service = OllamaService(settings)
    result: dict = {"models": await service.models(), "embeddings": {}}
    sample = "dietary sodium recommendation for hypertension | إرشادات الصوديوم لارتفاع ضغط الدم"
    for model in ("nomic-embed-text", "qwen3-embedding:0.6b", "bge-m3"):
        vectors, latency = await service.embed([sample], model=model)
        result["embeddings"][model] = {"dimensions": len(vectors[0]), "single_input_latency_ms": round(latency, 2)}
    generated, latency = await service.generate_json(
        "Return JSON with status set to ready and no other commentary.",
        {
            "type": "object",
            "required": ["status"],
            "properties": {"status": {"type": "string", "enum": ["ready"]}},
        },
    )
    result["generation"] = {"model": settings.generation_model, "response": generated, "smoke_latency_ms": round(latency, 2)}
    return result


def main() -> int:
    print(json.dumps(asyncio.run(main_async()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

