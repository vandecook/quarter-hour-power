<p align="center">
  <img
    src="https://raw.githubusercontent.com/vandecook/quarter-hour-power/main/custom_components/quarter_hour_power/brand/icon.png"
    width="128"
    alt="Quarter Hour Power"
  >
</p>

# Quarter Hour Power

Home Assistant custom integration for fixed 15-minute power-demand analysis from cumulative energy sensors.

[![Validate](https://github.com/vandecook/quarter-hour-power/actions/workflows/validate.yml/badge.svg)](https://github.com/vandecook/quarter-hour-power/actions/workflows/validate.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://www.hacs.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


## Requirements

- Minimum supported Home Assistant version: **2025.1.0**
- Recommended: latest stable Home Assistant release

Older Home Assistant versions are not part of the supported compatibility target.

## What it does

Quarter Hour Power calculates fixed quarter-hour average power values from cumulative energy meters. It is intended for demand/peak analysis where 15-minute intervals are relevant.

The grid-import energy sensor is required. A house-consumption energy sensor is optional. If the house source is configured, the integration also calculates how much of the house load was not supplied by the grid.

The integration intentionally uses cumulative **energy** sensors as its primary data source. Instantaneous power sensors are not integrated internally.

## Inputs

Required:

- Grid import energy: cumulative `Wh`, `kWh` or `MWh`
- `state_class`: `total` or `total_increasing`

Optional:

- House consumption energy: cumulative `Wh`, `kWh` or `MWh`
- `state_class`: `total` or `total_increasing`

PV production, battery power and grid export are not required. When a house source is configured, the difference between house consumption and grid import is treated as local supply / grid-import reduction. A battery is therefore intentionally not analysed separately.

## Calculation

At fixed quarter-hour boundaries the integration calculates the completed interval:

- Grid power = delta grid energy / 0.25 h
- House power = delta house energy / 0.25 h
- Grid reduction = max(house power - grid power, 0)
- Grid reduction percent = grid reduction / house power * 100

Intervals are rejected if the elapsed time is not approximately 15 minutes or if a cumulative energy counter moves backwards. This avoids turning a missed interval into a false demand peak.

## Entities

With only a grid source configured:

- Grid Power 15 min
- Grid Power Peak Month

With the optional house source configured, additional entities are provided:

- House Power 15 min
- Grid Reduction 15 min
- Grid Reduction 15 min Percent
- House Power At Grid Peak
- Grid Reduction At Grid Peak
- Grid Reduction At Grid Peak Percent
- House Power Peak Month
- Grid Power At House Peak
- Grid Reduction At House Peak
- Grid Reduction At House Peak Percent

Peak sensors include the corresponding peak timestamp in their attributes.

## Prefix and multiple instances

An optional entity-name prefix can be configured. This is useful when multiple instances are used in parallel, for example:

- `Total Grid Power Peak Month`
- `AMIS Grid Power Peak Month`

The prefix is not part of the entity `unique_id`, so changing it does not intentionally create a new logical entity for an existing config entry.

## Changing source entities

Grid and house energy sources can be changed later under **Settings -> Devices & services -> Quarter Hour Power -> Configure**.

When a source changes:

- applicable current-month peaks are preserved,
- the active 15-minute baseline is discarded,
- the next quarter-hour boundary establishes a fresh baseline,
- the following complete quarter hour produces the first value from the new source.

This prevents cumulative counters from different sources from being mixed in one interval.

## Recorder recovery

The integration stores its current state per Home Assistant config entry. If an integration entry is deleted and recreated, that config-entry-specific store is no longer available.

Quarter Hour Power therefore attempts to restore current-month peak information and the last published interval values from Home Assistant Recorder history. The cumulative-energy baseline itself is intentionally not reconstructed: after recreation, a fresh baseline is established at the next quarter-hour boundary.

For best recovery results, keep Recorder history for the generated entities and reuse the same entity-name prefix when recreating an instance.

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Add `https://github.com/vandecook/quarter-hour-power` as a custom repository of type **Integration**.
3. Install **Quarter Hour Power**.
4. Restart Home Assistant.
5. Go to **Settings -> Devices & services -> Add integration -> Quarter Hour Power**.
6. Select the cumulative grid-import energy sensor and, optionally, a cumulative house-consumption energy sensor.

### Manual

Copy:

`custom_components/quarter_hour_power`

to:

`/config/custom_components/quarter_hour_power`

Restart Home Assistant and add **Quarter Hour Power** from **Settings -> Devices & services**.

## Updating

When installed through HACS, install a newer GitHub release through HACS and restart Home Assistant when requested.

For a manual installation, replace the files under `/config/custom_components/quarter_hour_power/` with the files from the new version and restart Home Assistant. Do not delete the integration config entry merely to update the code.

## Version

Current integration version: **0.1.5**

## License

MIT License. See [LICENSE](LICENSE).
