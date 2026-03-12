"""
Oracle Database client using python-oracledb (thin mode — no Oracle Client required).

Vector embeddings are stored as CLOB (JSON string) and ranked in Python.
Cosine similarity is computed in Python after fetching candidates from Oracle.
"""

import json
import oracledb
from config.settings import ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN


def get_connection():
    """Return a new Oracle database connection (thin mode)."""
    if not ORACLE_USER or not ORACLE_PASSWORD:
        raise RuntimeError(
            "Oracle credentials are not configured. "
            "Set ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_PORT, "
            "and ORACLE_SERVICE_NAME environment variables."
        )
    return oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)


def initialize_schema():
    """
    Create the PRODUCTS table and sequence if they do not already exist.
    Uses Oracle-specific DDL (VARCHAR2, NUMBER, CLOB, IDENTITY columns).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Check if table already exists
            cur.execute(
                "SELECT COUNT(*) FROM user_tables WHERE table_name = 'PRODUCTS'"
            )
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    CREATE TABLE products (
                        id                      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                        product_name            VARCHAR2(255) NOT NULL,
                        category                VARCHAR2(100),

                        -- Microcontroller fields
                        architecture            VARCHAR2(100),
                        flash_kb                NUMBER,
                        ram_kb                  NUMBER,
                        gpio_pins               NUMBER(10),
                        voltage_min             NUMBER,
                        voltage_max             NUMBER,
                        interfaces              VARCHAR2(500),

                        -- Sensor fields
                        sensor_type             VARCHAR2(100),
                        measurement_range       VARCHAR2(200),
                        accuracy                VARCHAR2(100),

                        -- Power IC fields
                        topology                VARCHAR2(100),
                        output_voltage          VARCHAR2(100),
                        output_current_a        NUMBER,
                        switching_frequency_khz NUMBER,
                        efficiency              VARCHAR2(50),

                        -- Memory fields
                        memory_type             VARCHAR2(100),
                        capacity_mb             NUMBER,
                        speed                   VARCHAR2(100),

                        -- Shared / generic fields
                        max_speed_mhz           NUMBER,
                        package_type            VARCHAR2(100),
                        temp_range              VARCHAR2(100),
                        interface               VARCHAR2(200),
                        output_type             VARCHAR2(100),

                        -- Natural language feature text used for embedding
                        features_text           CLOB,

                        -- Embedding vector stored as JSON array in CLOB
                        embedding_vector        CLOB,

                        created_at              TIMESTAMP DEFAULT SYSTIMESTAMP,
                        updated_at              TIMESTAMP DEFAULT SYSTIMESTAMP,

                        CONSTRAINT uq_product_name UNIQUE (product_name)
                    )
                """)
                print("Table PRODUCTS created.")
            else:
                print("Table PRODUCTS already exists.")
        conn.commit()
        print("Schema initialized successfully.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def upsert_product(product: dict) -> int:
    """
    Insert a new product or update an existing one by product_name (MERGE).
    Returns the product id.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Use MERGE to handle insert-or-update (Oracle's upsert)
            cur.execute("""
                MERGE INTO products tgt
                USING (SELECT :product_name AS product_name FROM dual) src
                ON (tgt.product_name = src.product_name)
                WHEN MATCHED THEN UPDATE SET
                    category                = :category,
                    architecture            = :architecture,
                    flash_kb                = :flash_kb,
                    ram_kb                  = :ram_kb,
                    gpio_pins               = :gpio_pins,
                    voltage_min             = :voltage_min,
                    voltage_max             = :voltage_max,
                    interfaces              = :interfaces,
                    sensor_type             = :sensor_type,
                    measurement_range       = :measurement_range,
                    accuracy                = :accuracy,
                    topology                = :topology,
                    output_voltage          = :output_voltage,
                    output_current_a        = :output_current_a,
                    switching_frequency_khz = :switching_frequency_khz,
                    efficiency              = :efficiency,
                    memory_type             = :memory_type,
                    capacity_mb             = :capacity_mb,
                    speed                   = :speed,
                    max_speed_mhz           = :max_speed_mhz,
                    package_type            = :package_type,
                    temp_range              = :temp_range,
                    interface               = :interface,
                    output_type             = :output_type,
                    features_text           = :features_text,
                    updated_at              = SYSTIMESTAMP
                WHEN NOT MATCHED THEN INSERT (
                    product_name, category, architecture, flash_kb, ram_kb,
                    gpio_pins, voltage_min, voltage_max, interfaces,
                    sensor_type, measurement_range, accuracy,
                    topology, output_voltage, output_current_a,
                    switching_frequency_khz, efficiency,
                    memory_type, capacity_mb, speed,
                    max_speed_mhz, package_type, temp_range,
                    interface, output_type, features_text
                ) VALUES (
                    :product_name, :category, :architecture, :flash_kb, :ram_kb,
                    :gpio_pins, :voltage_min, :voltage_max, :interfaces,
                    :sensor_type, :measurement_range, :accuracy,
                    :topology, :output_voltage, :output_current_a,
                    :switching_frequency_khz, :efficiency,
                    :memory_type, :capacity_mb, :speed,
                    :max_speed_mhz, :package_type, :temp_range,
                    :interface, :output_type, :features_text
                )
            """, {**_default_product_fields(), **product})

            # Fetch the id of the upserted row
            cur.execute(
                "SELECT id FROM products WHERE product_name = :name",
                {"name": product["product_name"]}
            )
            row = cur.fetchone()
            product_id = row[0] if row else None

        conn.commit()
        return product_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def update_product_embedding(product_name: str, embedding: list):
    """Store the embedding vector for a product as a JSON CLOB."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET embedding_vector = :emb WHERE product_name = :name",
                {"emb": json.dumps(embedding), "name": product_name}
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()




def _to_json_safe_value(value):
    """Convert Oracle driver values (including LOBs) into JSON-serializable Python values."""
    if value is None:
        return None

    # python-oracledb LOB objects expose .read()
    if hasattr(value, "read") and callable(value.read):
        try:
            return value.read()
        except Exception:
            return None

    return value


def _normalize_row(columns: list[str], row: tuple) -> dict:
    """Build a dict row and normalize Oracle-specific value types."""
    return {
        col: _to_json_safe_value(val)
        for col, val in zip(columns, row)
    }


def get_product_by_name(product_name: str) -> dict | None:
    """Fetch a single product row by exact product name."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM products WHERE product_name = :name",
                {"name": product_name}
            )
            columns = [col[0].lower() for col in cur.description]
            row = cur.fetchone()
            if not row:
                return None
            product = _normalize_row(columns, row)
            # Parse embedding CLOB back to list if present
            if product.get("embedding_vector"):
                try:
                    product["embedding_vector"] = json.loads(product["embedding_vector"])
                except Exception:
                    product["embedding_vector"] = None
            return product
    finally:
        conn.close()


def get_products_without_embeddings() -> list[dict]:
    """Return all products that do not yet have an embedding vector."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT product_name, features_text FROM products WHERE embedding_vector IS NULL"
            )
            columns = [col[0].lower() for col in cur.description]
            return [_normalize_row(columns, row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_all_products() -> list[dict]:
    """Return all products (without the embedding_vector blob)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, product_name, category, architecture, flash_kb, ram_kb,
                       gpio_pins, voltage_min, voltage_max, interfaces,
                       sensor_type, measurement_range, accuracy,
                       topology, output_voltage, output_current_a,
                       switching_frequency_khz, efficiency,
                       memory_type, capacity_mb, speed,
                       max_speed_mhz, package_type, temp_range,
                       interface, output_type, features_text,
                       created_at, updated_at
                FROM products
                ORDER BY id
            """)
            columns = [col[0].lower() for col in cur.description]
            return [_normalize_row(columns, row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_structured_candidates(base_product: dict, top_n: int = 50) -> list[dict]:
    """
    Find candidate alternatives in the same category that meet minimum spec requirements.
    Includes the embedding_vector CLOB so vector_search can use it.
    """
    category = base_product.get("category")
    if not category:
        return []

    conditions = [
        "category = :category",
        "product_name != :product_name",
    ]
    params: dict = {
        "category": category,
        "product_name": base_product["product_name"],
        "top_n": top_n,
    }

    if base_product.get("flash_kb") is not None:
        conditions.append("(flash_kb IS NULL OR flash_kb >= :flash_kb)")
        params["flash_kb"] = base_product["flash_kb"]

    if base_product.get("ram_kb") is not None:
        conditions.append("(ram_kb IS NULL OR ram_kb >= :ram_kb)")
        params["ram_kb"] = base_product["ram_kb"]

    if base_product.get("gpio_pins") is not None:
        conditions.append("(gpio_pins IS NULL OR gpio_pins >= :gpio_pins)")
        params["gpio_pins"] = base_product["gpio_pins"]

    if base_product.get("output_current_a") is not None:
        conditions.append("(output_current_a IS NULL OR output_current_a >= :output_current_a)")
        params["output_current_a"] = base_product["output_current_a"]

    if base_product.get("topology"):
        conditions.append("(topology IS NULL OR LOWER(topology) = LOWER(:topology))")
        params["topology"] = base_product["topology"]

    if base_product.get("sensor_type"):
        conditions.append("(sensor_type IS NULL OR LOWER(sensor_type) = LOWER(:sensor_type))")
        params["sensor_type"] = base_product["sensor_type"]

    where_clause = " AND ".join(conditions)

    # Oracle uses FETCH FIRST n ROWS ONLY instead of LIMIT
    query = f"""
        SELECT id, product_name, category, architecture, flash_kb, ram_kb,
               gpio_pins, voltage_min, voltage_max, interfaces,
               sensor_type, measurement_range, accuracy,
               topology, output_voltage, output_current_a,
               switching_frequency_khz, efficiency,
               memory_type, capacity_mb, speed,
               max_speed_mhz, package_type, temp_range,
               interface, output_type, features_text,
               embedding_vector
        FROM products
        WHERE {where_clause}
        FETCH FIRST :top_n ROWS ONLY
    """

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            columns = [col[0].lower() for col in cur.description]
            results = []
            for row in cur.fetchall():
                product = _normalize_row(columns, row)
                # Parse embedding CLOB back to list if present
                if product.get("embedding_vector"):
                    try:
                        product["embedding_vector"] = json.loads(product["embedding_vector"])
                    except Exception:
                        product["embedding_vector"] = None
                results.append(product)
            return results
    finally:
        conn.close()


def _default_product_fields() -> dict:
    """Return a dict of all product columns set to None for safe MERGE."""
    return {
        "product_name": None, "category": None, "architecture": None,
        "flash_kb": None, "ram_kb": None, "gpio_pins": None,
        "voltage_min": None, "voltage_max": None, "interfaces": None,
        "sensor_type": None, "measurement_range": None, "accuracy": None,
        "topology": None, "output_voltage": None, "output_current_a": None,
        "switching_frequency_khz": None, "efficiency": None,
        "memory_type": None, "capacity_mb": None, "speed": None,
        "max_speed_mhz": None, "package_type": None, "temp_range": None,
        "interface": None, "output_type": None, "features_text": None,
    }
