from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import QuarterHourPowerCoordinator
from .const import CONF_NAME_PREFIX, DOMAIN


@dataclass(frozen=True)
class SensorDescription:
    key: str
    name: str
    value_fn: Callable[[Any], float | None]
    unit: str
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT
    requires_house: bool = False


SENSORS = (
    SensorDescription("grid_power", "Grid Power 15 min", lambda s: s.grid_power_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER),
    SensorDescription("house_power", "House Power 15 min", lambda s: s.house_power_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, requires_house=True),
    SensorDescription("reduction", "Grid Reduction 15 min", lambda s: s.reduction_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, requires_house=True),
    SensorDescription("reduction_percent", "Grid Reduction 15 min Percent", lambda s: s.reduction_percent, PERCENTAGE, None, requires_house=True),
    SensorDescription("grid_peak", "Grid Power Peak Month", lambda s: s.grid_peak_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER),
    SensorDescription("grid_peak_house", "House Power At Grid Peak", lambda s: s.grid_peak_house_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, requires_house=True),
    SensorDescription("grid_peak_reduction", "Grid Reduction At Grid Peak", lambda s: s.grid_peak_reduction_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, requires_house=True),
    SensorDescription("grid_peak_reduction_percent", "Grid Reduction At Grid Peak Percent", lambda s: s.grid_peak_reduction_percent, PERCENTAGE, None, requires_house=True),
    SensorDescription("house_peak", "House Power Peak Month", lambda s: s.house_peak_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, requires_house=True),
    SensorDescription("house_peak_grid", "Grid Power At House Peak", lambda s: s.house_peak_grid_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, requires_house=True),
    SensorDescription("house_peak_reduction", "Grid Reduction At House Peak", lambda s: s.house_peak_reduction_kw, UnitOfPower.KILO_WATT, SensorDeviceClass.POWER, requires_house=True),
    SensorDescription("house_peak_reduction_percent", "Grid Reduction At House Peak Percent", lambda s: s.house_peak_reduction_percent, PERCENTAGE, None, requires_house=True),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: QuarterHourPowerCoordinator = hass.data[DOMAIN][entry.entry_id]
    descriptions = [
        desc for desc in SENSORS
        if coordinator.house_entity is not None or not desc.requires_house
    ]
    entities = [QuarterHourPowerSensor(coordinator, entry, desc) for desc in descriptions]
    entities.append(QuarterHourPowerStatusSensor(coordinator, entry))
    async_add_entities(entities)


class QuarterHourPowerSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: QuarterHourPowerCoordinator, entry: ConfigEntry, description: SensorDescription) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self.description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        prefix = entry.options.get(CONF_NAME_PREFIX, entry.data.get(CONF_NAME_PREFIX, "")).strip()
        self._attr_name = f"{prefix} {description.name}" if prefix else description.name
        self._attr_native_unit_of_measurement = description.unit
        self._attr_device_class = description.device_class
        self._attr_state_class = description.state_class
        self._remove_listener = None

    @property
    def native_value(self):
        return self.description.value_fn(self.coordinator.state)

    @property
    def extra_state_attributes(self):
        state = self.coordinator.state
        attrs = {
            "interval_start": state.interval_start,
            "interval_end": state.interval_end,
            "invalid_intervals": state.invalid_intervals,
            "source_grid_energy": self.coordinator.grid_entity,
            "source_house_energy": self.coordinator.house_entity,
            "house_analysis_enabled": self.coordinator.house_entity is not None,
            "restored_from_history": state.restored_from_history,
            "restored_at": state.restored_at,
            "grid_source_changed_at": state.grid_source_changed_at,
            "house_source_changed_at": state.house_source_changed_at,
        }
        if self.description.key.startswith("grid_peak"):
            attrs["peak_time"] = state.grid_peak_time
        if self.description.key.startswith("house_peak"):
            attrs["peak_time"] = state.house_peak_time
        return attrs

    async def async_added_to_hass(self) -> None:
        @callback
        def handle_update() -> None:
            self.async_write_ha_state()

        self._remove_listener = self.coordinator.async_add_listener(handle_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None


class QuarterHourPowerStatusSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:stethoscope"

    def __init__(self, coordinator: QuarterHourPowerCoordinator, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_status"
        prefix = entry.options.get(CONF_NAME_PREFIX, entry.data.get(CONF_NAME_PREFIX, "")).strip()
        self._attr_name = f"{prefix} Quarter Hour Power Status" if prefix else "Quarter Hour Power Status"
        self._remove_listener = None

    @property
    def native_value(self):
        return self.coordinator.state.last_interval_status

    @property
    def extra_state_attributes(self):
        state = self.coordinator.state
        attrs = {
            "last_valid_interval": state.last_valid_interval,
            "last_interval_start": state.interval_start,
            "last_interval_end": state.interval_end,
            "grid_delta_kwh": state.last_grid_delta_kwh,
            "grid_power_kw": state.grid_power_kw,
            "grid_source": self.coordinator.grid_entity,
            "history_recovery": state.history_recovery_status,
            "discarded_intervals": state.invalid_intervals,
            "last_discard_reason": state.last_discard_reason,
        }

        # Grid-only mode deliberately exposes no house-related attributes.
        if self.coordinator.house_entity is not None:
            attrs.update({
                "house_delta_kwh": state.last_house_delta_kwh,
                "house_power_kw": state.house_power_kw,
                "reduction_kw": state.reduction_kw,
                "reduction_percent": state.reduction_percent,
                "house_source": self.coordinator.house_entity,
            })

        return attrs

    async def async_added_to_hass(self) -> None:
        @callback
        def handle_update() -> None:
            self.async_write_ha_state()

        self._remove_listener = self.coordinator.async_add_listener(handle_update)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None
