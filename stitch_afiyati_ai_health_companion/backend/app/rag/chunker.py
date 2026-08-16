from __future__ import annotations

import re
import uuid
from collections.abc import Iterable


TOKEN_PATTERN = re.compile(r"[\w\u0600-\u06ff]+|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text)


def estimate_tokens(text: str) -> int:
    return len(tokenize(text))


def _split_words(text: str, max_tokens: int, overlap: int) -> list[str]:
    words = text.split()
    if len(words) <= max_tokens:
        return [text.strip()] if text.strip() else []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + max_tokens)
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(start + 1, end - overlap)
    return chunks


def _looks_like_heading(line: str) -> bool:
    value = line.strip()
    if not value or len(value) > 140:
        return False
    return bool(
        re.match(r"^(?:\d+(?:\.\d+)+(?:[.)\s])|\d{1,2}[.)]\s+|[A-Z][.)]\s+)", value)
        or (value.isupper() and len(value.split()) <= 14)
    )


def section_aware_chunks(
    pages: Iterable[dict], metadata: dict, child_tokens: int = 450, parent_tokens: int = 850, overlap: int = 70
) -> list[dict]:
    """Create page-bounded chunks so every citation points to the evidence page.

    Section titles are carried across page boundaries, but chunk text never is.
    This trades a small amount of cross-page context for auditable page citations.
    """
    sections: list[dict] = []
    current_title = "Document"
    for page in pages:
        page_number = int(page.get("page_number", 1))
        current = {"title": current_title, "subsection": None, "page": page_number, "parts": []}
        for raw_line in page.get("text", "").splitlines():
            line = " ".join(raw_line.split())
            if not line:
                continue
            if _looks_like_heading(line):
                if current["parts"]:
                    sections.append(current)
                current_title = line
                current = {"title": current_title, "subsection": None, "page": page_number, "parts": []}
            else:
                current["parts"].append(line)
        if current["parts"]:
            sections.append(current)

    output: list[dict] = []
    namespace = uuid.UUID("8a6ef1ea-1a72-46a2-9786-afiyati000001".replace("afiyati", "af1a71"))
    for section_index, section in enumerate(sections):
        heading = section["title"] if section["title"] != "Document" else ""
        body = "\n".join(value for value in [heading, *section["parts"]] if value)
        parent_parts = _split_words(body, parent_tokens, overlap)
        for parent_index, parent_text in enumerate(parent_parts):
            parent_seed = f"{metadata.get('source_filename')}:{section_index}:{parent_index}:{parent_text[:100]}"
            parent_id = str(uuid.uuid5(namespace, parent_seed))
            for child_index, child_text in enumerate(_split_words(parent_text, child_tokens, overlap)):
                chunk_seed = f"{parent_id}:{child_index}:{child_text[:100]}"
                chunk_id = str(uuid.uuid5(namespace, chunk_seed))
                chunk_metadata = {
                    "chunk_id": chunk_id,
                    "parent_id": parent_id,
                    "condition": metadata.get("condition", "unknown"),
                    "organization": metadata.get("organization", "unknown"),
                    "guideline_id": metadata.get("guideline_id"),
                    "guideline_title": metadata.get("title") or metadata.get("guideline_title", "Untitled guideline"),
                    "publication_year": metadata.get("publication_year"),
                    "guideline_version": metadata.get("version"),
                    "language": metadata.get("language", "en"),
                    "section_title": section["title"],
                    "subsection_title": section.get("subsection"),
                    "page_number": section["page"],
                    "source_filename": metadata.get("source_filename", "unknown.pdf"),
                    "source_url": metadata.get("source_url"),
                }
                output.append({"text": child_text, "parent_text": parent_text, "metadata": chunk_metadata})
    return output


def fixed_chunks(text: str, size: int = 450, overlap: int = 70) -> list[str]:
    return _split_words(text, size, overlap)
