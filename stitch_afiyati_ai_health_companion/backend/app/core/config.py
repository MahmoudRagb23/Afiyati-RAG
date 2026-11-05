from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]


def _load_dotenv(path: Path) -> None:
    """Load local development settings without overriding real environment variables."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def _path_from_env(name: str, default: str) -> Path:
    value = Path(os.getenv(name, default))
    return value if value.is_absolute() else (ROOT_DIR / value).resolve()


def _bool_from_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    root_dir: Path = ROOT_DIR
    data_dir: Path = ROOT_DIR / "data"
    database_path: Path = ROOT_DIR / "data" / "afiyati.db"
    qdrant_path: Path = ROOT_DIR / "data" / "qdrant"
    qdrant_collection: str = "medical_guidelines"
    ollama_base_url: str = "http://127.0.0.1:11434"
    generation_model: str = "qwen3:4b"
    embedding_model: str = "qwen3-embedding:0.6b"
    reranker_model: str = "dengcao/Qwen3-Reranker-0.6B:Q8_0"
    secret_key: str = "afiyati-local-development-key-change-me"
    top_k: int = 5
    child_tokens: int = 450
    parent_tokens: int = 850
    chunk_overlap: int = 70
    embedding_batch_size: int = 16
    generation_timeout_seconds: float = 180.0
    generation_context_tokens: int = 4096
    generation_max_tokens: int = 420
    food_data_enabled: bool = True
    usda_fdc_api_key: str = "DEMO_KEY"
    usda_fdc_base_url: str = "https://api.nal.usda.gov/fdc/v1"
    food_cache_days: int = 30
    usda_timeout_seconds: float = 20.0
    cofid_enabled: bool = True
    cofid_dataset_path: Path = ROOT_DIR / "data" / "foods" / "raw" / "cofid_2021.xlsx"
    cofid_timeout_seconds: float = 60.0

    @classmethod
    def from_env(cls) -> "Settings":
        _load_dotenv(ROOT_DIR / ".env")
        database_url = os.getenv("DATABASE_URL", "sqlite:///./data/afiyati.db")
        database_value = database_url.removeprefix("sqlite:///")
        return cls(
            data_dir=_path_from_env("AFIYATI_DATA_DIR", "./data"),
            database_path=_path_from_env("AFIYATI_DATABASE_PATH", database_value),
            qdrant_path=_path_from_env("QDRANT_PATH", "./data/qdrant"),
            qdrant_collection=os.getenv("QDRANT_COLLECTION", "medical_guidelines"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
            generation_model=os.getenv("OLLAMA_GENERATION_MODEL", "qwen3:4b"),
            embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:0.6b"),
            reranker_model=os.getenv("OLLAMA_RERANKER_MODEL", "dengcao/Qwen3-Reranker-0.6B:Q8_0"),
            secret_key=os.getenv("AFIYATI_SECRET_KEY", "afiyati-local-development-key-change-me"),
            top_k=int(os.getenv("AFIYATI_TOP_K", "5")),
            child_tokens=int(os.getenv("AFIYATI_CHILD_TOKENS", "450")),
            parent_tokens=int(os.getenv("AFIYATI_PARENT_TOKENS", "850")),
            chunk_overlap=int(os.getenv("AFIYATI_CHUNK_OVERLAP", "70")),
            embedding_batch_size=int(os.getenv("AFIYATI_EMBED_BATCH_SIZE", "16")),
            generation_timeout_seconds=float(
                os.getenv("AFIYATI_GENERATION_TIMEOUT_SECONDS", "180")
            ),
            generation_context_tokens=int(os.getenv("AFIYATI_GENERATION_CONTEXT_TOKENS", "4096")),
            generation_max_tokens=int(os.getenv("AFIYATI_GENERATION_MAX_TOKENS", "420")),
            food_data_enabled=_bool_from_env("AFIYATI_FOOD_DATA_ENABLED", True),
            usda_fdc_api_key=os.getenv("USDA_FDC_API_KEY", "DEMO_KEY"),
            usda_fdc_base_url=os.getenv(
                "USDA_FDC_BASE_URL", "https://api.nal.usda.gov/fdc/v1"
            ).rstrip("/"),
            food_cache_days=int(os.getenv("AFIYATI_FOOD_CACHE_DAYS", "30")),
            usda_timeout_seconds=float(os.getenv("USDA_FDC_TIMEOUT_SECONDS", "20")),
            cofid_enabled=_bool_from_env("AFIYATI_COFID_ENABLED", True),
            cofid_dataset_path=_path_from_env(
                "AFIYATI_COFID_DATASET_PATH", "./data/foods/raw/cofid_2021.xlsx"
            ),
            cofid_timeout_seconds=float(os.getenv("AFIYATI_COFID_TIMEOUT_SECONDS", "60")),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.qdrant_path.parent.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "index").mkdir(parents=True, exist_ok=True)
        self.cofid_dataset_path.parent.mkdir(parents=True, exist_ok=True)
