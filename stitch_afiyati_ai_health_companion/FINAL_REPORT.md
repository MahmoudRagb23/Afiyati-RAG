# Afiyati final engineering report

## Final status

Afiyati is a runnable Arabic-first local health-guideline RAG product with a
React interface, FastAPI backend, SQLite persistence, deterministic safety
controls, an official four-document guideline corpus, hybrid retrieval, grounded
generation, evidence traces, and a live benchmark dashboard.

The product is engineering-complete for local demonstration. Benchmark results
are explicitly provisional until independent clinicians adjudicate relevance
and claim support.

## Production corpus and retrieval

- NICE NG136 hypertension, NICE NG28 type 2 diabetes, KDIGO CKD 2024, and GINA
  2026 are registered with canonical metadata, source URLs, versions, and
  SHA-256 checksums.
- PDF parsing preserves exact page attribution.
- Chunks are page-bounded so a citation cannot silently span onto another page.
- 2,059 chunks are indexed in BM25 and local Qdrant.
- Arabic and mixed-language query analysis expands clinical retrieval vocabulary.
- Rewritten queries are embedded in a single request, eliminating repeated model
  loads within one user question.
- Runtime retrieval uses dense + BM25 RRF and lexical reranking with Top-K 5.

## Grounding and safety

- Generation is constrained to a JSON schema and source evidence.
- The model returns at most three supporting chunk IDs; the backend accepts only
  IDs present in the retrieved set and derives all displayed citation metadata.
- A recommendation without a valid retrieved citation is rejected safely.
- Same-language lexical claim screening cannot mislabel Arabic claims against
  English PDFs; those claims are marked for cross-language review.
- Emergency, medication-change, out-of-scope, and insufficient-evidence paths
  remain deterministic and visible.

## Measured provisional benchmark

On 17 page-judged questions:

- Precision@3: **0.4902** (95% CI 0.3529-0.6275).
- Precision@5: **0.4588** (95% CI 0.3294-0.5882).
- Recall@5: **0.6247** (95% CI 0.4643-0.7815).
- MRR: **0.6569** (95% CI 0.4902-0.8137).
- Citation accuracy: **0.7778** (95% CI 0.6389-0.8889).
- Structural citation validity: **1.0000**.
- Same-language unsupported-claim proxy: **0.0000** across 29 evaluable claims;
  six cross-language claims were excluded and flagged for review.
- Safety regression: **6/6**.

The Technical RAG Demo loads these values from `/api/rag/benchmark` rather than
hardcoding placeholders. It visually distinguishes provisional results from an
official clinician-adjudicated dataset.

## Verification

- Backend: **26 tests passed**.
- Frontend: production Vite build passed.
- Corpus: 4/4 PDFs validated; no checksum, parsing, manifest, version, or missing
  file errors.
- Dense and lexical indexes: 2,059/2,059 chunks.
- Full live grounding evaluation: 17/17 cases completed with no generation error.

## Remaining clinical/product work

- Two or more independent clinicians must label relevance and claim entailment,
  resolve disagreements, and freeze an official benchmark before clinical or
  publication claims are made.
- Cross-language entailment requires a validated multilingual NLI or human review
  workflow; lexical screening is intentionally not substituted.
- Meal image recognition remains a user-confirmed local demo adapter.
- Browser notifications require the web app to remain open; native background
  scheduling is outside this local web product.
- Browser screenshot QA should be repeated when an in-app or connected browser is
  available.

The machine-readable benchmark and full methodology are documented in
`evaluation/reports/latest.json`, `evaluation/README.md`, and
`EVALUATION_REPORT.md`.
