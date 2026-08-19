from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import UnitOfEnergy
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import CONF_GRID_ENERGY, CONF_HOUSE_ENERGY, CONF_NAME_PREFIX, DOMAIN

_ALLOWED_ENERGY_UNITS = {
    UnitOfEnergy.WATT_HOUR,
    UnitOfEnergy.KILO_WATT_HOUR,
    UnitOfEnergy.MEGA_WATT_HOUR,
}
_ALLOWED_STATE_CLASSES = {"total", "total_increasing"}


def _energy_sensor_error(hass, entity_id: str | None) -> str | None:
    """Validate a cumulative energy sensor without requiring device_class=energy."""
    if not entity_id:
        return None

    state = hass.states.get(entity_id)
    if state is None:
        return "entity_not_found"

    unit = state.attributes.get("unit_of_measurement")
    if unit not in _ALLOWED_ENERGY_UNITS:
        return "invalid_energy_unit"

    state_class = state.attributes.get("state_class")
    if state_class not in _ALLOWED_STATE_CLASSES:
        return "invalid_state_class"

    return None


class QuarterHourPowerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            grid = user_input[CONF_GRID_ENERGY]
            house = user_input.get(CONF_HOUSE_ENERGY) or None

            grid_error = _energy_sensor_error(self.hass, grid)
            house_error = _energy_sensor_error(self.hass, house)
            if grid_error:
                errors[CONF_GRID_ENERGY] = grid_error
            if house_error:
                errors[CONF_HOUSE_ENERGY] = house_error

            if not errors:
                prefix = user_input.get(CONF_NAME_PREFIX, "").strip()
                data = {
                    CONF_GRID_ENERGY: grid,
                    CONF_NAME_PREFIX: prefix,
                }
                if house:
                    data[CONF_HOUSE_ENERGY] = house
                title = f"Quarter Hour Power - {prefix}" if prefix else "Quarter Hour Power"
                return self.async_create_entry(title=title, data=data)

        schema = vol.Schema(
            {
                vol.Required(CONF_GRID_ENERGY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_HOUSE_ENERGY): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Optional(CONF_NAME_PREFIX, default=""): selector.TextSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler."""
        return QuarterHourPowerOptionsFlow()


class QuarterHourPowerOptionsFlow(config_entries.OptionsFlow):
    """Allow changing sources and presentation options without recreating the integration."""

    async def async_step_init(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            grid = user_input[CONF_GRID_ENERGY]
            house = user_input.get(CONF_HOUSE_ENERGY) or None

            grid_error = _energy_sensor_error(self.hass, grid)
            house_error = _energy_sensor_error(self.hass, house)
            if grid_error:
                errors[CONF_GRID_ENERGY] = grid_error
            if house_error:
                errors[CONF_HOUSE_ENERGY] = house_error

            if not errors:
                prefix = user_input.get(CONF_NAME_PREFIX, "").strip()
                data = {
                    CONF_GRID_ENERGY: grid,
                    CONF_NAME_PREFIX: prefix,
                }
                if house:
                    data[CONF_HOUSE_ENERGY] = house
                return self.async_create_entry(title="", data=data)

        current_grid = self.config_entry.options.get(
            CONF_GRID_ENERGY,
            self.config_entry.data[CONF_GRID_ENERGY],
        )
        current_house = self.config_entry.options.get(
            CONF_HOUSE_ENERGY,
            self.config_entry.data.get(CONF_HOUSE_ENERGY),
        )
        current_prefix = self.config_entry.options.get(
            CONF_NAME_PREFIX,
            self.config_entry.data.get(CONF_NAME_PREFIX, ""),
        )
        schema_fields: dict = {
            vol.Required(CONF_GRID_ENERGY, default=current_grid): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
        }
        if current_house:
            schema_fields[vol.Optional(CONF_HOUSE_ENERGY, default=current_house)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
        else:
            schema_fields[vol.Optional(CONF_HOUSE_ENERGY)] = selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
        schema_fields[vol.Optional(CONF_NAME_PREFIX, default=current_prefix)] = selector.TextSelector()
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(schema_fields), errors=errors
        )
