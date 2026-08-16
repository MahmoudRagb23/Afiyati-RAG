from __future__ import annotations

import re


CONDITION_TERMS = {
    "hypertension": ["hypertension", "blood pressure", "ضغط", "الضغط"],
    "type_2_diabetes": ["type 2 diabetes", "diabetes", "t2d", "سكري", "السكري"],
    "chronic_kidney_disease": ["chronic kidney", "ckd", "kidney disease", "الكلى", "كلوي"],
    "asthma": ["asthma", "ربو", "الربو"],
}

TOPIC_TERMS = {
    "hba1c": ["hba1c", "glycated haemoglobin", "السكر التراكمي"],
    "home_blood_pressure": ["home blood pressure", "hbpm", "قياس الضغط في المنزل", "ضغط منزلي"],
    "mediterranean_diet": ["mediterranean", "حمية البحر المتوسط", "النظام المتوسطي"],
    "potassium": ["potassium", "بوتاسيوم"],
    "ace_inhibitor": ["ace inhibitor", "acei", "ras inhibitor", "مثبط الإنزيم المحول"],
    "fasting": ["fasting", "ramadan", "صيام", "الصيام", "رمضان"],
    "coffee": ["coffee", "caffeine", "قهو", "كافيين"],
    "banana": ["banana", "موز"],
    "rice": ["rice", "أرز", "رز"],
    "sodium": ["salt", "sodium", "ملح", "صوديوم"],
    "exercise": ["exercise", "walking", "physical activity", "رياضة", "مشي", "نشاط بدني", "النشاط البدني"],
    "sleep": ["sleep", "نوم"],
    "smoking": ["smoking", "cigarette", "تدخين", "سجائر"],
}


def analyze_query(text: str, profile_conditions: list[str] | None = None, mode: str = "chat") -> dict:
    normalized = text.lower()
    mentioned = [
        condition
        for condition, terms in CONDITION_TERMS.items()
        if any(term in normalized for term in terms)
    ]
    conditions = list(dict.fromkeys((profile_conditions or []) + mentioned))
    topic = next(
        (topic for topic, terms in TOPIC_TERMS.items() if any(term in normalized for term in terms)),
        "general_lifestyle",
    )
    if mode == "meal":
        intent = "meal_analysis"
    elif mode == "food" or any(term in normalized for term in ["food", "eat", "مناسب", "أكل"]):
        intent = "food_question"
    elif mode == "habit" or topic in {"coffee", "exercise", "sleep", "smoking"}:
        intent = "habit_question"
    elif mode == "symptom":
        intent = "symptom_question"
    elif re.search(r"dose|medicat|drug|دواء|جرعة", normalized):
        intent = "medication_question"
    else:
        intent = "general_guideline_question"
    return {"intent": intent, "conditions": conditions, "topic": topic, "subject": topic}


def rewrite_queries(original: str, analysis: dict) -> list[str]:
    topic = analysis["topic"]
    topic_expansion = {
        "hba1c": "HbA1c measurement individualized glycaemic target",
        "home_blood_pressure": "home blood pressure monitoring HBPM self-monitoring",
        "mediterranean_diet": "Mediterranean dietary pattern healthy diet",
        "potassium": "dietary potassium intake hyperkalemia individualized advice",
        "ace_inhibitor": "ACE inhibitor ACEi RASi monitoring lifestyle",
        "fasting": "fasting Ramadan medication safety",
        "coffee": "coffee caffeine intake",
        "banana": "banana fruit potassium",
        "rice": "rice carbohydrate glycemic",
        "sodium": "dietary sodium salt",
        "exercise": "physical activity exercise",
        "sleep": "sleep duration lifestyle",
        "smoking": "smoking cessation",
        "general_lifestyle": original,
    }.get(topic, original)
    queries = [original]
    for condition in analysis.get("conditions", []):
        label = condition.replace("_", " ")
        queries.append(f"{topic_expansion} {label} clinical guideline recommendation")
    return list(dict.fromkeys(query.strip() for query in queries if query.strip()))
