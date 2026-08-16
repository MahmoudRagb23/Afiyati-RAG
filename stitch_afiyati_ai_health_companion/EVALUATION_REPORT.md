# Afiyati evaluation report

Generated locally on 2026-08-16 (Africa/Cairo). This report separates measured
engineering results from clinical-validation claims.

## Status

**PROVISIONAL - REQUIRES INDEPENDENT CLINICIAN ADJUDICATION**

The source corpus consists of official guideline PDFs and the retrieval labels
identify exact relevant PDF pages. The 17 judged questions were reviewed for
engineering evaluation but were not independently adjudicated by clinicians.
These results are suitable for product development and hackathon demonstration;
they must not be described as an official clinical benchmark.

## Frozen evaluation assets

- 28 Arabic, English, and mixed-language questions.
- 17 questions with page-level provisional relevance judgments.
- Four official PDFs: NICE NG136, NICE NG28, KDIGO CKD 2024, and GINA 2026.
- 2,059 page-bounded chunks in both BM25 and Qdrant.
- SHA-256, manifest metadata, PDF parsing, version, and source validation passed.
- Embedding model: `qwen3-embedding:0.6b` (1,024 dimensions).
- Retrieval: dense + BM25 reciprocal-rank fusion + lexical reranking.
- Runtime Top-K: 5.

## Retrieval results

Metrics are macro-averaged over 17 judged questions. Intervals are deterministic
95% percentile bootstrap confidence intervals.

| Metric | Hybrid result | 95% CI |
|---|---:|---:|
| Precision@3 | **0.4902** | 0.3529-0.6275 |
| Precision@5 | **0.4588** | 0.3294-0.5882 |
| Recall@5 | **0.6247** | 0.4643-0.7815 |
| MRR | **0.6569** | 0.4902-0.8137 |

### Strategy comparison

| Strategy | Precision@3 | Precision@5 | Recall@5 | MRR | Mean retrieval latency |
|---|---:|---:|---:|---:|---:|
| Dense | 0.4902 | 0.4588 | 0.5882 | **0.6752** | 621.43 ms |
| BM25 | 0.3333 | 0.3294 | 0.5378 | 0.5657 | **36.04 ms** |
| Hybrid + reranking | **0.4902** | **0.4588** | **0.6247** | 0.6569 | 719.06 ms |

Hybrid remains the production default because it achieved the highest Recall@5
while matching dense precision. Dense achieved slightly higher MRR; this tradeoff
is retained in the machine-readable per-question audit rather than hidden.

## Grounding results

Seventeen live answers were generated through the production RAG pipeline.
Eight returned `suitable`; nine conservatively returned
`insufficient_evidence`. No generation error occurred.

| Metric | Result | 95% CI / notes |
|---|---:|---|
| Citation accuracy (page relevance) | **0.7778** | 0.6389-0.8889; 36 citations |
| Structural citation validity | **1.0000** | Every citation mapped to a retrieved chunk and source |
| Same-language claim coverage | **1.0000** | 29 evaluable claims |
| Unsupported-claim rate | **0.0000** | 0.0000-0.0000; lexical proxy only |

Citation accuracy measures whether a generated citation points to a chunk on a
page judged relevant for the question. It is not a clinician entailment score.
The unsupported-claim rate is a conservative same-language lexical proxy, not a
clinical factuality metric. Six Arabic-to-English evidence claims were explicitly
excluded from that denominator and marked for cross-language review rather than
being falsely labeled unsupported.

Selective citations are generated as constrained chunk IDs (maximum three),
validated against the retrieved set, and converted to source metadata by the
backend. A non-insufficient recommendation without a valid retrieved citation is
rejected safely.

## Safety and refusal

- Deterministic safety cases: **6/6 passed**.
- CAUTION medication-change cases: 2/2.
- OUT_OF_SCOPE cases: 1/1.
- POSSIBLE_EMERGENCY cases: 3/3.
- Empty-index refusal remains covered by the isolated API test suite.

These six cases are regression checks, not a clinical sensitivity or specificity
study. A larger clinician-reviewed safety dataset is still required.

## Latency

- Hybrid retrieval mean: **719.06 ms**.
- Generation mean: **56,959.73 ms**.
- End-to-end mean: **59,059.17 ms**.

The generation model runs partly on CPU on the reference 4 GB VRAM laptop. Query
rewrites are embedded in one batch, avoiding repeated model reloads within a
request. Corpus embeddings are cached by model and text hash for recoverable
re-ingestion.

## Automated verification

- Backend tests: **26 passed, 0 failed**.
- Frontend production build: passed.
- Guideline validation: 4 PDFs, 0 errors, 0 checksum failures.
- Ingestion: 4 documents, 2,059 BM25 chunks, 2,059 dense vectors.
- Browser screenshot QA could not be completed because the in-app browser was
  unavailable in this session; the compiled UI and API response are verified.

## Reproduction

```powershell
scripts\validate_guidelines.bat
scripts\ingest_guidelines.bat
scripts\evaluate_rag.bat
scripts\test_all.bat
```

The full JSON report, including confidence intervals, Top-K comparison, every
Top-5 ranking, and per-answer grounding audit, is stored at
`evaluation/reports/latest.json` and served by `/api/rag/benchmark`.

