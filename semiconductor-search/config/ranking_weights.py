"""Category-specific scoring weights and rule directions."""

RANKING_CONFIG = {
    "transistor": {
        "weights": {
            "vds_max_v": 30,
            "id_max_a": 25,
            "rds_on_ohm": 30,
            "gate_charge_nc": 10,
            "package_type": 15,
        },
        "rules": {
            "vds_max_v": "gte",
            "id_max_a": "gte",
            "rds_on_ohm": "lte",
            "gate_charge_nc": "lte",
        },
    },
    "microcontroller": {
        "weights": {
            "flash_kb": 35,
            "ram_kb": 25,
            "gpio_pins": 20,
            "max_speed_mhz": 20,
        },
        "rules": {
            "flash_kb": "gte",
            "ram_kb": "gte",
            "gpio_pins": "gte",
        },
    },
    "sensor": {
        "weights": {
            "accuracy": 40,
            "interface": 20,
            "package_type": 10,
        },
        "rules": {},
    },
    "power_ic": {
        "weights": {
            "output_current_a": 40,
            "switching_frequency_khz": 30,
            "package_type": 10,
        },
        "rules": {
            "output_current_a": "gte",
        },
    },
    "default": {
        "weights": {
            "voltage_max": 30,
            "output_current_a": 30,
            "package_type": 10,
        },
        "rules": {
            "voltage_max": "gte",
            "output_current_a": "gte",
        },
    },
}
