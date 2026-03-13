CATEGORIES = {

    "microcontroller": {
        "important_attributes": [
            "architecture",
            "core",
            "max_speed_mhz",
            "flash_kb",
            "ram_kb",
            "eeprom_kb",
            "gpio_pins",
            "adc_channels",
            "timers",
            "interfaces",
            "voltage_min",
            "voltage_max",
            "package_type",
            "temp_range",
        ],

        "html_spec_map": {

            "core": "core",
            "cpu": "core",
            "processor": "core",
            "architecture": "architecture",

            "flash": "flash_kb",
            "flash memory": "flash_kb",
            "program memory": "flash_kb",

            "ram": "ram_kb",
            "sram": "ram_kb",
            "data ram": "ram_kb",

            "eeprom": "eeprom_kb",

            "gpio": "gpio_pins",
            "gpio pins": "gpio_pins",
            "i/o pins": "gpio_pins",
            "number of i/os": "gpio_pins",

            "adc": "adc_channels",
            "adc channels": "adc_channels",

            "timers": "timers",
            "timer": "timers",

            "interface": "interfaces",
            "communication interface": "interfaces",
            "peripherals": "interfaces",

            "clock speed": "max_speed_mhz",
            "cpu speed": "max_speed_mhz",
            "max clock frequency": "max_speed_mhz",

            "supply voltage": "voltage_range",
            "operating voltage": "voltage_range",

            "package": "package_type",
            "package case": "package_type",
            "package / case": "package_type",

            "operating temperature": "temp_range",
            "operating temperature range": "temp_range",
        },
    },


    "sensor": {
        "important_attributes": [
            "sensor_type",
            "measurement_range",
            "resolution",
            "accuracy",
            "interface",
            "output_type",
            "sampling_rate",
            "voltage_min",
            "voltage_max",
            "package_type",
            "temp_range",
        ],

        "html_spec_map": {

            "sensor type": "sensor_type",
            "type": "sensor_type",

            "measurement range": "measurement_range",
            "range": "measurement_range",

            "resolution": "resolution",
            "accuracy": "accuracy",

            "sampling rate": "sampling_rate",
            "data rate": "sampling_rate",
            "odr": "sampling_rate",

            "interface": "interface",
            "output interface": "interface",

            "output type": "output_type",
            "output": "output_type",

            "supply voltage": "voltage_range",
            "operating voltage": "voltage_range",

            "package": "package_type",
            "package case": "package_type",

            "operating temperature": "temp_range",
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
            "package_type",
            "temp_range",
        ],

        "html_spec_map": {

            "topology": "topology",
            "converter type": "topology",

            "input voltage": "input_voltage_range",
            "vin": "input_voltage_range",

            "output voltage": "output_voltage",
            "vout": "output_voltage",

            "output current": "output_current_a",
            "iout": "output_current_a",

            "switching frequency": "switching_frequency_khz",

            "efficiency": "efficiency",

            "package": "package_type",
            "package case": "package_type",

            "operating temperature": "temp_range",
        },
    },


    "memory": {
        "important_attributes": [
            "memory_type",
            "capacity_kb",
            "interface",
            "clock_speed_mhz",
            "voltage_min",
            "voltage_max",
            "package_type",
            "temp_range",
        ],

        "html_spec_map": {

            "memory type": "memory_type",

            "capacity": "capacity_kb",
            "density": "capacity_kb",

            "interface": "interface",

            "clock frequency": "clock_speed_mhz",
            "speed": "clock_speed_mhz",

            "supply voltage": "voltage_range",

            "package": "package_type",
            "package case": "package_type",

            "operating temperature": "temp_range",
        },
    },


    "transistor": {
        "important_attributes": [
            "transistor_type",
            "polarity",
            "vce_max_v",
            "vds_max_v",
            "ic_max_a",
            "id_max_a",
            "power_dissipation_w",
            "gain_hfe",
            "rds_on_ohm",
            "gate_charge_nc",
            "package_type",
            "temp_range",
        ],

        "html_spec_map": {

            # transistor type
            "transistor type": "transistor_type",
            "technology": "transistor_type",

            # polarity
            "polarity": "polarity",
            "channel type": "polarity",

            # voltage
            "collector emitter voltage": "vce_max_v",
            "collector-emitter voltage": "vce_max_v",
            "collector emitter voltage vceo": "vce_max_v",
            "vceo": "vce_max_v",

            "drain source voltage": "vds_max_v",
            "drain-source voltage": "vds_max_v",
            "vds": "vds_max_v",

            # current
            "collector current": "ic_max_a",
            "collector current ic": "ic_max_a",
            "collector current continuous": "ic_max_a",
            "ic": "ic_max_a",

            "drain current": "id_max_a",
            "id": "id_max_a",

            # power
            "power dissipation": "power_dissipation_w",
            "pd": "power_dissipation_w",

            # gain
            "dc current gain": "gain_hfe",
            "dc current gain hfe": "gain_hfe",
            "hfe": "gain_hfe",

            # mosfet parameters
            "rds(on)": "rds_on_ohm",
            "rds on": "rds_on_ohm",

            "gate charge": "gate_charge_nc",

            # package
            "package": "package_type",
            "package case": "package_type",
            "package / case": "package_type",

            # temperature
            "operating temperature": "temp_range",
            "operating temperature range": "temp_range",
        },
    },
}