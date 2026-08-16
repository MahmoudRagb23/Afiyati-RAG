# Afiyati implementation plan

Baseline inspection on 2026-08-16 found a Stitch export containing 12 standalone
HTML mockups, 11 reference screenshots, and a design-token document. There was
no application runtime, router, package manifest, backend, persistence, or API
integration. The standalone landing page could be served as static HTML, but the
screens were isolated and most navigation and data were mock-only.

1. Preserve the Arabic RTL layout, light medical-teal palette, cards, emergency
   red treatment, and evidence-oriented information hierarchy in a React app.
2. Add a local FastAPI + SQLite backend with authentication, profiles,
   medication schedules, symptom triage, meal confirmation, and notifications.
3. Add an offline-first Ollama RAG pipeline: validation, PDF parsing,
   section-aware/parent-child chunking, Qdrant local storage, BM25, rank fusion,
   reranking, structured generation, citation validation, and safety refusal.
4. Connect every visible workflow and add loading, error, empty, responsive,
   accessibility, and technical-demo states.
5. Run guideline validation, automated tests, builds, model connectivity checks,
   and honest evaluation reports (never synthesizing unavailable measurements).

