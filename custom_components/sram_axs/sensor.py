from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COMPONENT_TYPES, CONF_COMPONENT_TYPE, CONF_NAME, DOMAIN
from .coordinator import SramAxsCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SramAxsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SramAxsBatterySensor(coordinator, entry)])


class SramAxsBatterySensor(CoordinatorEntity[SramAxsCoordinator], SensorEntity):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_has_entity_name = True
    _attr_name = "Battery"

    def __init__(
        self, coordinator: SramAxsCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        component_type = entry.data.get(CONF_COMPONENT_TYPE, "unknown")
        component_label = COMPONENT_TYPES.get(component_type, "Unknown")
        device_name = entry.data[CONF_NAME]

        self._attr_unique_id = f"{coordinator.address}_battery"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            name=f"SRAM AXS {component_label}",
            manufacturer="SRAM",
            model=f"AXS {component_label}",
            serial_number=device_name.removeprefix("SRAM "),
        )

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("battery_level")

    @property
    def extra_state_attributes(self) -> dict | None:
        if self.coordinator.data is None:
            return None
        last_read = self.coordinator.data.get("last_read")
        return {"last_read": last_read.isoformat() if last_read else None}

    @property
    def available(self) -> bool:
        # Show last known value even when the bike is out of BLE range.
        # Only unavailable before the first successful read.
        return self.coordinator.data is not None
