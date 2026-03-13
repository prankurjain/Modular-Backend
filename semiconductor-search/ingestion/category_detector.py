"""Category detection helpers for ingestion/search flows."""

from config.categories_config import CATEGORIES


KEY_FIELDS_BY_CATEGORY = {
    "microcontroller": {"architecture", "flash_kb", "ram_kb", "gpio_pins", "interfaces"},
    "sensor": {"sensor_type", "measurement_range", "accuracy", "output_type"},
    "power_ic": {"topology", "output_voltage", "output_current_a", "switching_frequency_khz"},
    "memory": {"memory_type", "capacity_kb", "clock_speed_mhz"},
    "transistor": {"vce_max_v", "vds_max_v", "ic_max_a", "id_max_a", "rds_on_ohm", "gate_charge_nc"},
}


def detect_category(raw_specs: dict, hint: str | None = None) -> str:
    """Detect category from parsed canonical spec keys, with optional hint fallback."""
    if hint and hint.lower().strip() in CATEGORIES:
        return hint.lower().strip()

    keys = {k for k, v in (raw_specs or {}).items() if v not in (None, "")}
    best_category = None
    best_score = -1

    for category, key_fields in KEY_FIELDS_BY_CATEGORY.items():
        score = len(keys.intersection(key_fields))
        if score > best_score:
            best_score = score
            best_category = category

    if best_score <= 0:
        return (hint or "transistor").lower().strip() if hint else "transistor"
    return best_category or "transistor"
