from __future__ import annotations

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import (
    COMPONENT_TYPES,
    CONF_ADDRESS,
    CONF_COMPONENT_TYPE,
    CONF_NAME,
    DEVICE_NAME_PREFIX,
    DOMAIN,
)


class SramAxsConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._address: str | None = None
        self._name: str | None = None
        self._discovered: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle auto-discovery when HA spots a 'SRAM *' BLE advertisement."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._address = discovery_info.address
        self._name = discovery_info.name
        self.context["title_placeholders"] = {"name": self._name}

        return await self.async_step_select_type()

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle manual setup: scan and present nearby SRAM devices."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            self._address = address
            self._name = self._discovered[address].name
            return await self.async_step_select_type()

        configured = self._async_current_ids()
        self._discovered = {
            si.address: si
            for si in async_discovered_service_info(self.hass, connectable=True)
            if si.name
            and si.name.startswith(DEVICE_NAME_PREFIX)
            and si.address not in configured
        }

        if not self._discovered:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            addr: f"{si.name} ({addr})"
                            for addr, si in self._discovered.items()
                        }
                    )
                }
            ),
        )

    async def async_step_select_type(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Ask which type of component this is (command post, shifter, etc.)."""
        if user_input is not None:
            component_type = user_input[CONF_COMPONENT_TYPE]
            component_label = COMPONENT_TYPES[component_type]
            return self.async_create_entry(
                title=f"SRAM AXS {component_label}",
                data={
                    CONF_ADDRESS: self._address,
                    CONF_NAME: self._name,
                    CONF_COMPONENT_TYPE: component_type,
                },
            )

        return self.async_show_form(
            step_id="select_type",
            data_schema=vol.Schema(
                {vol.Required(CONF_COMPONENT_TYPE): vol.In(COMPONENT_TYPES)}
            ),
            description_placeholders={"name": self._name},
        )
