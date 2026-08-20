# عافيتي — Afiyati

Afiyati is an Arabic-first, local AI assistant for understanding how food,
habits, meals, medications, and symptoms may relate to registered chronic
conditions. It is an evidence synthesizer, not an autonomous doctor. A fluent
answer is never treated as a safe answer: retrieval, citations, refusal, and
emergency escalation are visible product features.

The Stitch export remains in its original screen folders as the design
reference. The working React application and FastAPI backend now live directly
in this repository.

## What works

- Arabic RTL responsive landing, authentication, onboarding, dashboard, chat,
  evidence panel, meal flow, habits, symptoms, emergency view, medications,
  history, sources, settings, help, and technical RAG trace.
- Local scrypt password hashing, signed session tokens, SQLite profiles,
  conversations, medications, dose events, and symptom records.
- Profile-aware chat that uses only safe, user-reported profile fields plus
  summaries of the previous three questions for follow-up context. Profile and
  conversation context never count as medical evidence.
- Independent food-composition lookup across USDA FoodData Central and the UK
  CoFID 2021 dataset, with each source value and exact record shown separately.
- Recursive PDF validation and parsing with page preservation, repeated
  header/footer removal, section-aware parent/child chunks, and explicit
  manifest metadata.
- Ollama embeddings and `qwen3:4b` structured generation; Qdrant local mode;
  BM25; reciprocal-rank fusion; lexical fallback reranking; metadata-derived
  citations; structural citation validation; and claim screening.
- Deterministic safety classes: `ALLOWED`, `CAUTION`, `OUT_OF_SCOPE`, and
  `POSSIBLE_EMERGENCY`. Emergency triage works without login.
- A confirmed-ingredient meal workflow. Image recognition is a clearly labeled
  local demo fallback until a compatible local vision model is configured.

## Requirements

- Windows 10/11
- Python 3.12
- Node.js 20+
- Ollama at `http://127.0.0.1:11434`
- Recommended: RTX 3050 Laptop or better. Afiyati runs embedding and generation
  sequentially and asks Ollama to unload embedding models after each request.

No Docker or paid API key is required.

## Setup

From Explorer, run `scripts\setup.bat`, or in a terminal:

```powershell
scripts\setup.bat
```

Make a local configuration file if needed:

```powershell
Copy-Item .env.example .env
```

The current code reads environment variables from the process. The batch files
use the defaults in `.env.example`; set variables in the shell before launching
to override them.

## Ollama models

```powershell
ollama pull qwen3:4b
ollama pull qwen3-embedding:0.6b
ollama pull bge-m3
ollama pull nomic-embed-text
```

Optional reranker model present on the reference machine:

```powershell
ollama pull dengcao/Qwen3-Reranker-0.6B:Q8_0
```

The stable default uses deterministic lexical reranking. This avoids holding a
second language model in 4 GB VRAM; a model reranker can be added behind the
existing interface after it is benchmarked.

Generation defaults to a 4,096-token context and a 420-token structured answer
budget so the local 4B model remains practical on mixed CPU/GPU laptops. These
limits and the 180-second server timeout are configurable through `.env.example`.

## Start

Open two terminals:

```powershell
scripts\start_backend.bat
scripts\start_frontend.bat
```

Then open `http://127.0.0.1:5173`. API documentation is available locally at
`http://127.0.0.1:8000/docs`.

## Guideline library

The currently supported conditions are hypertension and type 2 diabetes. Their
production sources are NICE NG136 and NICE NG28. Other conditions remain
disabled in the interface until their full product and evidence support ships.

1. Put official current PDFs under `data/guidelines/<condition>/<organization>`.
2. Add authoritative metadata to `data/guidelines/manifest.json`.
3. Validate; fix every error before ingestion.
4. Ingest and restart the backend so its BM25 index reloads.

```powershell
scripts\validate_guidelines.bat
scripts\ingest_guidelines.bat
```

The validator reports unregistered/missing files, duplicate names and guideline
IDs, unknown folders/organizations, version/year gaps, current/archive
conflicts, empty files, and parsing failures. It never silently ingests invalid
content.

## Food and beverage data

Food and beverage questions are matched through the reviewed Arabic catalogue
in `data/foods/aliases.ar.json`. The catalogue currently covers 112 common
foods, beverages, and Egyptian mixed dishes. Nutrition composition is looked
up independently in two official databases:

- USDA FoodData Central is the primary live API lookup.
- UK Composition of Foods Integrated Dataset (CoFID) 2021 is an independent
  official cross-check and fallback. Its public workbook downloads lazily to
  the ignored `data/foods/raw` directory on first use.

When both sources have a sufficiently close generic-food match, the interface
shows both exact records and compares shared nutrients side by side. Values are
never merged or averaged. When only one source matches, the interface labels it
as a single-source result instead of claiming cross-verification. Trace values
such as `Tr` and unavailable CoFID values are omitted rather than converted to
invented zeroes.

Every result preserves its record ID, official URL, data type, organization,
and license. Quantities entered in grams scale each source independently from
its 100 g basis, and successful analyses are saved to the user's local food
history. Successful source lookups are cached in SQLite for 30 days.

`DEMO_KEY` works for local development. Set `USDA_FDC_API_KEY` to your own free
Data.gov key for production limits. If one official provider is unavailable,
the other can still provide a transparently labeled single-source result. If
neither source matches, or a mixed dish has no confirmed ingredients, Afiyati
displays no nutrition numbers rather than asking the language model to estimate
them. Asking `ما المصدر؟` returns the direct records preserved from the
previous answer.

## RAG flow

```text
Question + safe profile fields + last 3 conversation summaries
  -> deterministic safety screen
  -> query analysis and condition-aware rewrites
  -> dense Qdrant search + BM25
  -> reciprocal-rank fusion and deduplication
  -> modular fallback reranker, Top-5
  -> qwen3:4b structured generation from evidence only
  -> citation replacement from retrieved metadata
  -> claim/citation validation and safe downgrade
  -> answer + evidence panel + technical trace
```

With an empty knowledge base, clinical questions intentionally return
`insufficient_evidence`.

## Evaluation

`evaluation/questions.json` contains 28 Arabic, English, and mixed-language
cases spanning direct, multi-condition, ambiguous, refusal, and emergency
requests.

```powershell
scripts\evaluate_rag.bat
```

The repository includes a frozen two-document official corpus and 17
page-level provisional relevance judgments. The evaluator reports Precision@3,
Precision@5, Recall@5, MRR, Top-K comparisons, citation accuracy, citation
validity, unsupported-claim rate, and latency with 95% bootstrap confidence
intervals. Results are exposed through `/api/rag/benchmark` and the Technical
RAG Demo page.

Provisional results are engineering evidence, not a clinical validation claim.
The evaluator and UI keep them explicitly labeled until independent clinicians
adjudicate relevance and claim support. See `evaluation/README.md` for the
promotion workflow.

## Tests

```powershell
scripts\test_all.bat
```

Tests cover health, auth, profile persistence, safe chat personalization,
multi-source USDA/CoFID matching and comparison, multiple conditions, temporary
and permanent medication schedules, dose states, empty-index refusal, emergency
access without login, meal confirmation, chunk metadata, BM25 exact terms,
hybrid fallback, Qdrant local storage, citation metadata, validation, safety,
and Ollama model availability.

## Known limitations

- The two official PDFs are indexed locally, but the included relevance labels
  are provisional and require independent clinician adjudication before the
  metrics can be called official.
- Meal ingredient recognition is a mock/demo adapter; users must confirm every
  ingredient before RAG analysis.
- Arabic food coverage is controlled through `data/foods/aliases.ar.json`; an
  unrecognized name is refused until reviewed USDA and/or CoFID query aliases
  are added. Mixed dishes still require confirmed ingredients and weights.
- Browser reminders require the app to be open. Native background scheduling is
  outside this local web prototype.
- Lexical claim verification is a conservative screen, not clinical NLI. It can
  downgrade an answer; it must not be presented as formal medical validation.
- Contradiction display is represented in the prompt/trace architecture but
  requires multiple indexed, trusted sources to exercise and evaluate.

See `ARCHITECTURE.md`, `EVALUATION_REPORT.md`, and `FINAL_REPORT.md` for the
engineering record.
