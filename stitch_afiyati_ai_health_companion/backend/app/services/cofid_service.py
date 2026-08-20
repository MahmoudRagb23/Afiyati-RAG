from __future__ import annotations

import asyncio
import math
import threading
from pathlib import Path

import httpx
from openpyxl import load_workbook

from app.core.config import Settings


STOP_WORDS = {"a", "an", "and", "in", "of", "the", "with"}


def _ordered_tokens(value: str) -> list[str]:
    normalized = "".join(character.lower() if character.isalnum() else " " for character in value)
    return [
        token[:-1] if token.endswith("s") and len(token) > 3 else token
        for token in normalized.split()
        if token and token not in STOP_WORDS
    ]


def _tokens(value: str) -> set[str]:
    return set(_ordered_tokens(value))


def _number(value) -> float | None:
    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    if not isinstance(value, str) or value.strip().lower() in {"", "n", "tr"}:
        return None
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else None
    except ValueError:
        return None


class CoFIDProvider:
    def __init__(self, settings: Settings, source: dict):
        self.settings = settings
        self.source = source
        self.path = settings.cofid_dataset_path
        self.records: list[dict] | None = None
        self.last_error: str | None = None
        self._lock = threading.Lock()

    def status(self) -> dict:
        return {
            "enabled": self.settings.cofid_enabled,
            "dataset_downloaded": self.path.exists(),
            "records_loaded": len(self.records or []),
            "version": self.source.get("version", "2021"),
            "last_error": self.last_error,
        }

    async def search(self, entry: dict) -> dict | None:
        if not self.settings.cofid_enabled or entry.get("cofid_supported") is False:
            return None
        try:
            return await asyncio.to_thread(self._search_sync, entry)
        except (OSError, ValueError, KeyError, httpx.HTTPError) as exc:
            self.last_error = type(exc).__name__
            return None

    def _search_sync(self, entry: dict) -> dict | None:
        self._ensure_loaded()
        query = entry.get("cofid_query") or entry.get("query", "")
        ordered_query_tokens = _ordered_tokens(query)
        query_tokens = _tokens(query)
        if not query_tokens or not self.records:
            return None
        identity_token = ordered_query_tokens[0]
        excluded_tokens = set(entry.get("cofid_exclude_tokens", []))
        eligible_records = [
            record
            for record in self.records
            if identity_token in _tokens(record["name"])
            and not (excluded_tokens & _tokens(record["name"]))
        ]
        if not eligible_records:
            return None

        def score(record: dict) -> float:
            record_tokens = _tokens(record["name"])
            overlap = len(query_tokens & record_tokens)
            recall = overlap / len(query_tokens)
            precision = overlap / max(len(record_tokens), 1)
            return recall * 10 + precision * 2

        selected = max(eligible_records, key=score)
        selected_tokens = _tokens(selected["name"])
        overlap = len(query_tokens & selected_tokens)
        required_overlap = max(1, math.ceil(len(query_tokens) * 0.75))
        if len(query_tokens) > 1:
            required_overlap = max(2, required_overlap)
        if overlap < required_overlap or score(selected) < 4.5:
            return None
        return {
            "requested_name": entry["name_ar"],
            "matched_name": selected["name"],
            "category": entry.get("category", "food"),
            "basis": "بيانات CoFID لكل 100 جم",
            "nutrients": selected["nutrients"],
            "source": {
                "organization": self.source.get("organization", "Public Health England"),
                "title": self.source.get(
                    "name", "UK Composition of Foods Integrated Dataset (CoFID) 2021"
                ),
                "record_id": selected["code"],
                "data_type": "CoFID 2021",
                "url": self.source.get("website_url"),
                "license": self.source.get("license", "Open Government Licence v3.0"),
                "authority_level": self.source.get("authority_level", "official_primary"),
            },
            "record_context": {
                "description": selected.get("description"),
                "main_data_reference": selected.get("main_data_reference"),
            },
        }

    def _ensure_loaded(self) -> None:
        if self.records is not None:
            return
        with self._lock:
            if self.records is not None:
                return
            if not self.path.exists():
                self._download()
            self.records = self._load_records(self.path)
            self.last_error = None

    def _download(self) -> None:
        url = self.source.get("dataset_url")
        if not url:
            raise ValueError("CoFID dataset URL is not configured")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.path.with_suffix(".xlsx.part")
        with httpx.stream(
            "GET",
            url,
            follow_redirects=True,
            timeout=self.settings.cofid_timeout_seconds,
        ) as response:
            response.raise_for_status()
            with temporary_path.open("wb") as output:
                for chunk in response.iter_bytes():
                    output.write(chunk)
        temporary_path.replace(self.path)

    @staticmethod
    def _load_records(path: Path) -> list[dict]:
        workbook = load_workbook(path, read_only=True, data_only=True)
        proximates = workbook["1.3 Proximates"]
        inorganics = workbook["1.4 Inorganics"]
        minerals: dict[str, dict] = {}
        for row in inorganics.iter_rows(min_row=4, values_only=True):
            code = str(row[0] or "").strip()
            if not code:
                continue
            minerals[code] = {
                "sodium_mg": _number(row[7]),
                "potassium_mg": _number(row[8]),
            }

        records: list[dict] = []
        nutrient_columns = {
            "protein_g": (9, "G"),
            "fat_g": (10, "G"),
            "carbohydrates_g": (11, "G"),
            "calories_kcal": (12, "KCAL"),
            "sugars_g": (16, "G"),
            "fiber_g": (25, "G"),
            "saturated_fat_g": (27, "G"),
        }
        for row in proximates.iter_rows(min_row=4, values_only=True):
            code = str(row[0] or "").strip()
            name = str(row[1] or "").strip()
            if not code or not name:
                continue
            nutrients = {
                key: {"value": value, "unit": unit}
                for key, (index, unit) in nutrient_columns.items()
                if (value := _number(row[index])) is not None
            }
            for key, value in minerals.get(code, {}).items():
                if value is not None:
                    nutrients[key] = {"value": value, "unit": "MG"}
            if not nutrients:
                continue
            records.append(
                {
                    "code": code,
                    "name": name,
                    "description": row[2],
                    "main_data_reference": row[5],
                    "nutrients": nutrients,
                }
            )
        workbook.close()
        return records
