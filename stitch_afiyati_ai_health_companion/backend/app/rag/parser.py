from __future__ import annotations

from collections import Counter
from pathlib import Path

from pypdf import PdfReader


class PdfParsingError(RuntimeError):
    pass


def parse_pdf(path: Path) -> list[dict]:
    try:
        reader = PdfReader(path)
    except Exception as exc:
        raise PdfParsingError(f"Could not open {path.name}: {exc}") from exc
    raw_pages: list[list[str]] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise PdfParsingError(f"Text extraction failed in {path.name}: {exc}") from exc
        lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
        raw_pages.append(lines)
    if not any(raw_pages):
        raise PdfParsingError(f"No extractable text found in {path.name}")

    first_lines = Counter(lines[0] for lines in raw_pages if lines)
    last_lines = Counter(lines[-1] for lines in raw_pages if lines)
    threshold = max(3, len(raw_pages) // 2)
    repeated = {
        line for line, count in list(first_lines.items()) + list(last_lines.items()) if count >= threshold
    }
    pages: list[dict] = []
    for index, lines in enumerate(raw_pages, start=1):
        cleaned = [line for line in lines if line not in repeated]
        pages.append({"page_number": index, "text": "\n".join(cleaned)})
    return pages

