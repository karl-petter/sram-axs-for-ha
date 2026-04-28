from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from bleak import BleakClient, BleakError

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothChange, BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import BATTERY_LEVEL_CHAR_UUID, CONNECT_TIMEOUT, DOMAIN, READ_DEBOUNCE_SECONDS

_LOGGER = logging.getLogger(__name__)


class SramAxsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manages BLE communication with a single SRAM AXS component."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"SRAM AXS {name}",
            update_interval=None,  # Push-driven: updates triggered by BLE advertisements
        )
        self.address = address
        self.device_name = name
        self._cancel_callback: Any = None
        self._last_read: datetime | None = None
        self._reading = False

    async def async_start(self) -> None:
        """Register BLE advertisement callback so we know when the device wakes up."""
        self._cancel_callback = bluetooth.async_register_callback(
            self.hass,
            self._on_advertisement,
            {"address": self.address, "connectable": True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )

    async def async_stop(self) -> None:
        if self._cancel_callback:
            self._cancel_callback()
            self._cancel_callback = None

    @callback
    def _on_advertisement(
        self,
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        """Fires when a BLE advertisement is received from the device.

        Schedules a battery read, but debounced so we don't hammer the connection
        every time the device sends an advertisement packet.
        """
        if self._reading:
            return
        now = datetime.utcnow()
        if (
            self._last_read is not None
            and (now - self._last_read).total_seconds() < READ_DEBOUNCE_SECONDS
        ):
            return
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> dict[str, Any]:
        if self._reading:
            # Another refresh is already running; return cached data rather than
            # opening a second parallel connection.
            if self.data is not None:
                return self.data
            raise UpdateFailed("Read already in progress and no cached data available")

        self._reading = True
        try:
            device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if device is None:
                # Device not currently visible in the BLE scanner. Return the
                # last known value so sensors keep showing a useful reading.
                if self.data is not None:
                    return self.data
                raise UpdateFailed(
                    f"Device {self.address} not found — wake the component and try again"
                )

            async with BleakClient(device, timeout=CONNECT_TIMEOUT) as client:
                raw = await client.read_gatt_char(BATTERY_LEVEL_CHAR_UUID)

            battery_level = raw[0]
            self._last_read = datetime.utcnow()
            _LOGGER.debug("%s battery: %d%%", self.device_name, battery_level)
            return {"battery_level": battery_level}

        except BleakError as err:
            _LOGGER.warning("BLE read failed for %s: %s", self.device_name, err)
            # Keep showing last known value rather than making the sensor unavailable.
            if self.data is not None:
                return self.data
            raise UpdateFailed(f"BLE connection failed: {err}") from err
        finally:
            self._reading = False
