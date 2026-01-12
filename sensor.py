from __future__ import annotations

import logging
from datetime import timedelta

from bleak import BleakError
from bleak_retry_connector import (
    establish_connection,
    BleakClientWithServiceCache,
)

from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothScanningMode,
    async_ble_device_from_address,
    async_register_callback,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    BATTERY_LEVEL_CHAR_UUID,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Polar Verity Sense sensor."""
    
    coordinator = PolarBatteryCoordinator(hass, config_entry)
    await coordinator.async_config_entry_first_refresh()
    
    async_add_entities([PolarBatterySensor(coordinator, config_entry)])


class PolarBatteryCoordinator(DataUpdateCoordinator):
    """Coordinator to manage Polar Verity Sense data updates."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.config_entry = config_entry
        self.address = config_entry.unique_id
        self._device_available = False

        # Register callback for when device is discovered
        self._cancel_callback = async_register_callback(
            hass,
            self._async_device_detected,
            BluetoothCallbackMatcher(address=self.address),
            BluetoothScanningMode.ACTIVE,
        )

    @callback
    def _async_device_detected(
        self,
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        """Handle device detection."""
        # Device detected - mark as available and trigger update
        self._device_available = True
        self.async_set_updated_data(self.data)

    async def _async_update_data(self):
        """Fetch data from the device."""
        if not self._device_available:
            _LOGGER.debug("Device not available for update")
            return self.data

        ble_device = async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        
        if not ble_device:
            self._device_available = False
            raise UpdateFailed("Device not found")

        try:
            client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                self.address,
                disconnected_callback=lambda _: None,
            )
            
            try:
                battery_level = await client.read_gatt_char(BATTERY_LEVEL_CHAR_UUID)
                battery_percentage = int(battery_level[0])
                _LOGGER.debug("Read battery level: %s%%", battery_percentage)
                return battery_percentage
            finally:
                await client.disconnect()
                
        except (BleakError, TimeoutError) as err:
            self._device_available = False
            raise UpdateFailed(f"Failed to read battery: {err}") from err

    async def async_shutdown(self) -> None:
        """Shutdown coordinator."""
        if self._cancel_callback:
            self._cancel_callback()
        await super().async_shutdown()


class PolarBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Polar Verity Sense battery sensor."""

    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_has_entity_name = True
    _attr_name = "Battery"

    def __init__(
        self,
        coordinator: PolarBatteryCoordinator,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._attr_unique_id = f"{config_entry.unique_id}_battery"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.unique_id)},
            "name": config_entry.title,
            "manufacturer": "Polar",
            "model": "Verity Sense",
        }

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        return self.coordinator.data

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
