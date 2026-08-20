# Afiyati architecture

## System boundary

Afiyati is a local decision-support prototype. The React client communicates
only with a FastAPI process on loopback. FastAPI owns identity, persistence,
safety, retrieval, generation, and trace data. Ollama is the only model runtime.

## Frontend

The Vite/React application uses route-level workflows and a shared RTL shell.
All user records shown in the dashboard come from the API. Chat answers use a
structured renderer for summary, per-condition effects, quantity (only when the
model and evidence support it), warnings, evidence strength, citations, and
source chunks. The technical view exposes retrieval evidence and measured
timings but never chain-of-thought.

## Backend and database

FastAPI routers separate authentication, profile, medication, chat, meal,
symptom, source, and trace operations. SQLite stores users, health profiles,
medications, dose events, conversation history, and symptom classifications.
Passwords use salted scrypt hashes. HMAC-signed, expiring bearer tokens identify
local sessions. Emergency symptom triage accepts anonymous requests.

## Knowledge ingestion

The manifest is authoritative metadata. Validation precedes every ingestion.
`pypdf` preserves page order; repeated first/last page lines are removed only
when they recur across the document. Section-aware parsing recognizes short or
numbered headings. Each child chunk links to a larger parent context and retains
condition, organization, guideline, version, language, section, page, filename,
and source URL metadata.

Default experimental configuration:

- child: 450 estimated tokens
- parent: 850 estimated tokens
- overlap: 70 tokens
- one Qdrant collection: `medical_guidelines`
- metadata filtering by condition

These are implementation defaults, not benchmark winners. They remain subject
to the required post-data comparison.

## Retrieval

Query analysis derives intent, topic, and condition set. Deterministic rewriting
keeps the original query and adds one condition-aware English retrieval query
per registered disease. Dense search uses the configured Ollama embedding and
Qdrant local persistence. BM25 preserves exact terms such as HbA1c, CKD,
metformin, sodium, and Arabic surface forms. Reciprocal-rank fusion merges and
deduplicates both lists. A modular lexical reranker is used by default; it is
stable under the 4 GB VRAM constraint and is not claimed to improve quality
without a benchmark. The generator receives the best five chunks.

## Generation, citations, and verification

`qwen3:4b` receives the original question, registered conditions, retrieved
parent evidence, metadata, and explicit safety rules. Ollama JSON-schema output
is validated with Pydantic. The backend discards model-authored source metadata
and reconstructs citations exclusively from retrieved chunks. It verifies that
each cited chunk was retrieved and that page/source metadata matches. A
conservative lexical claim screen labels generated claims supported, partially
supported, or unsupported. If most claims fail, the answer is downgraded to
insufficient evidence.

## Safety

Deterministic bilingual rules run before retrieval. Possible emergency requests
bypass normal chat and immediately produce the emergency response. Medication
change requests are marked caution. Non-health domains are out of scope. An
empty or unavailable index returns insufficient evidence, and malformed model
JSON or Ollama failures fall back safely.

## Failure modes

- Ollama unavailable/model missing: safe insufficient-evidence response plus a
  clear local-runtime warning.
- Qdrant unavailable/corrupt: BM25 can still operate; status exposes the error.
- PDF parse failure: validation/ingestion stops and names the file.
- No results: no generator call is made.
- Malformed LLM JSON: Pydantic rejects it and the response is downgraded.
- Frontend API error: route-local, retryable Arabic error state.
