from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import Settings  # noqa: E402
from app.core.safety import classify_safety  # noqa: E402
from app.rag.bm25 import BM25Index  # noqa: E402
from app.rag.hybrid_search import HybridRetriever, rerank  # noqa: E402
from app.rag.query_analysis import analyze_query, rewrite_queries  # noqa: E402
from app.rag.vector_store import LocalVectorStore  # noqa: E402
from app.services.ollama_service import OllamaError, OllamaService  # noqa: E402
from app.services.rag_service import RAGService  # noqa: E402
from metrics import mean, metric_summary  # noqa: E402


DATA_REQUIRED = "NOT EVALUATED — DATA REQUIRED"
GENERATION_REQUIRED = "NOT EVALUATED — RUN WITH --full"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_judgments(payload: dict, question_ids: set[str]) -> None:
    if payload.get("label_tier") not in {"provisional", "official"}:
        raise ValueError("judgments.label_tier must be 'provisional' or 'official'")
    if payload.get("label_tier") == "official" and not payload.get("clinical_adjudication"):
        raise ValueError("official judgments must set clinical_adjudication=true")
    judgments = payload.get("questions")
    if not isinstance(judgments, dict) or not judgments:
        raise ValueError("judgments.questions must be a non-empty object")
    unknown = sorted(set(judgments) - question_ids)
    if unknown:
        raise ValueError(f"judgments reference unknown question IDs: {', '.join(unknown)}")
    for question_id, judgment in judgments.items():
        passages = judgment.get("relevant_passages", [])
        chunk_ids = judgment.get("relevant_chunk_ids", [])
        if not passages and not chunk_ids:
            raise ValueError(f"{question_id} has no relevant passages or chunks")
        for passage in passages:
            if not passage.get("source_filename") or not passage.get("pages"):
                raise ValueError(f"{question_id} contains an incomplete relevant passage")
            if any(not isinstance(page, int) or page <= 0 for page in passage["pages"]):
                raise ValueError(f"{question_id} contains an invalid page number")


def relevant_units(judgment: dict) -> set[tuple[str, str, int | str]]:
    units: set[tuple[str, str, int | str]] = set()
    for passage in judgment.get("relevant_passages", []):
        for page in passage["pages"]:
            units.add(("page", passage["source_filename"], int(page)))
    for chunk_id in judgment.get("relevant_chunk_ids", []):
        units.add(("chunk", "", chunk_id))
    return units


def matching_units(result: dict, judgment: dict) -> set[tuple[str, str, int | str]]:
    metadata = result.get("metadata", {})
    matches: set[tuple[str, str, int | str]] = set()
    chunk_id = metadata.get("chunk_id")
    if chunk_id in judgment.get("relevant_chunk_ids", []):
        matches.add(("chunk", "", chunk_id))
    filename = metadata.get("source_filename")
    page = metadata.get("page_number")
    for passage in judgment.get("relevant_passages", []):
        if filename == passage.get("source_filename") and page in passage.get("pages", []):
            matches.add(("page", filename, int(page)))
    return matches


def score_ranking(results: list[dict], judgment: dict) -> dict:
    labels = [bool(matching_units(result, judgment)) for result in results]
    expected = relevant_units(judgment)
    covered: set[tuple[str, str, int | str]] = set()
    for result in results[:5]:
        covered.update(matching_units(result, judgment))
    first_relevant = next((rank for rank, value in enumerate(labels, start=1) if value), None)
    return {
        "precision_at_3": sum(labels[:3]) / 3,
        "precision_at_5": sum(labels[:5]) / 5,
        "recall_at_5": len(covered) / len(expected) if expected else 0.0,
        "reciprocal_rank": 1.0 / first_relevant if first_relevant else 0.0,
        "relevant_at_5": sum(labels[:5]),
        "relevant_units_covered_at_5": len(covered),
        "relevant_units_total": len(expected),
    }


def aggregate_strategy(per_question: list[dict]) -> dict:
    return {
        "precision_at_3": metric_summary([item["precision_at_3"] for item in per_question]),
        "precision_at_5": metric_summary([item["precision_at_5"] for item in per_question]),
        "recall_at_5": metric_summary([item["recall_at_5"] for item in per_question]),
        "mrr": metric_summary([item["reciprocal_rank"] for item in per_question]),
        "average_retrieval_latency_ms": metric_summary(
            [item["retrieval_latency_ms"] for item in per_question], digits=2
        ),
        "questions": len(per_question),
        "per_question": per_question,
    }


async def evaluate_retrieval(
    settings: Settings, questions: list[dict], judgment_payload: dict
) -> dict:
    judgments = judgment_payload["questions"]
    judged = [question for question in questions if question["id"] in judgments]
    if not judged:
        return {"status": DATA_REQUIRED, "reason": "No relevance judgments exist."}

    bm25 = BM25Index(settings.data_dir / "index" / "chunks.json")
    store = LocalVectorStore(settings.qdrant_path, settings.qdrant_collection)
    dense_available = store.count() > 0
    lexical_available = bool(bm25.chunks)
    if not lexical_available and not dense_available:
        store.close()
        return {"status": DATA_REQUIRED, "reason": "The guideline index is empty."}

    ollama = OllamaService(settings)
    retriever = HybridRetriever(store, bm25, ollama)
    strategies = ["bm25"] if lexical_available else []
    if dense_available:
        strategies.insert(0, "dense")
        strategies.append("hybrid")

    report: dict[str, dict] = {}
    ranked_cache: dict[str, list[dict]] = {}
    for strategy in strategies:
        per_question: list[dict] = []
        for question_index, question in enumerate(judged):
            analysis = analyze_query(
                question["question"], question.get("profile_conditions", [])
            )
            queries = rewrite_queries(question["question"], analysis)
            results, timings = await retriever.retrieve(
                queries,
                analysis["conditions"],
                candidate_k=15,
                strategy=strategy,
                embedding_keep_alive=(
                    0 if question_index == len(judged) - 1 else "10m"
                ),
            )
            if strategy == "hybrid":
                results, rerank_latency = rerank(" ".join(queries), results, 15)
            else:
                rerank_latency = 0.0
            scored = score_ranking(results, judgments[question["id"]])
            per_question.append(
                {
                    "id": question["id"],
                    **{key: round(value, 4) for key, value in scored.items()},
                    "retrieval_latency_ms": round(
                        timings["retrieval_latency_ms"] + rerank_latency, 2
                    ),
                    "top_5": [
                        {
                            "chunk_id": item["metadata"].get("chunk_id"),
                            "source_filename": item["metadata"].get("source_filename"),
                            "page": item["metadata"].get("page_number"),
                            "relevant": bool(
                                matching_units(item, judgments[question["id"]])
                            ),
                        }
                        for item in results[:5]
                    ],
                }
            )
            if strategy == "hybrid" or (not dense_available and strategy == "bm25"):
                ranked_cache[question["id"]] = results
        report[strategy] = aggregate_strategy(per_question)

    primary_strategy = "hybrid" if "hybrid" in report else "bm25"
    top_k_comparison: dict[str, dict] = {}
    for k in (3, 5, 10, 15):
        precision_values: list[float] = []
        recall_values: list[float] = []
        for question in judged:
            results = ranked_cache.get(question["id"], [])
            judgment = judgments[question["id"]]
            labels = [bool(matching_units(item, judgment)) for item in results]
            covered: set[tuple[str, str, int | str]] = set()
            for item in results[:k]:
                covered.update(matching_units(item, judgment))
            precision_values.append(sum(labels[:k]) / k)
            recall_values.append(len(covered) / len(relevant_units(judgment)))
        top_k_comparison[str(k)] = {
            "precision": metric_summary(precision_values),
            "recall": metric_summary(recall_values),
        }

    index_status = {
        "bm25_chunks": len(bm25.chunks),
        "vector_chunks": store.count(),
        "dense_available": dense_available,
    }
    store.close()
    return {
        "status": "evaluated",
        "label_tier": judgment_payload["label_tier"],
        "judged_questions": len(judged),
        "primary_strategy": primary_strategy,
        "index": index_status,
        "strategies": report,
        "top_k_comparison": top_k_comparison,
    }


async def evaluate_grounding(
    settings: Settings, questions: list[dict], judgment_payload: dict
) -> dict:
    bm25 = BM25Index(settings.data_dir / "index" / "chunks.json")
    if not bm25.chunks:
        return {"status": DATA_REQUIRED, "reason": "The guideline index is empty."}
    chunks_by_id = {
        item["metadata"]["chunk_id"]: item for item in bm25.chunks
    }
    judgments = judgment_payload["questions"]
    eligible = [question for question in questions if question["id"] in judgments]
    rag = RAGService(settings)
    citation_labels: list[float] = []
    structural_labels: list[float] = []
    unsupported_labels: list[float] = []
    claim_coverage_labels: list[float] = []
    generation_latencies: list[float] = []
    end_to_end_latencies: list[float] = []
    cases: list[dict] = []
    try:
        for question in eligible:
            answer, trace = await rag.answer(
                question["question"], question.get("profile_conditions", [])
            )
            judgment = judgments[question["id"]]
            correct_citations = 0
            citations = answer.get("citations", [])
            for citation in citations:
                chunk = chunks_by_id.get(citation.get("chunk_id"))
                correct = bool(chunk and matching_units(chunk, judgment))
                citation_labels.append(float(correct))
                correct_citations += int(correct)
            validation = trace.get("citation_validation", {})
            for detail in validation.get("details", []):
                structural_labels.append(float(bool(detail.get("valid"))))

            claims = trace.get("claims", [])
            for claim in claims:
                if claim.get("status") == "NOT_EVALUATED_CROSS_LANGUAGE":
                    continue
                unsupported = claim.get("status") == "UNSUPPORTED"
                unsupported_labels.append(float(unsupported))
                claim_coverage_labels.append(float(not unsupported))

            latency = trace.get("latency", {})
            if isinstance(latency.get("generation_latency_ms"), (int, float)):
                generation_latencies.append(float(latency["generation_latency_ms"]))
            if isinstance(latency.get("end_to_end_ms"), (int, float)):
                end_to_end_latencies.append(float(latency["end_to_end_ms"]))
            cases.append(
                {
                    "id": question["id"],
                    "recommendation_status": answer.get("recommendation_status"),
                    "citations": len(citations),
                    "relevant_citations": correct_citations,
                    "claims": len(claims),
                    "unsupported_claims": sum(
                        claim.get("status") == "UNSUPPORTED" for claim in claims
                    ),
                    "cross_language_claims_not_evaluated": sum(
                        claim.get("status") == "NOT_EVALUATED_CROSS_LANGUAGE"
                        for claim in claims
                    ),
                    "generation_error": trace.get("generation_error"),
                    "end_to_end_ms": latency.get("end_to_end_ms"),
                }
            )
    finally:
        rag.vectors.close()

    return {
        "status": "evaluated",
        "label_tier": judgment_payload["label_tier"],
        "method": {
            "citation_accuracy": "Citation points to a retrieved chunk on a page labeled relevant for the question.",
            "structural_citation_validity": "Citation metadata matches a retrieved chunk and source.",
            "unsupported_claim_rate": "Conservative same-language lexical-support proxy; cross-language claims are excluded and clinician entailment review is still required.",
        },
        "citation_accuracy": metric_summary(citation_labels),
        "structural_citation_validity": metric_summary(structural_labels),
        "citation_coverage": metric_summary(claim_coverage_labels),
        "unsupported_claim_rate": metric_summary(unsupported_labels),
        "generation_latency_ms": metric_summary(generation_latencies, digits=2),
        "end_to_end_latency_ms": metric_summary(end_to_end_latencies, digits=2),
        "questions": len(eligible),
        "cases": cases,
    }


async def main_async(
    full: bool = False,
    judgments_path: Path | None = None,
    output_path: Path | None = None,
    grounding_only: bool = False,
) -> dict:
    settings = Settings.from_env()
    questions = load_json(ROOT / "evaluation" / "questions.json")
    judgment_payload = load_json(
        judgments_path or ROOT / "evaluation" / "judgments.json"
    )
    validate_judgments(judgment_payload, {item["id"] for item in questions})

    safety_cases = [item for item in questions if item.get("expected_safety")]
    safety_results = []
    for item in safety_cases:
        actual = classify_safety(item["question"]).classification
        safety_results.append(
            {
                "id": item["id"],
                "expected": item["expected_safety"],
                "actual": actual,
                "passed": actual == item["expected_safety"],
            }
        )

    ollama = OllamaService(settings)
    started = time.perf_counter()
    try:
        models = await ollama.models()
        ollama_result = {
            "status": "ready",
            "models": models,
            "tags_latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }
    except OllamaError as exc:
        ollama_result = {"status": "unavailable", "error": str(exc)}

    existing_output = output_path or ROOT / "evaluation" / "reports" / "latest.json"
    if grounding_only:
        try:
            retrieval = load_json(existing_output)["retrieval"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
            raise ValueError(
                "--grounding-only requires an existing report with retrieval results"
            ) from exc
        if retrieval.get("status") != "evaluated":
            raise ValueError("existing retrieval report is not evaluated")
    else:
        retrieval = await evaluate_retrieval(settings, questions, judgment_payload)
    grounding = (
        await evaluate_grounding(settings, questions, judgment_payload)
        if full
        else {"status": GENERATION_REQUIRED}
    )
    official = judgment_payload["label_tier"] == "official"
    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "evaluation_status": (
            "OFFICIAL" if official else "PROVISIONAL — REQUIRES CLINICIAN ADJUDICATION"
        ),
        "official_metrics_status": (
            "evaluated"
            if official
            else "DATA REQUIRED — independent clinician relevance and claim adjudication"
        ),
        "dataset": {
            "questions": len(questions),
            "judged_questions": len(judgment_payload["questions"]),
            "version": judgment_payload["dataset_version"],
            "label_tier": judgment_payload["label_tier"],
            "clinical_adjudication": judgment_payload["clinical_adjudication"],
            "annotation_method": judgment_payload["annotation_method"],
        },
        "safety": {
            "passed": sum(item["passed"] for item in safety_results),
            "total": len(safety_results),
            "cases": safety_results,
        },
        "ollama": ollama_result,
        "retrieval": retrieval,
        "grounding": grounding,
    }
    output = existing_output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the reproducible Afiyati safety, retrieval, and grounding evaluation"
    )
    parser.add_argument(
        "--full", action="store_true", help="Also generate answers and score grounding proxies"
    )
    parser.add_argument(
        "--grounding-only",
        action="store_true",
        help="Reuse retrieval results from the output report and rerun grounding only",
    )
    parser.add_argument("--judgments", type=Path, help="Override the qrels JSON file")
    parser.add_argument("--output", type=Path, help="Override the report JSON path")
    args = parser.parse_args()
    try:
        report = asyncio.run(
            main_async(
                args.full or args.grounding_only,
                args.judgments,
                args.output,
                grounding_only=args.grounding_only,
            )
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"EVALUATION FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
