import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PolarVeritySenseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Polar Verity Sense."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        
        self._discovered_devices[discovery_info.address] = discovery_info
        
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.context["title_placeholders"]["name"],
                data={},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders=self.context["title_placeholders"],
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user-initiated setup."""
        if user_input is not None:
            address = user_input["device"]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            
            discovery_info = self._discovered_devices[address]
            
            return self.async_create_entry(
                title=discovery_info.name or discovery_info.address,
                data={},
            )

        # Scan for Polar devices
        current_addresses = self._async_current_ids()
        
        for discovery_info in async_discovered_service_info(self.hass):
            if (
                discovery_info.address in current_addresses
                or not discovery_info.name
                or "Polar" not in discovery_info.name
            ):
                continue
            
            self._discovered_devices[discovery_info.address] = discovery_info

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): vol.In(
                        {
                            address: f"{info.name} ({address})"
                            for address, info in self._discovered_devices.items()
                        }
                    ),
                }
            ),
        )
