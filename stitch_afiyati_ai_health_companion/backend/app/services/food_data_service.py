from __future__ import annotations

import asyncio
import json
import math
import re
from pathlib import Path
from typing import Any

import httpx

from app.core.config import Settings
from app.db.database import Database
from app.services.cofid_service import CoFIDProvider


ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]")
NON_WORD = re.compile(r"[^\w]+", re.UNICODE)

NUTRIENTS = {
    1008: ("calories_kcal", "سعر حراري"),
    2047: ("calories_kcal", "سعر حراري"),
    2048: ("calories_kcal", "سعر حراري"),
    1003: ("protein_g", "جم"),
    1004: ("fat_g", "جم"),
    1005: ("carbohydrates_g", "جم"),
    1079: ("fiber_g", "جم"),
    2000: ("sugars_g", "جم"),
    1093: ("sodium_mg", "مجم"),
    1092: ("potassium_mg", "مجم"),
    1258: ("saturated_fat_g", "جم"),
    1057: ("caffeine_mg", "مجم"),
}

DATA_TYPE_PRIORITY = {
    "Foundation": 0.3,
    "SR Legacy": 0.2,
    "Survey (FNDDS)": 0.1,
}

GRAM_QUANTITY = r"(\d+(?:\.\d+)?)\s*(?:جم|جرام|جرامات|غ|غرام|غرامات|g|gram|grams)"


def normalize_food_text(value: str) -> str:
    normalized = ARABIC_DIACRITICS.sub("", value.strip().lower())
    normalized = normalized.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"}))
    return " ".join(NON_WORD.sub(" ", normalized).split())


def normalize_quantity_text(value: str) -> str:
    protected = re.sub(r"(?<=\d)[.,٫](?=\d)", "_decimal_", value)
    return normalize_food_text(protected).replace("_decimal_", ".")


class FoodDataService:
    def __init__(
        self,
        settings: Settings,
        database: Database,
        transport: httpx.AsyncBaseTransport | None = None,
        cofid_provider: CoFIDProvider | None = None,
    ):
        self.settings = settings
        self.database = database
        self.transport = transport
        self.aliases = self._load_json(settings.root_dir / "data" / "foods" / "aliases.ar.json", [])
        self.sources = self._load_json(settings.root_dir / "data" / "foods" / "sources.json", [])
        self.source = next((item for item in self.sources if item.get("id") == "usda_fdc"), {})
        cofid_source = next(
            (item for item in self.sources if item.get("id") == "uk_cofid_2021"), {}
        )
        self.cofid = cofid_provider or CoFIDProvider(settings, cofid_source)
        self.alias_index = sorted(
            (
                (normalize_food_text(alias), entry)
                for entry in self.aliases
                for alias in [entry.get("name_ar", ""), *entry.get("aliases", [])]
                if normalize_food_text(alias)
            ),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    @staticmethod
    def _load_json(path: Path, fallback: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return fallback

    def status(self) -> dict:
        with self.database.session() as connection:
            cached_records = connection.execute("SELECT COUNT(*) AS total FROM food_lookup_cache").fetchone()["total"]
        return {
            "enabled": self.settings.food_data_enabled,
            "sources": [
                {
                    "id": source.get("id"),
                    "name": source.get("name"),
                    "authority_level": source.get("authority_level"),
                    "active": source.get("active", False),
                }
                for source in self.sources
            ],
            "aliases": len(self.aliases),
            "cached_records": cached_records,
            "configured": bool(self.settings.usda_fdc_api_key),
            "cofid": self.cofid.status(),
        }

    def source_catalog(self) -> list[dict]:
        allowed_fields = {
            "id",
            "name",
            "organization",
            "type",
            "website_url",
            "api_guide_url",
            "guide_url",
            "version",
            "license",
            "active",
            "authority_level",
            "usage",
        }
        return [
            {key: value for key, value in source.items() if key in allowed_fields}
            for source in self.sources
        ]

    def _resolve_entry(self, value: str) -> dict | None:
        normalized = normalize_food_text(value)
        for alias, entry in self.alias_index:
            if self._contains_alias(normalized, alias):
                return entry
        return None

    @staticmethod
    def _contains_alias(normalized: str, alias: str) -> bool:
        return f" {alias} " in f" {normalized} "

    def _entries_from_question(self, question: str) -> list[dict]:
        normalized = normalize_food_text(question)
        matches: list[dict] = []
        seen: set[str] = set()
        occupied_aliases: list[str] = []
        for alias, entry in self.alias_index:
            query = entry.get("query") or entry.get("name_ar")
            if (
                self._contains_alias(normalized, alias)
                and query not in seen
                and not any(alias in value for value in occupied_aliases)
            ):
                matches.append(entry)
                seen.add(query)
                occupied_aliases.append(alias)
        return matches[:5]

    async def lookup_question(
        self,
        question: str,
        confirmed_ingredients: list[str] | None = None,
        food_quantities: list[dict] | None = None,
        mode: str = "chat",
    ) -> dict:
        result = {"items": [], "notices": [], "matched_terms": [], "entries": []}
        if not self.settings.food_data_enabled:
            return result

        targets: list[tuple[dict, float, bool]] = []
        if food_quantities:
            for quantity in food_quantities[:20]:
                name = str(quantity.get("name", "")).strip()
                amount_g = float(quantity.get("amount_g", 100))
                entry = self._resolve_entry(name)
                if entry:
                    targets.append((entry, amount_g, True))
                else:
                    result["notices"].append(
                        f"لم أجد اسماً موثقاً للمكوّن «{name}». لم أضف له أي قيم غذائية."
                    )
        elif confirmed_ingredients:
            for ingredient in confirmed_ingredients[:8]:
                entry = self._resolve_entry(ingredient)
                if entry:
                    targets.append((entry, 100.0, False))
                else:
                    result["notices"].append(
                        f"لم أجد اسماً موثقاً للمكوّن «{ingredient}». لم أضف له أي قيم غذائية."
                    )
        else:
            entries = self._entries_from_question(question)
            targets = []
            for entry in entries:
                amount = self._amount_for_entry(question, entry, len(entries) == 1)
                targets.append((entry, amount or 100.0, amount is not None))

        seen_queries: set[str] = set()
        for entry, amount_g, amount_provided in targets:
            display_name = entry.get("name_ar", "الطعام")
            display_amount = int(amount_g) if amount_g.is_integer() else amount_g
            result["entries"].append(
                {
                    "name_ar": display_name,
                    "category": entry.get("category", "food"),
                    "requires_ingredients": bool(entry.get("requires_ingredients")),
                    "amount_g": display_amount,
                    "amount_provided": amount_provided,
                }
            )
            if entry.get("requires_ingredients"):
                result["notices"].append(
                    f"«{display_name}» وصفة مركبة؛ أكّد المكونات والكميات أولاً حتى لا تُعرض قيم غير دقيقة."
                )
                continue
            query = entry.get("query")
            if not query or query in seen_queries:
                continue
            seen_queries.add(query)
            result["matched_terms"].append(display_name)
            item, notice = await self._lookup(entry)
            if item:
                result["items"].append(self._scale_item(item, amount_g, amount_provided))
            elif notice:
                result["notices"].append(notice)

        if mode in {"food", "meal"} and not targets and not result["notices"]:
            result["notices"].append(
                "لم أتعرف على طعام محدد للبحث في المصدر. اكتب اسم الطعام أو المشروب بوضوح."
            )
        return result

    def _amount_for_entry(self, question: str, entry: dict, allow_generic: bool) -> float | None:
        normalized = normalize_quantity_text(question)
        aliases = sorted(
            {
                normalize_food_text(value)
                for value in [entry.get("name_ar", ""), *entry.get("aliases", [])]
                if normalize_food_text(value)
            },
            key=len,
            reverse=True,
        )
        for alias in aliases:
            escaped = re.escape(alias)
            patterns = [
                rf"(?:^|\s){GRAM_QUANTITY}\s+(?:من\s+)?{escaped}(?:\s|$)",
                rf"(?:^|\s){escaped}\s+{GRAM_QUANTITY}(?:\s|$)",
            ]
            for pattern in patterns:
                match = re.search(pattern, normalized)
                if match:
                    return self._valid_amount(match.group(1))
        if allow_generic:
            match = re.search(GRAM_QUANTITY, normalized)
            if match:
                return self._valid_amount(match.group(1))
        return None

    @staticmethod
    def _valid_amount(value: str) -> float | None:
        amount = float(value)
        return amount if 1 <= amount <= 5000 else None

    @staticmethod
    def _scale_item(item: dict, amount_g: float, amount_provided: bool = False) -> dict:
        scale = amount_g / 100
        display_amount = int(amount_g) if amount_g.is_integer() else amount_g
        supporting_sources = [
            {
                **source_item,
                "basis": f"للكمية المحددة: {display_amount} جم",
                "nutrients": {
                    key: {**nutrient, "value": round(nutrient["value"] * scale, 2)}
                    for key, nutrient in source_item.get("nutrients", {}).items()
                },
            }
            for source_item in item.get("supporting_sources", [])
        ]
        scaled = {
            **item,
            "amount_g": display_amount,
            "amount_provided": amount_provided,
            "basis": f"للكمية المحددة: {display_amount} جم ({item['source']['title']} لكل 100 جم)",
            "nutrients": {
                key: {**nutrient, "value": round(nutrient["value"] * scale, 2)}
                for key, nutrient in item.get("nutrients", {}).items()
            },
            "supporting_sources": supporting_sources,
        }
        if supporting_sources:
            scaled["source_comparison"] = FoodDataService._compare_sources(
                scaled, supporting_sources[0]
            )
        return scaled

    async def _lookup(self, entry: dict) -> tuple[dict | None, str | None]:
        query = entry["query"]
        query_key = f"official-multi-v1:{normalize_food_text(query)}"
        cached = self._cache_get(query_key)
        if cached and (not self.settings.cofid_enabled or cached.get("source_count", 1) > 1):
            return cached, None

        usda_result, cofid_result = await asyncio.gather(
            self._lookup_usda(entry),
            self.cofid.search(entry),
            return_exceptions=True,
        )
        usda_item = usda_result if isinstance(usda_result, dict) else None
        cofid_item = cofid_result if isinstance(cofid_result, dict) else None
        if not usda_item and not cofid_item:
            return (
                None,
                f"تعذر العثور على سجل رسمي موثوق لـ«{entry['name_ar']}» في USDA أو CoFID، لذلك لم أعرض أي أرقام.",
            )

        item = usda_item or cofid_item
        supporting = cofid_item if usda_item and cofid_item else None
        item["source_count"] = 2 if supporting else 1
        item["source_status"] = (
            "cross_checked_official_sources" if supporting else "single_official_source"
        )
        item["supporting_sources"] = []
        if supporting:
            item["supporting_sources"].append(
                {
                    "matched_name": supporting["matched_name"],
                    "basis": supporting["basis"],
                    "nutrients": supporting["nutrients"],
                    "source": supporting["source"],
                    "record_context": supporting.get("record_context"),
                }
            )
            item["source_comparison"] = self._compare_sources(item, supporting)
        if not self.settings.cofid_enabled or item["source_count"] > 1:
            self._cache_put(query_key, item)
        return item, None

    async def _lookup_usda(self, entry: dict) -> dict | None:
        query = entry["query"]

        try:
            async with httpx.AsyncClient(
                transport=self.transport,
                timeout=self.settings.usda_timeout_seconds,
            ) as client:
                response = await client.post(
                    f"{self.settings.usda_fdc_base_url}/foods/search",
                    params={"api_key": self.settings.usda_fdc_api_key},
                    json={
                        "query": query,
                        "pageSize": 10,
                        "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"],
                    },
                )
                response.raise_for_status()
                foods = response.json().get("foods", [])
        except (httpx.HTTPError, json.JSONDecodeError, TypeError, ValueError):
            return None

        selected = self._select_food(query, foods)
        if not selected:
            return None
        item = self._normalize_food(entry, selected)
        if not item["nutrients"]:
            return None
        return item

    @staticmethod
    def _compare_sources(primary: dict, secondary: dict) -> dict:
        shared_keys = sorted(set(primary.get("nutrients", {})) & set(secondary.get("nutrients", {})))
        nutrients = [
            {
                "key": key,
                "primary_value": primary["nutrients"][key]["value"],
                "primary_unit": primary["nutrients"][key]["unit"],
                "secondary_value": secondary["nutrients"][key]["value"],
                "secondary_unit": secondary["nutrients"][key]["unit"],
            }
            for key in shared_keys
            if primary["nutrients"][key]["unit"].upper()
            == secondary["nutrients"][key]["unit"].upper()
        ]
        return {
            "status": "independent_official_comparison",
            "shared_nutrients": nutrients,
            "note": "القيم معروضة منفصلة كما وردت في كل قاعدة رسمية؛ لا يتم دمجها أو أخذ متوسطها.",
        }

    @staticmethod
    def _select_food(query: str, foods: list[dict]) -> dict | None:
        def search_tokens(value: str) -> set[str]:
            return {
                token[:-1] if token.endswith("s") and len(token) > 3 else token
                for token in normalize_food_text(value).split()
            }

        query_tokens = search_tokens(query)

        def score(item: dict, index: int) -> float:
            description_tokens = search_tokens(item.get("description", ""))
            overlap_count = len(query_tokens & description_tokens)
            recall = overlap_count / max(len(query_tokens), 1)
            precision = overlap_count / max(len(description_tokens), 1)
            return (
                recall * 10
                + precision * 2
                + DATA_TYPE_PRIORITY.get(item.get("dataType", ""), 0)
                - index / 1000
            )

        candidates = [item for item in foods if item.get("fdcId") and item.get("description")]
        return max(candidates, key=lambda item: score(item, foods.index(item)), default=None)

    def _normalize_food(self, entry: dict, food: dict) -> dict:
        nutrients: dict[str, dict] = {}
        for nutrient in food.get("foodNutrients", []):
            nutrient_id = nutrient.get("nutrientId")
            definition = NUTRIENTS.get(nutrient_id)
            amount = nutrient.get("value", nutrient.get("amount"))
            if not definition or not isinstance(amount, (int, float)) or not math.isfinite(amount):
                continue
            key, fallback_unit = definition
            if key in nutrients and nutrient_id != 1008:
                continue
            nutrients[key] = {
                "value": round(float(amount), 2),
                "unit": nutrient.get("unitName") or fallback_unit,
            }

        fdc_id = str(food["fdcId"])
        return {
            "requested_name": entry["name_ar"],
            "matched_name": food["description"],
            "category": entry.get("category", "food"),
            "basis": "بيانات USDA لكل 100 جم",
            "nutrients": nutrients,
            "source": {
                "organization": self.source.get(
                    "organization", "U.S. Department of Agriculture, Agricultural Research Service"
                ),
                "title": self.source.get("name", "USDA FoodData Central"),
                "record_id": fdc_id,
                "data_type": food.get("dataType"),
                "url": f"https://fdc.nal.usda.gov/fdc-app.html#/food-details/{fdc_id}/nutrients",
                "license": self.source.get("license", "CC0 1.0 Universal"),
                "authority_level": self.source.get("authority_level", "official_primary"),
            },
        }

    def _cache_get(self, query_key: str) -> dict | None:
        with self.database.session() as connection:
            row = connection.execute(
                """
                SELECT response_json FROM food_lookup_cache
                WHERE query_key=? AND updated_at >= datetime('now', ?)
                """,
                (query_key, f"-{self.settings.food_cache_days} days"),
            ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["response_json"])
        except (json.JSONDecodeError, TypeError):
            return None

    def _cache_put(self, query_key: str, item: dict) -> None:
        with self.database.session() as connection:
            connection.execute(
                """
                INSERT INTO food_lookup_cache (query_key,response_json,updated_at)
                VALUES (?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(query_key) DO UPDATE SET
                    response_json=excluded.response_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (query_key, json.dumps(item, ensure_ascii=False)),
            )
