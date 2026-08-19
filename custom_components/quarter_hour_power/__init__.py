from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import QuarterHourPowerCoordinator

PLATFORMS = [Platform.SENSOR]


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when options such as the entity name prefix change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = QuarterHourPowerCoordinator(hass, entry)
    await coordinator.async_initialize()
    hass.data.setdefault(entry.domain, {})[entry.entry_id] = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: QuarterHourPowerCoordinator = hass.data[entry.domain].pop(entry.entry_id)
        await coordinator.async_shutdown()
    return unload_ok
