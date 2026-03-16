"""
Reads the products CSV file and returns a list of dicts with product metadata.

Supported columns (flexible):
  - product_name (required)
  - category (optional, defaults to "transistor")
  - html_path / html_file / source
  - url / product_url
  - datasheet_link / datasheet_url / datasheet_path

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
      optional: category, html_path (or html_file/source), url (or product_url),
                datasheet_link (or datasheet_url/datasheet_path)

    Returns:
        List of dicts with keys: product_name, category, html_path
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    products = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            print(row)
            print(row.keys())
            name = row.get("product_name", "").strip()
            category = row.get("category", "").strip().lower() or "transistor"
            html_path = (
                row.get("html_path", "").strip()
                or row.get("html_file", "").strip()
                or row.get("source", "").strip()
            )
            source_url = row.get("url", "").strip() or row.get("product_url", "").strip()
            datasheet_link = (
                row.get("datasheet_link", "").strip()
                or row.get("datasheet_url", "").strip()
                or row.get("datasheet_path", "").strip()
            )

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
                "datasheet_link": datasheet_link,
            })

    print(f"[CSV] Loaded {len(products)} products from {csv_path}")
    return products
