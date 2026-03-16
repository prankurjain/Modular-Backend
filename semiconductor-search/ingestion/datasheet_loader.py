"""Load datasheet content from local files or URLs."""

from __future__ import annotations

import io
from pathlib import Path

import requests


try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - fallback import path
    try:
        from PyPDF2 import PdfReader  # type: ignore
    except Exception:  # pragma: no cover
        PdfReader = None  # type: ignore


from ingestion.html_loader import _normalize_windows_path


def _read_pdf_bytes(source: str, csv_dir: str | None = None) -> bytes:
    source = source.strip()
    if source.startswith("http://") or source.startswith("https://"):
        response = requests.get(source, timeout=30)
        response.raise_for_status()
        return response.content

    base_dir = Path(csv_dir).resolve() if csv_dir else Path.cwd()
    pdf_path = _normalize_windows_path(source, base_dir)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Datasheet file not found: {source}")
    return pdf_path.read_bytes()


def read_datasheet_text(source: str, csv_dir: str | None = None) -> str:
    """Extract text from a PDF datasheet source (url or local path)."""
    if not source:
        return ""
    if PdfReader is None:
        print("[Datasheet] pypdf/PyPDF2 not available, skipping datasheet parsing")
        return ""

    try:
        pdf_bytes = _read_pdf_bytes(source, csv_dir=csv_dir)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [(page.extract_text() or "") for page in reader.pages[:8]]
        return "\n".join(pages).strip()
    except Exception as exc:
        print(f"[Datasheet] Unable to read datasheet '{source}': {exc}")
        return ""
