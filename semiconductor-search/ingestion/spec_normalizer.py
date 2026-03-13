"""Normalize raw spec values into typed product rows."""

from utils.value_parser import (
    parse_memory_kb,
    parse_voltage_range,
    parse_numeric,
    parse_list,
    parse_frequency_mhz,
    parse_frequency_khz,
    parse_current_a,
)
from utils.feature_builder import build_features_text


def normalize_specs(product_name: str, category: str, raw_specs: dict) -> dict:
    product = {
        "product_name": product_name,
        "part_number": raw_specs.get("part_number") or product_name,
        "category": category,
        "manufacturer": raw_specs.get("manufacturer"),
        "datasheet_url": raw_specs.get("datasheet_url"),
    }

    for field in ("voltage_range", "input_voltage_range"):
        raw_v = raw_specs.get(field)
        if raw_v:
            vmin, vmax = parse_voltage_range(raw_v)
            product["voltage_min"] = vmin
            product["voltage_max"] = vmax

    if raw_specs.get("architecture"):
        product["architecture"] = raw_specs["architecture"]
    if raw_specs.get("flash_kb"):
        product["flash_kb"] = parse_memory_kb(raw_specs["flash_kb"])
    if raw_specs.get("ram_kb"):
        product["ram_kb"] = parse_memory_kb(raw_specs["ram_kb"])
    if raw_specs.get("gpio_pins"):
        product["gpio_pins"] = int(parse_numeric(raw_specs["gpio_pins"]) or 0) or None
    if raw_specs.get("interfaces"):
        ifaces = parse_list(raw_specs["interfaces"])
        product["interfaces"] = ", ".join(ifaces) if ifaces else None
    if raw_specs.get("max_speed_mhz"):
        product["max_speed_mhz"] = parse_frequency_mhz(raw_specs["max_speed_mhz"])

    if raw_specs.get("sensor_type"):
        product["sensor_type"] = raw_specs["sensor_type"]
    if raw_specs.get("measurement_range"):
        product["measurement_range"] = raw_specs["measurement_range"]
    if raw_specs.get("accuracy"):
        product["accuracy"] = raw_specs["accuracy"]
    if raw_specs.get("interface"):
        product["interface"] = raw_specs["interface"]
    if raw_specs.get("output_type"):
        product["output_type"] = raw_specs["output_type"]

    if raw_specs.get("topology"):
        product["topology"] = raw_specs["topology"]
    if raw_specs.get("output_voltage"):
        product["output_voltage"] = raw_specs["output_voltage"]
    if raw_specs.get("output_current_a"):
        product["output_current_a"] = parse_current_a(raw_specs["output_current_a"])
    if raw_specs.get("switching_frequency_khz"):
        product["switching_frequency_khz"] = parse_frequency_khz(raw_specs["switching_frequency_khz"])
    if raw_specs.get("efficiency"):
        product["efficiency"] = raw_specs["efficiency"]

    if raw_specs.get("memory_type"):
        product["memory_type"] = raw_specs["memory_type"]
    if raw_specs.get("capacity_mb"):
        product["capacity_mb"] = parse_numeric(raw_specs["capacity_mb"])
    if raw_specs.get("speed"):
        product["speed"] = raw_specs["speed"]

    # MOSFET/transistor normalization
    if raw_specs.get("transistor_type"):
        product["transistor_type"] = raw_specs["transistor_type"]
    if raw_specs.get("polarity"):
        product["polarity"] = raw_specs["polarity"]
    if raw_specs.get("vce_max_v"):
        product["vce_max_v"] = parse_numeric(raw_specs["vce_max_v"])
    if raw_specs.get("vds_max_v"):
        product["vds_max_v"] = parse_numeric(raw_specs["vds_max_v"])
    if raw_specs.get("ic_max_a"):
        product["ic_max_a"] = parse_current_a(raw_specs["ic_max_a"])
    if raw_specs.get("id_max_a"):
        product["id_max_a"] = parse_current_a(raw_specs["id_max_a"])
    if raw_specs.get("power_dissipation_w"):
        product["power_dissipation_w"] = parse_numeric(raw_specs["power_dissipation_w"])
    if raw_specs.get("gain_hfe"):
        product["gain_hfe"] = parse_numeric(raw_specs["gain_hfe"])
    if raw_specs.get("rds_on_ohm"):
        raw = str(raw_specs["rds_on_ohm"]).lower().replace(" ", "")
        value = parse_numeric(raw)
        if value is not None and "m" in raw and "ohm" in raw:
            value /= 1000
        product["rds_on_ohm"] = value
    if raw_specs.get("gate_charge_nc"):
        product["gate_charge_nc"] = parse_numeric(raw_specs["gate_charge_nc"])

    if raw_specs.get("package_type"):
        product["package_type"] = raw_specs["package_type"]
    if raw_specs.get("temp_range"):
        product["temp_range"] = raw_specs["temp_range"]

    product["features_text"] = build_features_text(product)
    return product
