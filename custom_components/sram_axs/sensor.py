from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    RestoreSensor,
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
    async_add_entities([
        SramAxsBatterySensor(coordinator, entry),
        SramAxsLastReadSensor(coordinator, entry),
    ])


def _device_info(coordinator: SramAxsCoordinator, entry: ConfigEntry) -> DeviceInfo:
    component_type = entry.data.get(CONF_COMPONENT_TYPE, "unknown")
    component_label = COMPONENT_TYPES.get(component_type, "Unknown")
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.address)},
        name=f"SRAM AXS {component_label}",
        manufacturer="SRAM",
        model=f"AXS {component_label}",
        serial_number=entry.data[CONF_NAME].removeprefix("SRAM "),
    )


class SramAxsBatterySensor(CoordinatorEntity[SramAxsCoordinator], RestoreSensor):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_has_entity_name = True
    _attr_translation_key = "battery"
    _restored_value: int | None = None

    def __init__(self, coordinator: SramAxsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_battery"
        self._attr_device_info = _device_info(coordinator, entry)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.data is None:
            if (last := await self.async_get_last_sensor_data()) is not None:
                self._restored_value = last.native_value

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data is not None:
            return self.coordinator.data.get("battery_level")
        return self._restored_value

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None or self._restored_value is not None


class SramAxsLastReadSensor(CoordinatorEntity[SramAxsCoordinator], RestoreSensor):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_has_entity_name = True
    _attr_translation_key = "last_read"
    _restored_value: datetime | None = None

    def __init__(self, coordinator: SramAxsCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_last_read"
        self._attr_device_info = _device_info(coordinator, entry)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        if self.coordinator.data is None:
            if (last := await self.async_get_last_sensor_data()) is not None:
                self._restored_value = last.native_value

    @property
    def native_value(self) -> datetime | None:
        if self.coordinator.data is not None:
            return self.coordinator.data.get("last_read")
        return self._restored_value

    @property
    def available(self) -> bool:
        return self.coordinator.data is not None or self._restored_value is not None
