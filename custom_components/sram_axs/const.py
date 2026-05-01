from __future__ import annotations

DOMAIN = "sram_axs"
DEVICE_NAME_PREFIX = "SRAM "

# Standard BLE Battery Service (confirmed working on both SRAM AXS devices)
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

# SRAM proprietary service prefix — used to fingerprint devices in advertisements
SRAM_SERVICE_UUID_PREFIX = "d905"

CONF_ADDRESS = "address"
CONF_NAME = "name"
CONF_COMPONENT_TYPE = "component_type"

COMPONENT_TYPE_COMMAND_POST = "command_post"
COMPONENT_TYPE_SHIFTER = "shifter"
COMPONENT_TYPE_UNKNOWN = "unknown"

COMPONENT_TYPES: dict[str, str] = {
    COMPONENT_TYPE_COMMAND_POST: "Command Post",
    COMPONENT_TYPE_SHIFTER: "Shifter",
    COMPONENT_TYPE_UNKNOWN: "Unknown",
}

# Seconds between BLE reads — battery changes slowly, no need to hammer the connection
READ_DEBOUNCE_SECONDS = 300  # 5 minutes

# Battery level below which a HA Repair issue is raised
BATTERY_LOW_THRESHOLD = 20

# BLE connection timeout
CONNECT_TIMEOUT = 10.0
