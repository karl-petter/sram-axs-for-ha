from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from bleak import BleakClient, BleakError
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothChange, BluetoothServiceInfoBleak
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import BATTERY_LEVEL_CHAR_UUID, CONNECT_TIMEOUT, DOMAIN, READ_DEBOUNCE_SECONDS

_LOGGER = logging.getLogger(__name__)


class SramAxsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manages BLE communication with a single SRAM AXS component."""

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"SRAM AXS {name}",
            update_interval=None,
        )
        self.address = address
        self.device_name = name
        self._cancel_callback: Any = None
        self._last_read: datetime | None = None
        self._reading = False

    async def async_start(self) -> None:
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
        if self._reading:
            return
        now = datetime.now(UTC)
        if (
            self._last_read is not None
            and (now - self._last_read).total_seconds() < READ_DEBOUNCE_SECONDS
        ):
            return
        # Pass the BLE device object directly — we have it right now while the
        # device is awake. Re-looking it up later via async_ble_device_from_address
        # races against the device going back to sleep.
        self.hass.async_create_task(self._async_read(service_info.device))

    async def _async_read(self, device: BLEDevice) -> None:
        self._reading = True
        try:
            client = await establish_connection(
                BleakClient, device, self.device_name, max_attempts=3
            )
            try:
                raw = await client.read_gatt_char(BATTERY_LEVEL_CHAR_UUID)
            finally:
                await client.disconnect()

            self._last_read = datetime.now(UTC)
            battery_level = raw[0]
            _LOGGER.debug("%s battery: %d%%", self.device_name, battery_level)
            self.async_set_updated_data(
                {"battery_level": battery_level, "last_read": self._last_read}
            )

        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("BLE read failed for %s: %s", self.device_name, err)
        finally:
            self._reading = False
