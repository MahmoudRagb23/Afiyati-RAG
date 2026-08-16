# Afiyati benchmark

This directory contains the reproducible evaluation harness for the local RAG
system. It deliberately separates engineering evidence from clinical claims.

## One-command run

After validating and ingesting the guideline corpus:

```powershell
scripts\evaluate_rag.bat
```

The command evaluates deterministic safety cases, dense/BM25/hybrid retrieval,
Top-K behavior, citation relevance, structural citation validity, grounding
coverage, unsupported-claim rate, and latency. The machine-readable result is
written to `evaluation/reports/latest.json` and displayed by the Technical RAG
Demo page.

For a fast retrieval-only run:

```powershell
python evaluation\run_evaluation.py
```

## Judgment tiers

`judgments.json` is currently `provisional`. Its relevance units are exact PDF
pages reviewed against the locally stored official sources. This is suitable
for development, regression testing, and hackathon demonstration, but it is not
a clinician-adjudicated benchmark.

To produce an official report:

1. Give independent reviewers the frozen questions, PDF versions, and candidate
   passages without showing system rankings.
2. Have at least two qualified clinicians label relevant pages/chunks and claim
   support independently.
3. Adjudicate disagreements and record the decision trail.
4. Replace or override the provisional qrels, set `label_tier` to `official`,
   and set `clinical_adjudication` to `true`.
5. Run `python evaluation\run_evaluation.py --full --judgments <file>`.

The evaluator rejects an `official` label tier unless clinical adjudication is
explicitly declared. The UI also keeps provisional results visually distinct.

## Metric definitions

- Precision@K: relevant page-bounded chunks in the first K ranks divided by K.
- Recall@K: unique judged page/chunk units covered in the first K ranks divided
  by all relevant units for that question.
- MRR: reciprocal rank of the first relevant result, macro-averaged.
- Citation accuracy: generated citations whose chunk falls on a page judged
  relevant for the question, divided by all generated citations.
- Structural citation validity: citations whose metadata matches a retrieved
  chunk and source.
- Unsupported-claim rate: current conservative lexical proxy. It remains
  provisional until claim-to-evidence entailment is clinician labeled.

Retrieval metrics are macro-averaged across judged questions. The report stores
deterministic 95% bootstrap confidence intervals and per-question audit data.
