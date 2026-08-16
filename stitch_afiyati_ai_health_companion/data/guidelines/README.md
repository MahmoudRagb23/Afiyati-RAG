# Afiyati guideline library

Place only official, current clinical guideline PDFs in the matching folder.
Do not mix drafts, archived versions, blogs, or unsourced summaries into the
production index. Afiyati does not download medical sources automatically.

For each PDF add one object to `manifest.json`:

```json
{
  "file": "hypertension/nice/NICE_NG136_Hypertension_Adults.pdf",
  "condition": "hypertension",
  "organization": "nice",
  "guideline_id": "NG136",
  "title": "Hypertension in adults: diagnosis and management",
  "language": "en",
  "status": "current",
  "source_type": "clinical_guideline",
  "publication_year": 2023,
  "version": "2023 update",
  "source_url": "https://www.nice.org.uk/guidance/ng136"
}
```

The path is relative to this directory. Folder names supply useful defaults,
but explicit manifest metadata is authoritative. Validate before ingestion:

```powershell
cd backend
python -m app.rag.validate_guidelines
python -m app.rag.ingestion
```

The validator blocks silent ingestion of missing, unregistered, empty, or
unparseable PDFs and reports metadata gaps. A zero-document library is valid;
the assistant will safely return `insufficient_evidence` until sources exist.

