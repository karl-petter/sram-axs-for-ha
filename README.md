# SRAM AXS for Home Assistant

A custom Home Assistant integration that reads battery status from SRAM AXS components (shifter, command post/dropper post) via Bluetooth Low Energy.

![Entity card showing battery levels for Command Post and Shifter](images/screenshot-entity-card.png)

## Features

- **Battery level** sensor (%) for each paired component
- **Last Read** timestamp sensor showing when the value was last fetched from the device
- **Low battery repair issue** — automatically raised in Settings → Repairs when battery drops below 20%, clears when it recovers. No automation needed.
- Values persist across HA restarts — shows last known reading until the bike is in range again
- Event-driven: reads trigger when the component wakes up (button press), not on a fixed timer
- Auto-discovery: HA detects SRAM AXS devices automatically when they are in BLE range

## Supported components

Any SRAM AXS component that exposes the standard BLE Battery Service should work. Confirmed working:

- AXS Command Post (dropper post controller)
- AXS Shifter (road/gravel)

## Requirements

- Home Assistant with Bluetooth support (Raspberry Pi built-in BT, or a USB BLE adapter)
- SRAM AXS components within BLE range of the HA host (~5–10m line of sight; walls reduce range)
- No ANT+ dongle or additional hardware needed

> **Tip:** If your bike is stored in a garage or room with poor BLE coverage, an [ESPHome Bluetooth proxy](https://esphome.io/components/bluetooth_proxy.html) on an ESP32 (~€5–10) placed near the bike dramatically improves connection reliability.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=karl-petter&repository=sram-axs-for-ha&category=integration)

Or add manually in HACS:

1. Open HACS → **⋮ → Custom repositories**
2. Add `https://github.com/karl-petter/sram-axs-for-ha` with category **Integration**
3. Search for *SRAM AXS* and install
4. Restart Home Assistant

### Manual

Copy the `custom_components/sram_axs/` folder into your HA `config/custom_components/` directory and restart Home Assistant.

## Configuration

1. Wake your SRAM AXS components by pressing a button on each one.
2. In HA go to **Settings → Devices & Services**.
3. A discovery notification for *SRAM AXS* should appear automatically. If not, click **Add Integration** and search for *SRAM AXS*.
4. The setup wizard will ask what type of component it is (Shifter, Command Post, etc.).
5. Repeat for each component.

## How it works

SRAM AXS components expose a standard Bluetooth GATT Battery Service (`0x180F`) alongside several proprietary SRAM services. This integration reads the Battery Level characteristic (`0x2A19`) which returns a value from 0–100.

Components only broadcast BLE advertisements when awake (after a button press). The integration registers a callback for each device's BLE address and connects to read the battery level whenever an advertisement is detected — no polling timer is used. The debounce window is 5 minutes, so rapid button presses only trigger one read per session.

## Dashboard card

Add this to your Lovelace dashboard to see all components at a glance:

```yaml
type: entities
title: Bike
entities:
  - entity: sensor.sram_axs_command_post_battery
  - entity: sensor.sram_axs_command_post_last_read
  - entity: sensor.sram_axs_shifter_battery
  - entity: sensor.sram_axs_shifter_last_read
```

## Low battery automation example

```yaml
alias: "Warn when SRAM battery is low"
triggers:
  - trigger: numeric_state
    entity_id:
      - sensor.sram_axs_command_post_battery
      - sensor.sram_axs_shifter_battery
    below: 20
conditions: []
actions:
  - action: notify.mobile_app
    data:
      message: "{{ trigger.to_state.name }} is at {{ trigger.to_state.state }}%"
mode: single
```

## Roadmap

- [ ] Explore SRAM proprietary BLE services for additional data (gear position, shift count, post position) via HCI snoop log analysis

## Contributing

Open source, non-commercial. PRs and issues welcome.

## License

MIT
