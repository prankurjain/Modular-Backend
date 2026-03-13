"""
Oracle Database client using python-oracledb.

Embeddings are stored as JSON in CLOB for local cosine ranking.
"""

import json
import oracledb
from config.settings import ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN


def get_connection():
    if not ORACLE_USER or not ORACLE_PASSWORD:
        raise RuntimeError(
            "Oracle credentials are not configured. "
            "Set ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, ORACLE_PORT, and ORACLE_SERVICE_NAME."
        )
    return oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD, dsn=ORACLE_DSN)


def initialize_schema():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM user_tables WHERE table_name = 'PRODUCTS'")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    CREATE TABLE products (
                        id                      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                        product_name            VARCHAR2(255) NOT NULL,
                        part_number             VARCHAR2(255),
                        category                VARCHAR2(100),
                        manufacturer            VARCHAR2(255),
                        datasheet_url           VARCHAR2(1000),
                        architecture            VARCHAR2(100),
                        flash_kb                NUMBER,
                        ram_kb                  NUMBER,
                        gpio_pins               NUMBER(10),
                        voltage_min             NUMBER,
                        voltage_max             NUMBER,
                        interfaces              VARCHAR2(500),
                        sensor_type             VARCHAR2(100),
                        measurement_range       VARCHAR2(200),
                        accuracy                VARCHAR2(100),
                        topology                VARCHAR2(100),
                        output_voltage          VARCHAR2(100),
                        output_current_a        NUMBER,
                        switching_frequency_khz NUMBER,
                        efficiency              VARCHAR2(50),
                        memory_type             VARCHAR2(100),
                        capacity_mb             NUMBER,
                        speed                   VARCHAR2(100),
                        max_speed_mhz           NUMBER,
                        package_type            VARCHAR2(100),
                        temp_range              VARCHAR2(100),
                        interface               VARCHAR2(200),
                        output_type             VARCHAR2(100),
                        transistor_type         VARCHAR2(100),
                        polarity                VARCHAR2(100),
                        vce_max_v               NUMBER,
                        vds_max_v               NUMBER,
                        ic_max_a                NUMBER,
                        id_max_a                NUMBER,
                        power_dissipation_w     NUMBER,
                        gain_hfe                NUMBER,
                        rds_on_ohm              NUMBER,
                        gate_charge_nc          NUMBER,
                        features_text           CLOB,
                        embedding_vector        CLOB,
                        created_at              TIMESTAMP DEFAULT SYSTIMESTAMP,
                        updated_at              TIMESTAMP DEFAULT SYSTIMESTAMP,
                        CONSTRAINT uq_product_name UNIQUE (product_name),
                        CONSTRAINT uq_part_number UNIQUE (part_number)
                    )
                """)
            else:
                _ensure_column(cur, "PRODUCTS", "PART_NUMBER", "VARCHAR2(255)")
                _ensure_column(cur, "PRODUCTS", "MANUFACTURER", "VARCHAR2(255)")
                _ensure_column(cur, "PRODUCTS", "DATASHEET_URL", "VARCHAR2(1000)")
                _ensure_column(cur, "PRODUCTS", "TRANSISTOR_TYPE", "VARCHAR2(100)")
                _ensure_column(cur, "PRODUCTS", "POLARITY", "VARCHAR2(100)")
                _ensure_column(cur, "PRODUCTS", "VCE_MAX_V", "NUMBER")
                _ensure_column(cur, "PRODUCTS", "VDS_MAX_V", "NUMBER")
                _ensure_column(cur, "PRODUCTS", "IC_MAX_A", "NUMBER")
                _ensure_column(cur, "PRODUCTS", "ID_MAX_A", "NUMBER")
                _ensure_column(cur, "PRODUCTS", "POWER_DISSIPATION_W", "NUMBER")
                _ensure_column(cur, "PRODUCTS", "GAIN_HFE", "NUMBER")
                _ensure_column(cur, "PRODUCTS", "RDS_ON_OHM", "NUMBER")
                _ensure_column(cur, "PRODUCTS", "GATE_CHARGE_NC", "NUMBER")
                _ensure_unique_constraint(cur, "PRODUCTS", "UQ_PART_NUMBER", "part_number")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ensure_column(cur, table_name: str, column_name: str, ddl: str):
    cur.execute(
        "SELECT COUNT(*) FROM user_tab_cols WHERE table_name = :table_name AND column_name = :column_name",
        {"table_name": table_name, "column_name": column_name},
    )
    if cur.fetchone()[0] == 0:
        cur.execute(f"ALTER TABLE {table_name.lower()} ADD ({column_name.lower()} {ddl})")


def _ensure_unique_constraint(cur, table_name: str, constraint_name: str, column_name: str):
    cur.execute(
        "SELECT COUNT(*) FROM user_constraints WHERE table_name = :table_name AND constraint_name = :constraint_name",
        {"table_name": table_name, "constraint_name": constraint_name},
    )
    if cur.fetchone()[0] == 0:
        cur.execute(f"ALTER TABLE {table_name.lower()} ADD CONSTRAINT {constraint_name.lower()} UNIQUE ({column_name})")


def upsert_product(product: dict) -> int:
    conn = get_connection()
    try:
        merged = {**_default_product_fields(), **product}
        lookup_key = merged.get("part_number") or merged["product_name"]
        print("merged:", merged)
        print("lookup_key:", lookup_key)
        with conn.cursor() as cur:
            cur.execute(
                """
                MERGE INTO products tgt
                USING (SELECT :lookup_key AS lookup_key FROM dual) src
                ON (NVL(tgt.part_number, tgt.product_name) = src.lookup_key)
                WHEN MATCHED THEN UPDATE SET
                    category                 = :category,
                    manufacturer             = :manufacturer,
                    datasheet_url            = :datasheet_url,
                    architecture             = :architecture,
                    flash_kb                 = :flash_kb,
                    ram_kb                   = :ram_kb,
                    gpio_pins                = :gpio_pins,
                    voltage_min              = :voltage_min,
                    voltage_max              = :voltage_max,
                    interfaces               = :interfaces,
                    sensor_type              = :sensor_type,
                    measurement_range        = :measurement_range,
                    accuracy                 = :accuracy,
                    topology                 = :topology,
                    output_voltage           = :output_voltage,
                    output_current_a         = :output_current_a,
                    switching_frequency_khz  = :switching_frequency_khz,
                    efficiency               = :efficiency,
                    memory_type              = :memory_type,
                    capacity_mb              = :capacity_mb,
                    speed                    = :speed,
                    max_speed_mhz            = :max_speed_mhz,
                    package_type             = :package_type,
                    temp_range               = :temp_range,
                    interface                = :interface,
                    output_type              = :output_type,
                    transistor_type          = :transistor_type,
                    polarity                 = :polarity,
                    vce_max_v                = :vce_max_v,
                    vds_max_v                = :vds_max_v,
                    ic_max_a                 = :ic_max_a,
                    id_max_a                 = :id_max_a,
                    power_dissipation_w      = :power_dissipation_w,
                    gain_hfe                 = :gain_hfe,
                    rds_on_ohm               = :rds_on_ohm,
                    gate_charge_nc           = :gate_charge_nc,
                    features_text            = :features_text,
                    updated_at               = SYSTIMESTAMP
                WHEN NOT MATCHED THEN INSERT (
                    product_name, part_number, category, manufacturer, datasheet_url,
                    architecture, flash_kb, ram_kb, gpio_pins, voltage_min, voltage_max,
                    interfaces, sensor_type, measurement_range, accuracy,
                    topology, output_voltage, output_current_a, switching_frequency_khz,
                    efficiency, memory_type, capacity_mb, speed, max_speed_mhz,
                    package_type, temp_range, interface, output_type,
                    transistor_type, polarity, vce_max_v, vds_max_v,
                    ic_max_a, id_max_a, power_dissipation_w, gain_hfe,
                    rds_on_ohm, gate_charge_nc, features_text
                ) VALUES (
                    :product_name, :part_number, :category, :manufacturer, :datasheet_url,
                    :architecture, :flash_kb, :ram_kb, :gpio_pins, :voltage_min, :voltage_max,
                    :interfaces, :sensor_type, :measurement_range, :accuracy,
                    :topology, :output_voltage, :output_current_a, :switching_frequency_khz,
                    :efficiency, :memory_type, :capacity_mb, :speed, :max_speed_mhz,
                    :package_type, :temp_range, :interface, :output_type,
                    :transistor_type, :polarity, :vce_max_v, :vds_max_v,
                    :ic_max_a, :id_max_a, :power_dissipation_w, :gain_hfe,
                    :rds_on_ohm, :gate_charge_nc, :features_text
                )
                """,
                {**merged, "lookup_key": lookup_key},
            )
            cur.execute(
                "SELECT id FROM products WHERE NVL(part_number, product_name) = :lookup_key",
                {"lookup_key": lookup_key},
            )
            row = cur.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception as e:
        conn.rollback()
        import traceback
        print("upsert_product ERROR:", repr(e))
        traceback.print_exc()
        raise
    finally:
        conn.close()


def update_product_embedding(product_name: str, embedding: list[float]):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET embedding_vector = :emb WHERE NVL(part_number, product_name) = :name",
                {"emb": json.dumps(embedding), "name": product_name},
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _to_json_safe_value(value):
    if value is None:
        return None
    if hasattr(value, "read") and callable(value.read):
        return value.read()
    return value


def _normalize_row(columns: list[str], row: tuple) -> dict:
    product = {col: _to_json_safe_value(val) for col, val in zip(columns, row)}
    if product.get("embedding_vector"):
        try:
            product["embedding_vector"] = json.loads(product["embedding_vector"])
        except Exception:
            product["embedding_vector"] = None
    return product


def get_product_by_name(product_name: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE product_name = :name", {"name": product_name})
            row = cur.fetchone()
            if not row:
                return None
            columns = [c[0].lower() for c in cur.description]
            return _normalize_row(columns, row)
    finally:
        conn.close()


def get_product_by_part_number(part_number: str) -> dict | None:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM products WHERE LOWER(NVL(part_number, product_name)) = LOWER(:part_number)",
                {"part_number": part_number},
            )
            row = cur.fetchone()
            if not row:
                return None
            columns = [c[0].lower() for c in cur.description]
            return _normalize_row(columns, row)
    finally:
        conn.close()


def get_products_without_embeddings() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT product_name, part_number, features_text "
                "FROM products WHERE embedding_vector IS NULL"
            )
            columns = [c[0].lower() for c in cur.description]
            return [_normalize_row(columns, r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_products_with_embeddings() -> list[dict]:
    """Return products that have embeddings (for vector index sync jobs)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products WHERE embedding_vector IS NOT NULL ORDER BY id")
            columns = [c[0].lower() for c in cur.description]
            return [_normalize_row(columns, r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_all_products() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM products ORDER BY id")
            columns = [c[0].lower() for c in cur.description]
            return [_normalize_row(columns, r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_products_with_embeddings_by_category(category: str, exclude_lookup_key: str | None = None) -> list[dict]:
    """Return products in a category that already have embeddings (vector index source)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            params = {"category": category}
            query = (
                "SELECT * FROM products WHERE category = :category "
                "AND embedding_vector IS NOT NULL"
            )
            if exclude_lookup_key:
                query += " AND NVL(part_number, product_name) != :exclude_lookup_key"
                params["exclude_lookup_key"] = exclude_lookup_key
            query += " ORDER BY id"
            cur.execute(query, params)
            columns = [c[0].lower() for c in cur.description]
            return [_normalize_row(columns, r) for r in cur.fetchall()]
    finally:
        conn.close()


def get_structured_candidates(base_product: dict, top_n: int = 50) -> list[dict]:
    category = base_product.get("category")
    if not category:
        return []

    conditions = ["category = :category", "NVL(part_number, product_name) != :lookup_key"]
    params = {
        "category": category,
        "lookup_key": base_product.get("part_number") or base_product["product_name"],
        "top_n": top_n,
    }
    if base_product.get("vds_max_v") is not None:
        conditions.append("(vds_max_v IS NULL OR vds_max_v >= :vds_max_v)")
        params["vds_max_v"] = base_product["vds_max_v"]
    if base_product.get("vce_max_v") is not None:
        conditions.append("(vce_max_v IS NULL OR vce_max_v >= :vce_max_v)")
        params["vce_max_v"] = base_product["vce_max_v"]
    if base_product.get("ic_max_a") is not None:
        conditions.append("(ic_max_a IS NULL OR ic_max_a >= :ic_max_a)")
        params["ic_max_a"] = base_product["ic_max_a"]
    if base_product.get("id_max_a") is not None:
        conditions.append("(id_max_a IS NULL OR id_max_a >= :id_max_a)")
        params["id_max_a"] = base_product["id_max_a"]
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
    # if base_product.get("temp_range") is not None:
    # # temp_range here is expected to be a numeric value in Python
    #     raw_temp = base_product.get("temp_range")
    #     parsed_temp = parse_temp_to_float(raw_temp)

    #     if parsed_temp is not None:
    #         conditions.append(
    #             "(TEMP_RANGE IS NULL OR "
    #             "TO_NUMBER(REGEXP_SUBSTR(REPLACE(REPLACE(REPLACE(TEMP_RANGE, '°', ''), 'C', ''), 'c', ''), '[-+]?[0-9]+')) "
    #             "BETWEEN :temp_range_min AND :temp_range_max)"
    #         )
    #         params["temp_range_min"] = parsed_temp - 15
    #         params["temp_range_max"] = parsed_temp + 15

    if base_product.get("temp_range") is not None:
        raw_temp = base_product.get("temp_range")
        parsed_temp = parse_temp_to_float(raw_temp)
        
        if parsed_temp is not None:
            conditions.append(
                "("
                "TEMP_RANGE IS NULL OR "
                "TO_NUMBER(NULLIF("
                "  REGEXP_SUBSTR("
                "    REPLACE(REPLACE(REPLACE(UPPER(TEMP_RANGE), '°', ''), 'C', ''), ' ', ''),"  # remove °, C, and spaces
                "    '[-+]?[0-9]+'"
                "  ),"
                "  ''"
                ")) BETWEEN :temp_range_min AND :temp_range_max"
                ")"
            )
            params['temp_range_min'] = parsed_temp - 15
            params['temp_range_max'] = parsed_temp + 15    


    query = f"SELECT * FROM products WHERE {' AND '.join(conditions)} FETCH FIRST :top_n ROWS ONLY"
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            columns = [c[0].lower() for c in cur.description]
            return [_normalize_row(columns, r) for r in cur.fetchall()]
    finally:
        conn.close()


def _default_product_fields() -> dict:
    return {
        "product_name": None,
        "part_number": None,
        "category": None,
        "manufacturer": None,
        "datasheet_url": None,
        "architecture": None,
        "flash_kb": None,
        "ram_kb": None,
        "gpio_pins": None,
        "voltage_min": None,
        "voltage_max": None,
        "interfaces": None,
        "sensor_type": None,
        "measurement_range": None,
        "accuracy": None,
        "topology": None,
        "output_voltage": None,
        "output_current_a": None,
        "switching_frequency_khz": None,
        "efficiency": None,
        "memory_type": None,
        "capacity_mb": None,
        "speed": None,
        "max_speed_mhz": None,
        "package_type": None,
        "temp_range": None,
        "interface": None,
        "output_type": None,
        "transistor_type": None,
        "polarity": None,
        "vce_max_v": None,
        "vds_max_v": None,
        "ic_max_a": None,
        "id_max_a": None,
        "power_dissipation_w": None,
        "gain_hfe": None,
        "rds_on_ohm": None,
        "gate_charge_nc": None,
        "features_text": None,
    }


import re

def parse_temp_to_float(raw_temp):
    """
    Convert the base product temp_range to float.
    Expects raw_temp to be numeric (e.g. 25, -40, 85.0).
    Returns float or None.
    """
    if raw_temp is None:
        return None
    try:
        return float(raw_temp)
    except (TypeError, ValueError):
        return None
