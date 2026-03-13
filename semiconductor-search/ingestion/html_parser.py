"""
Parses semiconductor HTML and extracts key/value spec pairs.
"""

import re
from bs4 import BeautifulSoup
from config.categories_config import CATEGORIES


def _normalize_label(text: str) -> str:
    text = (text or "").strip().lower().rstrip(":")
    text = re.sub(r"\s+", " ", text)
    # Keep alnum and common symbols used in labels like rds(on)
    text = re.sub(r"[^a-z0-9()/%+\- ]", "", text)
    return text.strip()


def _resolve_canonical(label: str, spec_map: dict[str, str]) -> str | None:
    if label in spec_map:
        return spec_map[label]

    # Try relaxed matching for labels like "Collector-Emitter Voltage VCEO"
    compact_label = label.replace(" ", "")
    for raw_key, canonical in spec_map.items():
        normalized_key = _normalize_label(raw_key)
        if normalized_key in label or normalized_key.replace(" ", "") in compact_label:
            return canonical
    return None


def _build_spec_map(category: str | None) -> dict[str, str]:
    if category and category.lower().strip() in CATEGORIES:
        cat_config = CATEGORIES[category.lower().strip()]
        return {_normalize_label(k): v for k, v in cat_config.get("html_spec_map", {}).items()}

    merged: dict[str, str] = {}
    for cat_cfg in CATEGORIES.values():
        for label, canonical in cat_cfg.get("html_spec_map", {}).items():
            merged[_normalize_label(label)] = canonical
    return merged


def parse_product_specs(html: str, category: str | None) -> dict:
    """Parse an HTML page and extract canonical specs.

    If category is unknown, use a merged map across all supported categories.
    """
    spec_map = _build_spec_map(category)

    soup = BeautifulSoup(html, "html.parser")
    raw_specs: dict[str, str] = {}

    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["th", "td"])
            if len(cells) < 2:
                continue

            label = _normalize_label(cells[0].get_text(separator=" ", strip=True))
            value = cells[1].get_text(separator=" ", strip=True)

            canonical = _resolve_canonical(label, spec_map)
            if canonical and value and canonical not in raw_specs:
                raw_specs[canonical] = value

    dls = soup.find_all("dl")
    for dl in dls:
        for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
            label = _normalize_label(dt.get_text(separator=" ", strip=True))
            value = dd.get_text(separator=" ", strip=True)
            canonical = _resolve_canonical(label, spec_map)
            if canonical and value and canonical not in raw_specs:
                raw_specs[canonical] = value

    # Mouser-like specs blocks
    for row in soup.select("[class*='spec']"):
        text_cells = row.find_all(["th", "td", "span", "dt", "dd", "label"])
        if len(text_cells) < 2:
            continue
        label = _normalize_label(text_cells[0].get_text(separator=" ", strip=True))
        value = text_cells[1].get_text(separator=" ", strip=True)
        canonical = _resolve_canonical(label, spec_map)
        if canonical and value and canonical not in raw_specs:
            raw_specs[canonical] = value

    return raw_specs
