CATEGORIES = {
    "microcontroller": {
        "important_attributes": [
            "architecture",
            "flash_kb",
            "ram_kb",
            "gpio_pins",
            "voltage_min",
            "voltage_max",
            "interfaces",
        ],
        "html_spec_map": {
            "core": "architecture",
            "cpu": "architecture",
            "processor": "architecture",
            "flash": "flash_kb",
            "flash memory": "flash_kb",
            "program memory": "flash_kb",
            "program memory size": "flash_kb",
            "ram": "ram_kb",
            "sram": "ram_kb",
            "data ram": "ram_kb",
            "gpio": "gpio_pins",
            "gpio pins": "gpio_pins",
            "i/o pins": "gpio_pins",
            "number of i/os": "gpio_pins",
            "voltage": "voltage_range",
            "supply voltage": "voltage_range",
            "operating voltage": "voltage_range",
            "vcc": "voltage_range",
            "interface": "interfaces",
            "communication interface": "interfaces",
            "peripherals": "interfaces",
            "speed": "max_speed_mhz",
            "clock speed": "max_speed_mhz",
            "cpu speed": "max_speed_mhz",
            "max clock frequency": "max_speed_mhz",
            "package": "package_type",
            "package type": "package_type",
            "operating temperature": "temp_range",
            "temperature range": "temp_range",
        },
    },
    "sensor": {
        "important_attributes": [
            "sensor_type",
            "measurement_range",
            "accuracy",
            "interface",
            "voltage_min",
            "voltage_max",
            "output_type",
        ],
        "html_spec_map": {
            "sensor type": "sensor_type",
            "type": "sensor_type",
            "sensing element": "sensor_type",
            "measurement range": "measurement_range",
            "range": "measurement_range",
            "full scale range": "measurement_range",
            "accuracy": "accuracy",
            "resolution": "resolution",
            "interface": "interface",
            "output interface": "interface",
            "output type": "output_type",
            "output": "output_type",
            "supply voltage": "voltage_range",
            "operating voltage": "voltage_range",
            "vcc": "voltage_range",
            "operating temperature": "temp_range",
            "package": "package_type",
        },
    },
    "power_ic": {
        "important_attributes": [
            "topology",
            "input_voltage_min",
            "input_voltage_max",
            "output_voltage",
            "output_current_a",
            "switching_frequency_khz",
            "efficiency",
        ],
        "html_spec_map": {
            "topology": "topology",
            "converter type": "topology",
            "type": "topology",
            "input voltage": "input_voltage_range",
            "vin": "input_voltage_range",
            "input voltage range": "input_voltage_range",
            "output voltage": "output_voltage",
            "vout": "output_voltage",
            "output current": "output_current_a",
            "iout": "output_current_a",
            "maximum output current": "output_current_a",
            "switching frequency": "switching_frequency_khz",
            "frequency": "switching_frequency_khz",
            "efficiency": "efficiency",
            "package": "package_type",
            "operating temperature": "temp_range",
        },
    },
    "memory": {
        "important_attributes": [
            "memory_type",
            "capacity_mb",
            "interface",
            "voltage_min",
            "voltage_max",
            "speed",
        ],
        "html_spec_map": {
            "memory type": "memory_type",
            "type": "memory_type",
            "capacity": "capacity_mb",
            "density": "capacity_mb",
            "interface": "interface",
            "bus interface": "interface",
            "supply voltage": "voltage_range",
            "operating voltage": "voltage_range",
            "access time": "speed",
            "speed": "speed",
            "package": "package_type",
        },
    },

    # NEW: Transistor category
    "transistor": {
        "important_attributes": [
            "transistor_type",        # BJT / MOSFET / IGBT etc.
            "polarity",               # NPN / PNP / N-channel / P-channel
            "vce_max_v",              # or vds_max_v, generic "max_voltage_v"
            "ic_max_a",               # or id_max_a, generic "max_current_a"
            "power_dissipation_w",
            "gain_hfe",               # or transconductance for MOSFET if desired
            "rds_on_ohm",             # mostly for MOSFETs
            "package_type",
        ],
        "html_spec_map": {
            # Type / Structure
            "transistor type": "transistor_type",
            "type": "transistor_type",
            "device type": "transistor_type",
            "technology": "transistor_type",
            "structure": "transistor_type",
            "configuration": "transistor_type",

            # Polarity
            "polarity": "polarity",
            "channel type": "polarity",
            "channel": "polarity",

            # Voltage ratings
            "collector emitter voltage": "vce_max_v",
            "collector-emitter voltage": "vce_max_v",
            "vceo": "vce_max_v",
            "vces": "vce_max_v",
            "drain source voltage": "vds_max_v",
            "drain-source voltage": "vds_max_v",
            "vds": "vds_max_v",
            "maximum voltage": "max_voltage_v",

            # Current ratings
            "collector current": "ic_max_a",
            "ic": "ic_max_a",
            "drain current": "id_max_a",
            "id": "id_max_a",
            "maximum current": "max_current_a",

            # Power
            "power dissipation": "power_dissipation_w",
            "total power dissipation": "power_dissipation_w",
            "pd": "power_dissipation_w",

            # Gain / transconductance
            "dc current gain": "gain_hfe",
            "hfe": "gain_hfe",
            "gain": "gain_hfe",
            "transconductance": "transconductance",

            # On-resistance (MOSFET)
            "on resistance": "rds_on_ohm",
            "on-resistance": "rds_on_ohm",
            "rds(on)": "rds_on_ohm",
            "rds on": "rds_on_ohm",

            # Package & temperature
            "package": "package_type",
            "case": "package_type",
            "package type": "package_type",
            "operating temperature": "temp_range",
            "junction temperature": "temp_range",
            "storage temperature": "temp_range",
        },
    },
}