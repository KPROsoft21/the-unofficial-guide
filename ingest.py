"""Stage 1 — Document ingestion.

Loads every document in documents/ (supports .txt and .pdf), strips boilerplate,
and returns clean text plus a source name for attribution. PDFs are read with
pdfplumber (digitally-created PDFs only; no OCR).

Run directly to inspect what was loaded:
    python ingest.py
"""

import re
from pathlib import Path

from config import DOCS_DIR


def _clean(text: str) -> str:
    """Remove the leading SOURCE/COLLECTED metadata header and normalize whitespace.

    The corpus files carry a small provenance header (SOURCE:/COLLECTED:) that is
    useful for a human reading the raw file but is not student-knowledge content,
    so we drop it before chunking. We also collapse stray HTML entities and runs
    of blank lines that would otherwise create empty chunks.
    """
    # Strip a leading metadata header block (lines starting SOURCE:/COLLECTED:)
    lines = text.splitlines()
    while lines and re.match(r"^\s*(SOURCE:|COLLECTED:)", lines[0]):
        lines.pop(0)
    text = "\n".join(lines)

    # Decode the few HTML entities that survive copy-paste from web sources
    entities = {"&amp;": "&", "&nbsp;": " ", "&#39;": "'", "&quot;": '"', "&gt;": ">", "&lt;": "<"}
    for ent, char in entities.items():
        text = text.replace(ent, char)

    # Strip any leftover HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Collapse 3+ newlines to a paragraph break; trim trailing spaces per line
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _read_file(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        import pdfplumber  # imported lazily so .txt-only users don't need it
        with pdfplumber.open(path) as pdf:
            return "\n\n".join(p.extract_text() for p in pdf.pages if p.extract_text())
    return path.read_text(encoding="utf-8", errors="ignore")


def load_documents(docs_dir: Path = DOCS_DIR) -> list[dict]:
    """Return a list of {"source": filename, "text": cleaned_text} dicts.

    Any file that produces empty text after cleaning (e.g. a scanned-only PDF) is
    skipped with a warning rather than poisoning the index with blank content.
    """
    docs = []
    for path in sorted(docs_dir.iterdir()):
        if path.suffix.lower() not in {".txt", ".pdf"} or path.name.startswith("."):
            continue
        cleaned = _clean(_read_file(path))
        if not cleaned:
            print(f"  ! skipped {path.name}: produced empty text (scanned PDF?)")
            continue
        docs.append({"source": path.name, "text": cleaned})
    return docs


if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents from {DOCS_DIR}\n")
    sample = docs[0]
    print(f"--- {sample['source']} (first 500 chars after cleaning) ---")
    print(sample["text"][:500])
