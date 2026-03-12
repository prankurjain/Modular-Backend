"""
Loads raw HTML content from a local file path or URL.
"""

from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _normalize_windows_path(raw_path: str, csv_dir: Path) -> Path:
    """Make Windows-style paths usable in Unix container environments.

    If the provided absolute path does not exist, try using only the file name inside
    the CSV directory and common HTML data directories.
    """
    candidate = Path(raw_path)
    if candidate.exists():
        return candidate

    filename = Path(raw_path.replace("\\", "/")).name
    fallbacks = [
        csv_dir / filename,
        csv_dir / "html" / filename,
        csv_dir.parent / "html" / filename,
    ]
    for path in fallbacks:
        if path.exists():
            return path

    return candidate


def load_html(html_source: str, csv_dir: str | None = None) -> str:
    """
    Read and return raw HTML from a local file path or a URL.

    Args:
        html_source: Local file path or an HTTP(S) URL.
        csv_dir: Optional directory of the CSV file for resolving relative paths.

    Raises:
        FileNotFoundError: If local file does not exist.
        ValueError: If source is empty.
    """
    source = (html_source or "").strip()
    if not source:
        raise ValueError("html_source cannot be empty")

    if _looks_like_url(source):
        req = Request(source, headers={"User-Agent": DEFAULT_USER_AGENT})
        with urlopen(req, timeout=30) as response:  # nosec B310 - controlled use for ingestion
            return response.read().decode("utf-8", errors="replace")

    base_dir = Path(csv_dir).resolve() if csv_dir else Path.cwd()

    path = Path(source)
    if not path.is_absolute():
        path = (base_dir / path).resolve()
    else:
        path = _normalize_windows_path(source, base_dir)

    if not path.exists():
        # last attempt for Windows-style absolute paths represented as plain text
        path = _normalize_windows_path(source, base_dir)

    if not path.exists():
        raise FileNotFoundError(f"HTML file not found: {source}")

    with path.open(encoding="utf-8", errors="replace") as f:
        return f.read()
