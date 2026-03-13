# Semiconductor Alternative Search — Application Flow

## 1) What this service does
This service ingests semiconductor product data, stores normalized specs in **Oracle DB**, stores/retrieves vectors from a **Vector DB** (Qdrant when enabled), and returns ranked alternatives via hybrid search.

## 2) Runtime architecture
- **API layer**: FastAPI (`main.py`, `api/routes.py`)
- **Structured storage**: Oracle (`database/db_client.py`)
- **Vector storage/search**: `vector_db/service.py`
  - `VECTOR_DB_PROVIDER=qdrant` → external Qdrant
  - otherwise fallback to Oracle embedding scan
- **Normalization/parsing**: `ingestion/*`
- **Ranking**: `search/comparison_engine.py` with weights in `config/ranking_weights.py`

## 3) End-to-end search flow (`POST /find-alternative`)
1. User sends `part_number`.
2. API loads base product from Oracle by part number.
3. Structured candidates are fetched from Oracle using category/spec constraints.
4. Vector neighbors are fetched from vector DB service (Qdrant if configured; fallback otherwise).
5. Candidate sets are merged.
6. Comparison engine applies category rules (`gte`/`lte`) and weighted scoring.
7. Ranked alternatives are returned with search source metadata.

## 4) Ingestion flows

### A) `POST /ingest-data`
- Reads CSV (`PRODUCTS_CSV_PATH`, default `data/products.csv`).
- For each row:
  - loads HTML from local file path or URL
  - parses canonical specs
  - detects category (if needed)
  - normalizes to typed fields
  - upserts into Oracle

> Note: this endpoint stores structured data. Use `/generate-embeddings` (or your own vector generation pipeline) to generate vectors afterward.

### B) `POST /ingest-demo-data`
- Loads JSON demo records (`DEMO_PRODUCTS_PATH`, default `data/demo_products.json`).
- Upserts into Oracle.
- Creates demo vectors and stores them in Oracle embedding field.
- Syncs those vectors into external vector DB (if enabled).

### C) `POST /generate-embeddings`
- Generates embeddings for products missing vectors.
- Stores vectors in Oracle.
- Pushes vectors into external vector DB (if enabled).

### D) `POST /sync-vector-db`
- Reads all products that already have embeddings in Oracle.
- Pushes them to external vector DB.
- Useful when enabling Qdrant on an existing dataset.

## 5) API list
- `GET /health`
- `POST /ingest-data`
- `POST /ingest-demo-data`
- `POST /generate-embeddings`
- `POST /sync-vector-db`
- `POST /find-alternative`
- `GET /find-alternatives` (legacy compatibility)
- `GET /products`
- `GET /products/{product_name}`

## 6) How to start
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set Oracle env vars:
   - `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE_NAME`, `ORACLE_USER`, `ORACLE_PASSWORD`
3. (Optional) Set vector DB env vars for Qdrant:
   - `VECTOR_DB_PROVIDER=qdrant`
   - `QDRANT_URL`
   - `QDRANT_API_KEY` (if required)
   - `QDRANT_COLLECTION_PREFIX` (optional)
4. (Optional) Set `OPENAI_API_KEY` for embedding generation.
5. Run app:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 7) Recommended startup sequence (production-like)
1. Start Oracle and Qdrant.
2. Start API.
3. Ingest products (`/ingest-data` or `/ingest-demo-data`).
4. Generate vectors (`/generate-embeddings`) if not already present.
5. Run `/sync-vector-db` once to guarantee external vector DB is fully populated.
6. Use `/find-alternative` for runtime search.

## 8) Notes on correctness
- Oracle remains source of truth for structured specs.
- Vector DB is source for nearest-neighbor similarity.
- Comparison engine always applies final engineering constraints and weighted ranking before response.


## 9) Streamlit Frontend
- File: `frontend/app.py`
- Run:
  ```bash
  streamlit run frontend/app.py
  ```
- Features:
  - Ingest via `/ingest-data` with user-provided CSV path
  - Ingest demo via `/ingest-demo-data`
  - Search via `/find-alternative` with pros/cons visualization
  - View all ingested products from `/products`
- Configure backend URL from the sidebar (`API Base URL`).
