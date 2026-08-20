from __future__ import annotations

import json
import re
import time
import uuid
from collections import OrderedDict

from pydantic import ValidationError

from app.core.config import Settings
from app.core.safety import (
    classify_safety,
    emergency_response,
    insufficient_evidence_response,
    unsupported_condition_response,
)
from app.rag.bm25 import BM25Index
from app.rag.hybrid_search import HybridRetriever, rerank
from app.rag.query_analysis import analyze_query, rewrite_queries
from app.rag.vector_store import LocalVectorStore
from app.schemas.api import AfiyatiAnswer
from app.services.citation_service import citation_from_chunk, validate_citations, verify_claims
from app.services.contradiction_service import detect_guideline_differences
from app.services.ollama_service import OllamaError, OllamaService


GENERATION_SCHEMA = {
    "type": "object",
    "required": [
        "summary",
        "recommendation_status",
        "conditions_considered",
        "warnings",
        "evidence_strength",
        "needs_professional_attention",
        "emergency",
        "cited_chunk_ids",
    ],
    "properties": {
        "summary": {"type": "string"},
        "recommendation_status": {
            "type": "string",
            "enum": ["suitable", "caution", "not_recommended", "insufficient_evidence"],
        },
        "conditions_considered": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["condition", "assessment"],
                "properties": {"condition": {"type": "string"}, "assessment": {"type": "string"}},
            },
        },
        "suggested_quantity": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "required": ["value", "basis", "certainty"],
                    "properties": {
                        "value": {"type": "string"},
                        "basis": {"type": "string"},
                        "certainty": {"type": "string"},
                    },
                },
            ]
        },
        "warnings": {"type": "array", "items": {"type": "string"}},
        "evidence_strength": {"type": "string", "enum": ["strong", "moderate", "limited", "insufficient"]},
        "needs_professional_attention": {"type": "boolean"},
        "emergency": {"type": "boolean"},
        "cited_chunk_ids": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
        },
    },
}


def validate_generated_summary(summary: str, question: str) -> None:
    first_question_line = question.splitlines()[0]

    def normalize(value: str) -> str:
        return " ".join(re.sub(r"[^\w\u0600-\u06ff]+", " ", value.lower()).split())

    normalized_summary = normalize(summary)
    normalized_question = normalize(first_question_line)
    if not normalized_summary or normalized_summary == normalized_question:
        raise ValueError("Generated summary repeated the question")
    if re.search(r"[\u0600-\u06ff]", first_question_line) and not re.search(
        r"[\u0600-\u06ff]", summary
    ):
        raise ValueError("Generated summary did not preserve the Arabic language")


FALLBACK_GUIDANCE = {
    "hypertension": {
        "citation": {
            "document": "Hypertension in adults: diagnosis and management (NG136)",
            "organization": "National Institute for Health and Care Excellence (NICE)",
            "section": "Lifestyle advice: 1.4.2, 1.4.4 and 1.4.5",
            "page": None,
            "chunk_id": "fallback-nice-ng136-lifestyle",
            "source_url": "https://www.nice.org.uk/guidance/ng136",
        },
        "general": "لإدارة ضغط الدم، توصي NICE بنمط غذائي صحي ونشاط بدني منتظم، مع تقليل الصوديوم وتجنب الإفراط في القهوة ومنتجات الكافيين.",
        "coffee": "بالنسبة للقهوة والكافيين، توصي NICE بتجنب الإفراط في استهلاك القهوة ومنتجات الكافيين مع ارتفاع ضغط الدم.",
        "sodium": "توصي NICE بأن يكون مدخول الصوديوم الغذائي منخفضًا للمساعدة في خفض ضغط الدم؛ لذلك يُفضّل تقليل الملح المضاف والأطعمة عالية الصوديوم.",
        "exercise": "توضح NICE أن النمط الغذائي الصحي والرياضة المنتظمة يمكن أن يسهما في خفض ضغط الدم.",
    },
    "type_2_diabetes": {
        "citation": {
            "document": "Type 2 diabetes in adults: management (NG28)",
            "organization": "National Institute for Health and Care Excellence (NICE)",
            "section": "Dietary advice: 1.3.3, 1.3.5 and 1.3.6",
            "page": None,
            "chunk_id": "fallback-nice-ng28-dietary",
            "source_url": "https://www.nice.org.uk/guidance/ng28/chapter/Dietary-advice-and-interventions",
        },
        "general": "توصي NICE لسكري النوع الثاني بنمط أكل يعتمد على مصادر كربوهيدرات أعلى أليافًا وأقل في المؤشر الجلايسيمي، مثل الخضراوات والفواكه والحبوب الكاملة والبقوليات، مع جعل الكربوهيدرات ونمط الوجبات مناسبين لخطة الشخص العلاجية.",
        "coffee": "في السكري من النوع الثاني، توصي NICE بأن تكون اختيارات الطعام والشراب ونمط الوجبات جزءًا من خطة شخصية تراعي الكربوهيدرات والأدوية؛ راجع كمية السكر أو الإضافات في المشروب.",
        "sodium": "في السكري من النوع الثاني، توصي NICE بخطة غذائية شخصية ضمن نمط أكل صحي؛ راجع الصوديوم الظاهر في بيانات الطعام، خاصة إذا كان لديك أيضًا ضغط مرتفع.",
        "exercise": "توصي NICE بدمج النشاط البدني في خطة إدارة السكري الشخصية إلى جانب التغذية والعلاج الموصوف.",
    },
}


def grounded_fallback_response(
    conditions: list[str],
    topic: str,
    selected: list[dict] | None = None,
    food_context: dict | None = None,
) -> dict:
    active_conditions = [condition for condition in conditions if condition in FALLBACK_GUIDANCE]
    if active_conditions:
        summaries = [
            FALLBACK_GUIDANCE[condition].get(topic, FALLBACK_GUIDANCE[condition]["general"])
            for condition in active_conditions
        ]
        return {
            "summary": " ".join(dict.fromkeys(summaries)),
            "recommendation_status": "caution",
            "conditions_considered": [
                {
                    "condition": condition,
                    "assessment": FALLBACK_GUIDANCE[condition].get(
                        topic, FALLBACK_GUIDANCE[condition]["general"]
                    ),
                }
                for condition in active_conditions
            ],
            "suggested_quantity": None,
            "warnings": ["هذه معلومات عامة موثقة ولا تغيّر العلاج أو جرعات الدواء الموصوفة."],
            "evidence_strength": "limited",
            "citations": [FALLBACK_GUIDANCE[condition]["citation"] for condition in active_conditions],
            "needs_professional_attention": False,
            "emergency": False,
            "safety_classification": "ALLOWED",
            "evidence": _fallback_evidence(selected or []),
            "grounded_fallback": True,
        }
    if food_context and (food_context.get("items") or food_context.get("entries")):
        return {
            "summary": "ستجد القيم الغذائية والمصدر الرسمي للطعام أو المشروب الذي ذكرتَه. ولتقييم أثر صحي مخصص، اذكر إن كان السؤال يتعلق بضغط الدم أو السكري من النوع الثاني.",
            "recommendation_status": "suitable",
            "conditions_considered": [],
            "suggested_quantity": None,
            "warnings": [],
            "evidence_strength": "limited",
            "citations": [],
            "needs_professional_attention": False,
            "emergency": False,
            "safety_classification": "ALLOWED",
            "evidence": _fallback_evidence(selected or []),
            "grounded_fallback": True,
        }
    return insufficient_evidence_response(active_conditions)


def _fallback_evidence(selected: list[dict]) -> list[dict]:
    return [
        {
            "rank": index,
            "document": item["metadata"].get("guideline_title"),
            "organization": item["metadata"].get("organization"),
            "section": item["metadata"].get("section_title"),
            "page": item["metadata"].get("page_number"),
            "chunk_id": item["metadata"]["chunk_id"],
            "relevance": item.get("rerank_score"),
            "excerpt": item["text"][:500],
        }
        for index, item in enumerate(selected, start=1)
    ]


class RAGService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.ollama = OllamaService(settings)
        self.vectors = LocalVectorStore(settings.qdrant_path, settings.qdrant_collection)
        self.bm25 = BM25Index(settings.data_dir / "index" / "chunks.json")
        self.retriever = HybridRetriever(self.vectors, self.bm25, self.ollama)
        self.traces: OrderedDict[str, dict] = OrderedDict()

    def status(self) -> dict:
        return {
            "collection": self.settings.qdrant_collection,
            "vector_store_available": self.vectors.available,
            "vector_store_error": self.vectors.error,
            "indexed_chunks": self.vectors.count(),
            "bm25_chunks": len(self.bm25.chunks),
            "generation_model": self.settings.generation_model,
            "embedding_model": self.settings.embedding_model,
            "chunk_strategy": "section-aware + parent-child",
            "child_tokens": self.settings.child_tokens,
            "parent_tokens": self.settings.parent_tokens,
            "overlap": self.settings.chunk_overlap,
            "top_k": self.settings.top_k,
        }

    def _remember_trace(self, trace: dict) -> str:
        trace_id = str(uuid.uuid4())
        self.traces[trace_id] = trace
        while len(self.traces) > 100:
            self.traces.popitem(last=False)
        return trace_id

    def get_trace(self, trace_id: str) -> dict | None:
        return self.traces.get(trace_id)

    async def answer(
        self,
        question: str,
        conditions: list[str],
        mode: str = "chat",
        food_context: dict | None = None,
        user_context: dict | None = None,
        conversation_context: list[dict] | None = None,
    ) -> tuple[dict, dict]:
        total_started = time.perf_counter()
        food_context = food_context or {"items": [], "notices": [], "matched_terms": []}
        user_context = user_context or {}
        conversation_context = conversation_context or []
        safety = classify_safety(question)
        if safety.emergency:
            answer = emergency_response()
            trace = {
                "original_query": question,
                "safety": {
                    "classification": safety.classification,
                    "matched_rules": safety.matched_rules,
                    "emergency": safety.emergency,
                },
                "claims": [],
                "profile_context_fields": [key for key, value in user_context.items() if value],
                "latency": {},
            }
            answer["trace_id"] = self._remember_trace(trace)
            return answer, trace
        if safety.classification == "OUT_OF_SCOPE":
            answer = insufficient_evidence_response(conditions)
            answer["safety_classification"] = "OUT_OF_SCOPE"
            trace = {
                "original_query": question,
                "safety": {
                    "classification": safety.classification,
                    "matched_rules": safety.matched_rules,
                    "emergency": safety.emergency,
                },
                "claims": [],
                "profile_context_fields": [key for key, value in user_context.items() if value],
                "latency": {},
            }
            answer["trace_id"] = self._remember_trace(trace)
            return answer, trace
        if safety.classification == "UNSUPPORTED_CONDITION":
            answer = unsupported_condition_response(safety.matched_rules)
            trace = {
                "original_query": question,
                "safety": {
                    "classification": safety.classification,
                    "matched_rules": safety.matched_rules,
                    "emergency": False,
                },
                "claims": [],
                "profile_context_fields": [key for key, value in user_context.items() if value],
                "latency": {},
            }
            answer["trace_id"] = self._remember_trace(trace)
            return answer, trace

        analysis = analyze_query(question, conditions, mode)
        rewritten = rewrite_queries(question, analysis)
        candidates, retrieval_metrics = await self.retriever.retrieve(
            rewritten, analysis["conditions"], candidate_k=15, strategy="hybrid"
        )
        selected, rerank_latency = rerank(" ".join(rewritten), candidates, self.settings.top_k)
        guideline_differences = detect_guideline_differences(selected)
        if not selected:
            answer = grounded_fallback_response(
                analysis["conditions"], analysis["topic"], food_context=food_context
            )
            answer["safety_classification"] = safety.classification
            trace = {
                "original_query": question,
                "rewritten_queries": rewritten,
                "analysis": analysis,
                "retrieval": retrieval_metrics,
                "retrieved_chunks": [],
                "reranked_chunks": [],
                "claims": [],
                "citation_validation": {"valid": 0, "total": 0, "details": []},
                "food_lookup": food_context,
                "grounded_fallback": bool(answer.get("grounded_fallback")),
                "profile_context_fields": [key for key, value in user_context.items() if value],
                "conversation_turns_used": len(conversation_context),
                "latency": {"end_to_end_ms": round((time.perf_counter() - total_started) * 1000, 2)},
            }
            answer["trace_id"] = self._remember_trace(trace)
            return answer, trace

        evidence_text = "\n\n".join(
            f"CHUNK {item['metadata']['chunk_id']}\n"
            f"SOURCE: {item['metadata'].get('guideline_title')} | {item['metadata'].get('organization')} | "
            f"PAGE {item['metadata'].get('page_number')} | SECTION {item['metadata'].get('section_title')}\n"
            f"{item['text']}"
            for item in selected
        )
        food_matches = [
            {
                "requested_name": item.get("requested_name"),
                "matched_name": item.get("matched_name"),
                "category": item.get("category"),
            }
            for item in food_context.get("items", [])
        ]
        mode_guidance = {
            "chat": (
                "Handle conversational Arabic, including common Egyptian phrasing and short follow-ups. "
                "Use the recent conversation only to resolve what the user means by a reference such as “this” or “what about it”. "
                "For a non-urgent symptom mention, do not diagnose; invite the user to record duration and severity in symptom follow-up."
            ),
            "food": (
                "Focus on the named food or drink and its relationship to the registered conditions. "
                "If amount is relevant but absent, ask one direct follow-up question about the amount rather than guessing."
            ),
            "meal": (
                "Discuss only the confirmed meal ingredients and weights. If an ingredient is unclear, say what needs confirmation."
            ),
            "habit": (
                "Connect the described habit to the registered conditions only when the evidence supports that connection. "
                "Ask for frequency or duration only when it changes how the guidance should be interpreted."
            ),
            "symptom": (
                "Do not diagnose symptoms. Give calm next-step guidance and request duration, severity, and change over time when needed."
            ),
        }.get(mode, "")
        prompt = f"""You are Afiyati, an evidence-grounded chronic-disease lifestyle assistant.
Answer in Arabic when the user's question is Arabic; do not switch to English. Use only the evidence below.
Use a respectful, calm, professional tone. Answer the user's ordinary question directly before adding any caveat.
MODE-SPECIFIC BEHAVIOR: {mode_guidance}
Consider every registered condition. Use the first name naturally and briefly, without repeating it.
The summary must answer the question directly in clear Arabic; never repeat or paraphrase the question as the answer.
Interpret everyday Arabic wording, including Egyptian dialect and incomplete follow-up messages, before deciding that clarification is needed.
Do not diagnose, change doses, suggest stopping prescribed medicine, or invent quantities. If evidence is not
enough for a safe recommendation, set recommendation_status to insufficient_evidence. Preserve uncertainty.
Never invent a source, page, guideline, or URL. Return only JSON matching the supplied schema.
The matched food identities below come from separate official food databases. Their nutrition values are deliberately not
included in this prompt because the interface renders the exact API values separately. Never state, estimate, or
characterize calories, nutrients, caffeine, sodium, sugar, or other composition from model memory. Discuss only
clinical guidance explicitly supported by the guideline CHUNK identifiers. Do not derive a safe serving or threshold
from a food identity alone.
The profile is user-reported context, not medical evidence. Never infer a diagnosis, medicine, laboratory result,
or a safe dose from age, height, weight, or gender. Respect reported allergies and dietary restrictions; when a food
could contain an allergen, tell the user to verify ingredients and labels rather than claiming it is safe.
Recent conversation summaries may only resolve references or follow-up wording. They are not evidence and cannot
support a recommendation.
If the evidence contains a potential guideline difference, describe each source separately and do not invent consensus.
For every factual recommendation, include only the supporting CHUNK identifiers in cited_chunk_ids.
Use no more than 3 identifiers and do not cite background or irrelevant chunks. Do not state a confidence score,
relevance score, probability, or percentage to the user.

REGISTERED CONDITIONS: {json.dumps(analysis['conditions'], ensure_ascii=False)}
USER-REPORTED PROFILE CONTEXT: {json.dumps(user_context, ensure_ascii=False)}
RECENT CONVERSATION CONTEXT: {json.dumps(conversation_context, ensure_ascii=False)}
POTENTIAL GUIDELINE DIFFERENCES: {json.dumps(guideline_differences, ensure_ascii=False)}
OFFICIAL MATCHED FOOD IDENTITIES: {json.dumps(food_matches, ensure_ascii=False)}
QUESTION: {question}
EVIDENCE:
{evidence_text}
"""
        generation_latency = 0.0
        generation_error = None
        used_grounded_fallback = False
        try:
            raw_answer, generation_latency = await self.ollama.generate_json(prompt, GENERATION_SCHEMA)
            validate_generated_summary(str(raw_answer.get("summary", "")), question)
            selected_by_id = {item["metadata"]["chunk_id"]: item for item in selected}
            requested_ids = list(dict.fromkeys(raw_answer.pop("cited_chunk_ids", [])))
            cited_chunks = [selected_by_id[value] for value in requested_ids if value in selected_by_id]
            if raw_answer.get("recommendation_status") != "insufficient_evidence" and not cited_chunks:
                raise ValueError("Generated recommendation did not include a valid evidence citation")
            raw_answer["citations"] = [citation_from_chunk(item) for item in cited_chunks]
            raw_answer["safety_classification"] = safety.classification
            raw_answer["evidence"] = [
                {
                    "rank": index,
                    "document": item["metadata"].get("guideline_title"),
                    "organization": item["metadata"].get("organization"),
                    "section": item["metadata"].get("section_title"),
                    "page": item["metadata"].get("page_number"),
                    "chunk_id": item["metadata"]["chunk_id"],
                    "relevance": item.get("rerank_score"),
                    "excerpt": item["text"][:500],
                }
                for index, item in enumerate(selected, start=1)
            ]
            answer = AfiyatiAnswer.model_validate(raw_answer).model_dump()
            if answer["recommendation_status"] == "insufficient_evidence":
                answer = grounded_fallback_response(
                    analysis["conditions"], analysis["topic"], selected, food_context
                )
                used_grounded_fallback = True
        except OllamaError as exc:
            generation_error = str(exc)
            answer = grounded_fallback_response(
                analysis["conditions"], analysis["topic"], selected, food_context
            )
            used_grounded_fallback = True
        except (ValidationError, ValueError) as exc:
            generation_error = str(exc)
            answer = grounded_fallback_response(
                analysis["conditions"], analysis["topic"], selected, food_context
            )
            used_grounded_fallback = True

        claims = (
            verify_claims(answer, selected)
            if answer.get("citations") and not used_grounded_fallback
            else []
        )
        evaluable_claims = [
            item for item in claims if item["status"] != "NOT_EVALUATED_CROSS_LANGUAGE"
        ]
        if evaluable_claims and sum(
            item["status"] == "UNSUPPORTED" for item in evaluable_claims
        ) > len(evaluable_claims) / 2:
            answer = grounded_fallback_response(
                analysis["conditions"], analysis["topic"], selected, food_context
            )
            claims = []
            used_grounded_fallback = True
        evaluable_claims = [
            item for item in claims if item["status"] != "NOT_EVALUATED_CROSS_LANGUAGE"
        ]
        if analysis["conditions"] and not answer.get("citations"):
            answer["citations"] = [citation_from_chunk(item) for item in selected[:3]]
        citation_validation = (
            {"valid": len(answer.get("citations", [])), "total": len(answer.get("citations", [])), "details": []}
            if used_grounded_fallback
            else validate_citations(answer.get("citations", []), selected)
        )
        trace = {
            "original_query": question,
            "rewritten_queries": rewritten,
            "analysis": analysis,
            "safety": {"classification": safety.classification, "matched_rules": safety.matched_rules},
            "retrieval": retrieval_metrics,
            "retrieved_chunks": candidates,
            "reranked_chunks": selected,
            "generation_evidence": [item["metadata"]["chunk_id"] for item in selected],
            "claims": claims,
            "citation_validation": citation_validation,
            "potential_guideline_differences": guideline_differences,
            "food_lookup": food_context,
            "profile_context_fields": [key for key, value in user_context.items() if value],
            "conversation_turns_used": len(conversation_context),
            "citation_coverage": {
                "supported": sum(item["status"] == "SUPPORTED" for item in claims),
                "total": len(evaluable_claims),
                "not_evaluated_cross_language": len(claims) - len(evaluable_claims),
            },
            "generation_error": generation_error,
            "grounded_fallback": used_grounded_fallback,
            "latency": {
                **retrieval_metrics,
                "reranking_latency_ms": round(rerank_latency, 2),
                "generation_latency_ms": round(generation_latency, 2),
                "end_to_end_ms": round((time.perf_counter() - total_started) * 1000, 2),
            },
        }
        trace_id = self._remember_trace(trace)
        answer["trace_id"] = trace_id
        return answer, trace
