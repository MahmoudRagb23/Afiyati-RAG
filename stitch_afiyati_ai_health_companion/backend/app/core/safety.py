from __future__ import annotations

import re
from dataclasses import dataclass


EMERGENCY_PATTERNS = {
    "chest_pain": [
        r"chest pain",
        r"chest pressure",
        r"ألم (?:شديد )?في الصدر",
        r"وجع (?:شديد )?في الصدر",
        r"ضغط (?:شديد )?(?:على|في) الصدر",
        r"وجع (?:شديد )?في قلبي",
    ],
    "breathing": [
        r"can't breathe",
        r"cannot breathe",
        r"difficulty breathing",
        r"shortness of breath",
        r"choking",
        r"gasping(?: for air)?",
        r"ضيق (?:شديد )?(?:في )?التنفس",
        r"ضيق نفس",
        r"صعوبة (?:شديدة )?(?:في )?التنفس",
        r"مش قادر (?:ا|أ)?تنفس",
        r"مش قادر (?:ا|أ)?خد نفس",
        r"لا أستطيع التنفس",
        r"مش عارف أتنفس",
        r"(?:حاسس|حاسة|بحس|حسيت) (?:ب(?:إ|ا)?ني )?(?:باختنق|بختنق|مخنوق)",
        r"(?:باختنق|بختنق|اختناق)",
        r"نفسي (?:مخنوق|قاطع)",
    ],
    "consciousness": [
        r"unconscious",
        r"loss of consciousness",
        r"faint(?:ed|ing)?",
        r"فقد(?:ان)? الوعي",
        r"مغمى عليه",
        r"أغمي علي(?:ا|ه)",
        r"فقدت الوعي",
    ],
    "stroke": [
        r"face droop",
        r"slurred speech",
        r"cannot speak clearly",
        r"one side (?:is |feels )?weak",
        r"one.side weakness",
        r"اعوجاج الوجه",
        r"ثقل الكلام",
        r"ضعف مفاجئ",
        r"تنميل مفاجئ",
        r"خدر مفاجئ",
        r"مش قادر (?:ا|أ)?تكلم",
        r"مش عارف (?:ا|أ)?تكلم",
    ],
    "bleeding": [
        r"severe bleeding",
        r"won't stop bleeding",
        r"vomiting blood",
        r"black stool",
        r"نزيف (?:شديد|لا يتوقف)",
        r"ترجيع دم",
        r"قيء دم",
        r"براز (?:أسود|اسود)",
    ],
    "severe_allergy": [
        r"anaphylaxis",
        r"swollen (?:tongue|lips|throat)",
        r"تورم (?:اللسان|الشفايف|الشفتين|الحلق)",
        r"حساسية شديدة",
    ],
    "self_harm": [r"kill myself", r"suicid", r"أنتحر", r"اقتل نفسي"],
}

MEDICATION_CHANGE_PATTERNS = [
    r"stop (?:my )?(?:medicine|medication|drug)",
    r"change (?:my )?dose",
    r"increase (?:my )?dose",
    r"decrease (?:my )?dose",
    r"أوقف (?:الدواء|دوائي)",
    r"أزيد (?:ال)?جرعة",
    r"أقلل (?:ال)?جرعة",
    r"أغير (?:ال)?جرعة",
    r"\b(?:stop|increase|decrease|change)\b.{0,30}\b(?:metformin|lisinopril|insulin|medicine|medication|drug|dose)\b",
]

OUT_OF_SCOPE_PATTERNS = [
    r"legal advice",
    r"investment advice",
    r"write (?:malware|a virus)",
    r"استشارة قانونية",
    r"استثمار",
]

UNSUPPORTED_CONDITION_TERMS = {
    "الربو": [r"asthma", r"الربو", r"ربو"],
    "مرض الكلى": [r"chronic kidney disease", r"kidney disease", r"kidney failure", r"مرض الكل[ىي]", r"فشل كلوي"],
    "مرض القلب": [r"heart failure", r"heart disease", r"cardiovascular disease", r"قصور القلب", r"مرض القلب"],
    "السرطان": [r"cancer", r"سرطان"],
    "أمراض الكبد": [r"liver disease", r"مرض الكبد", r"أمراض الكبد"],
    "الغدة الدرقية": [r"thyroid", r"الغدة الدرقية"],
    "الصرع": [r"epilepsy", r"صرع"],
    "الحمل": [r"pregnancy", r"حامل", r"الحمل"],
}


@dataclass(slots=True)
class SafetyResult:
    classification: str
    matched_rules: list[str]
    emergency: bool = False


def unsupported_condition_mentions(text: str) -> list[str]:
    normalized = " ".join(text.lower().split())
    return [
        label
        for label, patterns in UNSUPPORTED_CONDITION_TERMS.items()
        if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns)
    ]


def classify_safety(text: str, severity: int | None = None) -> SafetyResult:
    normalized = " ".join(text.lower().split())
    emergency_matches: list[str] = []
    for label, patterns in EMERGENCY_PATTERNS.items():
        if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns):
            emergency_matches.append(label)
    if emergency_matches or (severity is not None and severity >= 9):
        return SafetyResult("POSSIBLE_EMERGENCY", emergency_matches or ["severity_9_or_10"], True)
    medication = [pattern for pattern in MEDICATION_CHANGE_PATTERNS if re.search(pattern, normalized, re.IGNORECASE)]
    if medication:
        return SafetyResult("CAUTION", ["medication_change_request"])
    unsupported_conditions = unsupported_condition_mentions(normalized)
    if unsupported_conditions:
        return SafetyResult("UNSUPPORTED_CONDITION", unsupported_conditions)
    if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in OUT_OF_SCOPE_PATTERNS):
        return SafetyResult("OUT_OF_SCOPE", ["non_medical_scope"])
    return SafetyResult("ALLOWED", [])


def emergency_response() -> dict:
    return {
        "summary": "قد تكون هذه الأعراض حالة طارئة. اتصل بخدمات الطوارئ المحلية الآن، ولا تنتظر رد المحادثة.",
        "recommendation_status": "not_recommended",
        "conditions_considered": [],
        "suggested_quantity": None,
        "warnings": [
            "إذا كنت في مصر فاتصل بالإسعاف على 123، أو استخدم رقم الطوارئ المحلي في بلدك.",
            "لا تقد السيارة بنفسك. اطلب من شخص قريب البقاء معك إن أمكن.",
        ],
        "evidence_strength": "insufficient",
        "citations": [],
        "needs_professional_attention": True,
        "emergency": True,
        "safety_classification": "POSSIBLE_EMERGENCY",
        "evidence": [],
    }


def insufficient_evidence_response(conditions: list[str] | None = None) -> dict:
    return {
        "summary": "لا توجد معلومات موثوقة كافية في المصادر المتاحة لإعطاء توصية آمنة حول هذا السؤال.",
        "recommendation_status": "insufficient_evidence",
        "conditions_considered": [
            {"condition": condition, "assessment": "لم تتوفر أدلة مسترجعة كافية لهذه الحالة."}
            for condition in (conditions or [])
        ],
        "suggested_quantity": None,
        "warnings": ["أعد صياغة السؤال أو استشر طبيبك أو الصيدلي للحصول على نصيحة شخصية."],
        "evidence_strength": "insufficient",
        "citations": [],
        "needs_professional_attention": False,
        "emergency": False,
        "safety_classification": "ALLOWED",
        "evidence": [],
    }


def unsupported_condition_response(conditions: list[str]) -> dict:
    names = "، ".join(dict.fromkeys(conditions)) or "هذه الحالة"
    return {
        "summary": (
            f"أعتذر، لا تتوفر لدى عافيتي معلومات موثقة عن {names}. "
            "يدعم النظام حاليًا ارتفاع ضغط الدم والسكري من النوع الثاني فقط."
        ),
        "recommendation_status": "insufficient_evidence",
        "conditions_considered": [],
        "suggested_quantity": None,
        "warnings": [
            "للحصول على إرشاد عن هذه الحالة، يُفضّل الرجوع إلى الطبيب أو مصدر طبي مختص بها."
        ],
        "evidence_strength": "insufficient",
        "citations": [],
        "needs_professional_attention": False,
        "emergency": False,
        "safety_classification": "UNSUPPORTED_CONDITION",
        "evidence": [],
    }
