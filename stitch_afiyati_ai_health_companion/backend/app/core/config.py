from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]


def _path_from_env(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else (ROOT_DIR / value).resolve()


@dataclass(slots=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    database_path: Path = ROOT_DIR / "data" / "afiyati.db"
    qdrant_path: Path = ROOT_DIR / "data" / "qdrant"
    qdrant_collection: str = "medical_guidelines"
    ollama_base_url: str = "http://127.0.0.1:11434"
    generation_model: str = "qwen3:8b"
    embedding_model: str = "qwen3-embedding:0.6b"
    reranker_model: str = "dengcao/Qwen3-Reranker-0.6B:Q8_0"
    secret_key: str = "afiyati-local-development-key-change-me"
    top_k: int = 5
    child_tokens: int = 450
    parent_tokens: int = 850
    chunk_overlap: int = 70
    embedding_batch_size: int = 16

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.getenv("DATABASE_URL", "sqlite:///./data/afiyati.db")
        database_value = database_url.removeprefix("sqlite:///")
        return cls(
            data_dir=_path_from_env("AFIYATI_DATA_DIR", "./data"),
            database_path=_path_from_env("AFIYATI_DATABASE_PATH", database_value),
            qdrant_path=_path_from_env("QDRANT_PATH", "./data/qdrant"),
            qdrant_collection=os.getenv("QDRANT_COLLECTION", "medical_guidelines"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
            generation_model=os.getenv("OLLAMA_GENERATION_MODEL", "qwen3:8b"),
            embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:0.6b"),
            reranker_model=os.getenv("OLLAMA_RERANKER_MODEL", "dengcao/Qwen3-Reranker-0.6B:Q8_0"),
            secret_key=os.getenv("AFIYATI_SECRET_KEY", "afiyati-local-development-key-change-me"),
            top_k=int(os.getenv("AFIYATI_TOP_K", "5")),
            child_tokens=int(os.getenv("AFIYATI_CHILD_TOKENS", "450")),
            parent_tokens=int(os.getenv("AFIYATI_PARENT_TOKENS", "850")),
            chunk_overlap=int(os.getenv("AFIYATI_CHUNK_OVERLAP", "70")),
            embedding_batch_size=int(os.getenv("AFIYATI_EMBED_BATCH_SIZE", "16")),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.qdrant_path.parent.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "index").mkdir(parents=True, exist_ok=True)
