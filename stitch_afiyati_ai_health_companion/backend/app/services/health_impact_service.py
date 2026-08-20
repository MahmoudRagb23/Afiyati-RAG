from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.conditions import SUPPORTED_CONDITION_SET


CONDITION_LABELS = {
    "hypertension": "ارتفاع ضغط الدم",
    "type_2_diabetes": "السكري من النوع الثاني",
}

ACTION_LABELS = {
    "no_documented_harm": "لا ضرر خاص موثق",
    "ask_quantity": "نحتاج الكمية أولاً",
    "review_portion": "راجع الكمية",
    "reduce": "قلّل",
    "avoid": "تجنّب",
    "needs_ingredients": "ثبّت المكونات",
    "insufficient_evidence": "لا يوجد حكم خاص موثق",
}


class HealthImpactService:
    """Applies reviewed, source-linked food rules to registered conditions only."""

    def __init__(self, root_dir: Path):
        self.rules_data = self._load_json(root_dir / "data" / "foods" / "health_rules.ar.json", {})
        self.activities_data = self._load_json(
            root_dir / "data" / "activities" / "activities.ar.json", {}
        )
        self.sources = {
            item["id"]: item
            for item in self.rules_data.get("sources", [])
            if isinstance(item, dict) and item.get("id")
        }
        self.activity_sources = {
            item["id"]: item
            for item in self.activities_data.get("sources", [])
            if isinstance(item, dict) and item.get("id")
        }
        self.food_groups = self._food_group_index()
        self.rules = [item for item in self.rules_data.get("rules", []) if isinstance(item, dict)]

    @staticmethod
    def _load_json(path: Path, fallback: Any) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return fallback

    def _food_group_index(self) -> dict[str, list[dict]]:
        index: dict[str, list[dict]] = {}
        for group in self.rules_data.get("meal_groups", []):
            if not isinstance(group, dict) or not group.get("id"):
                continue
            for food_name in group.get("foods", []):
                index.setdefault(str(food_name), []).append(
                    {"id": group["id"], "label": group.get("label", group["id"])}
                )
        return index

    def status(self) -> dict:
        return {
            "rules": len(self.rules),
            "meal_groups": len(self.rules_data.get("meal_groups", [])),
            "medical_sources": len(self.sources),
            "activities": len(self.activities_data.get("activities", [])),
            "activity_sources": len(self.activity_sources),
        }

    def catalog(self) -> dict:
        return {
            "medical_sources": list(self.sources.values()),
            "activity_sources": list(self.activity_sources.values()),
            "meal_groups": [
                {"id": item.get("id"), "label": item.get("label"), "food_count": len(item.get("foods", []))}
                for item in self.rules_data.get("meal_groups", [])
                if isinstance(item, dict)
            ],
            "activities": self.activities_data.get("activities", []),
        }

    def assess(self, food_context: dict, conditions: list[str]) -> list[dict]:
        active_conditions = [condition for condition in conditions if condition in SUPPORTED_CONDITION_SET]
        if not active_conditions:
            return []
        impacts = []
        for entry in food_context.get("entries", []):
            if not isinstance(entry, dict) or not entry.get("name_ar"):
                continue
            food_name = entry["name_ar"]
            groups = self.food_groups.get(food_name, [])
            impact = {
                "food_name": food_name,
                "category": entry.get("category", "food"),
                "meal_groups": groups,
                "amount_g": entry.get("amount_g"),
                "amount_provided": bool(entry.get("amount_provided")),
                "assessments": [],
            }
            if entry.get("requires_ingredients"):
                impact["requires_ingredients"] = True
                impact["assessments"] = [
                    self._ingredient_assessment(condition, food_name) for condition in active_conditions
                ]
            else:
                impact["assessments"] = [
                    self._assessment_for_entry(entry, groups, condition) for condition in active_conditions
                ]
            impacts.append(impact)
        return impacts

    def _ingredient_assessment(self, condition: str, food_name: str) -> dict:
        return {
            "condition": condition,
            "condition_label": CONDITION_LABELS[condition],
            "action": "needs_ingredients",
            "action_label": ACTION_LABELS["needs_ingredients"],
            "assessment": f"«{food_name}» طبق مركب؛ لا يمكن تحديد أثره على حالتك قبل معرفة المكونات وطريقة التحضير.",
            "advice": "أضف المكونات والكميات، وبالأخص الملح والسكريات والدهون المضافة، ثم أعد التحليل.",
            "question": "ما المكونات وكميات كل مكوّن؟",
            "sources": [],
        }

    def _assessment_for_entry(self, entry: dict, groups: list[dict], condition: str) -> dict:
        group_ids = {group["id"] for group in groups}
        matching_rules = [
            rule
            for rule in self.rules
            if rule.get("condition") == condition
            and group_ids.intersection(rule.get("food_groups", []))
        ]
        if not matching_rules:
            return {
                "condition": condition,
                "condition_label": CONDITION_LABELS[condition],
                "action": "insufficient_evidence",
                "action_label": ACTION_LABELS["insufficient_evidence"],
                "assessment": "لا توجد قاعدة طعام خاصة ومراجعة لهذا الصنف ضمن مصادر التطبيق الحالية؛ لن أصفه بأنه آمن أو ضار بالتخمين.",
                "advice": "اعتمد على القيم الغذائية والمصدر الظاهرين، وأضف طريقة التحضير والكمية أو اسأل اختصاصي التغذية إذا كانت لديك خطة علاجية خاصة.",
                "question": None,
                "sources": [],
            }
        rule = max(matching_rules, key=lambda item: int(item.get("priority", 0)))
        action = rule.get("action", "insufficient_evidence")
        needs_quantity = bool(rule.get("needs_quantity")) and not entry.get("amount_provided")
        if needs_quantity:
            action = "ask_quantity"
        food_name = entry["name_ar"]
        return {
            "condition": condition,
            "condition_label": CONDITION_LABELS[condition],
            "action": action,
            "action_label": ACTION_LABELS[action],
            "assessment": rule.get("assessment", "لا توجد قاعدة قابلة للعرض لهذا الصنف."),
            "advice": rule.get("advice", "راجع خطتك الغذائية الفردية."),
            "question": f"ما كمية «{food_name}» التي تناولتها؟" if needs_quantity else None,
            "sources": [self.sources[source_id] for source_id in rule.get("source_ids", []) if source_id in self.sources],
        }
