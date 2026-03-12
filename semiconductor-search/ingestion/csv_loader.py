"""
Reads the products CSV file and returns a list of dicts with product metadata.

Supported columns (flexible):
  - product_name (required)
  - category (optional, defaults to "transistor")
  - html_path / html_file / source
  - url / product_url

If a local html path is not provided, URL can be used as the HTML source.
"""

import csv
import os

from config.categories_config import CATEGORIES


def load_product_csv(csv_path: str) -> list[dict]:
    """
    Parse the products CSV file.

    Expected columns:
      required: product_name
      optional: category, html_path (or html_file/source), url (or product_url)

    Returns:
        List of dicts with keys: product_name, category, html_path
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    products = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            name = row.get("product_name", "").strip()
            category = row.get("category", "").strip().lower() or "transistor"
            html_path = (
                row.get("html_path", "").strip()
                or row.get("html_file", "").strip()
                or row.get("source", "").strip()
            )
            source_url = row.get("url", "").strip() or row.get("product_url", "").strip()

            if not name:
                print(f"  [CSV] Row {i}: skipping row with empty product_name")
                continue
            if category and category not in CATEGORIES:
                print(
                    f"  [CSV] Row {i}: unknown category '{category}' for '{name}', defaulting to 'transistor'"
                )
                category = "transistor"
            if not html_path and not source_url:
                print(
                    f"  [CSV] Row {i}: skipping '{name}' — missing both html_path and url"
                )
                continue

            products.append({
                "product_name": name,
                "category": category,
                "html_path": html_path,
                "source_url": source_url,
            })

    print(f"[CSV] Loaded {len(products)} products from {csv_path}")
    return products
