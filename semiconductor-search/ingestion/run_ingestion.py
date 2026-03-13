from pathlib import Path

from ingestion.csv_loader import load_product_csv
from ingestion.html_loader import load_html
from ingestion.html_parser import parse_product_specs
from ingestion.spec_normalizer import normalize_specs

from database.db_client import (
    upsert_product,
    update_product_embedding
)

from embeddings.embedding_service import get_embedding


def run_ingestion(csv_path: str):

    print(f"[INGEST] Loading CSV: {csv_path}")

    products = load_product_csv(csv_path)

    if not products:
        print("[INGEST] No products found in CSV")
        return

    csv_dir = Path(csv_path).parent

    for p in products:

        name = p["product_name"]
        category = p["category"]

        print(f"[INGEST] Processing: {name}")

        try:

            html_source = p["html_path"] or p["source_url"]

            # Load HTML
            html = load_html(html_source, str(csv_dir))

            # Parse specs
            raw_specs = parse_product_specs(html, category)

            # Normalize specs
            product = normalize_specs(name, category, raw_specs)

            # Insert / update database
            upsert_product(product)

            # Generate embedding
            embedding = get_embedding(product["features_text"])

            if embedding:
                update_product_embedding(name, embedding)

            print(f"[INGEST] Completed: {name}")

        except Exception as e:
            print(f"[ERROR] {name}: {e}")

    print("[INGEST] Pipeline completed successfully")


if __name__ == "__main__":

    csv_file = "data/products.csv"

    run_ingestion(csv_file)