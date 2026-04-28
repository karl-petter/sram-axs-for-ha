# SRAM AXS — Home Assistant Integration Plan

## Goal

Expose battery status from SRAM AXS components as Home Assistant sensor entities for low-battery alerts.

---

## Confirmed Hardware

| Component | BLE Address | Device Name | Battery |
| --- | --- | --- | --- |
| Command Post | `f2:ee:77:38:d1:41` | `SRAM 1042267555` | 55% |
| Shifter | `ef:de:d6:27:23:5f` | `SRAM 1427171611` | 100% |

> Note: BLE addresses are random/private and may rotate. Device names (`SRAM <serial>`) are stable and should be used for identification.

---

## Confirmed BLE Services

Both devices expose:

| UUID | Name | Notes |
| --- | --- | --- |
| `0x1800` | Generic Access | Contains device name (`SRAM <serial>`) |
| `0x1801` | Generic Attribute | Standard |
| `0xFE51` | Unknown | Registered company service |
| `0x180F` | **Battery Service** | ✅ Returns 0–100 integer via characteristic `0x2A19` |
| `d905xxxx-90aa-4c7c-b036-1e01fb8eb7ee` | SRAM proprietary | Multiple services; command post has ~14, more than shifter |
| `adee0001-xxxx-453c-a069-007ea97a0add` | Unknown proprietary | 2 services seen |

**Key result**: Standard BLE Battery Service (`0x180F`) is confirmed working. No ANT+ dongle needed.

---

## Approach: Pure BLE via Home Assistant Bluetooth Integration

HA ships with `bleak` (Python BLE library) and a `bluetooth` integration framework. The integration will:

1. Scan for BLE advertisements containing the SRAM service UUID prefix
2. Identify devices by name pattern `SRAM \d+` (stable across address rotations)
3. Connect on demand, read Battery Level characteristic, disconnect
4. Expose one sensor entity per component, mark unavailable when out of range

---

## Integration Architecture

```text
SRAM AXS Components (BLE advertising)
        │
        ▼
HA Bluetooth stack (bleak / passive scanner)
        │  advertisement detected → name matches "SRAM \d+"
        ▼
DataUpdateCoordinator
  • Active BLE connect → read 0x180F / 0x2A19 → disconnect
  • Poll interval: 10 minutes (battery changes slowly)
  • Mark unavailable when device not seen for > 60 min
        │
        ▼
Sensor entities (per device)
  • battery_level  (%, device_class=battery, state_class=measurement)
  • component_type attribute (command_post / shifter / unknown)
        │
        ▼
HA UI + automations (low battery alerts)
```

---

## Implementation Phases

### Phase 1 — MVP battery sensors

- [ ] Scaffold `custom_components/sram_axs/`
- [ ] `manifest.json` with `bluetooth` dependency
- [ ] Config flow: passive BLE scan → show discovered SRAM devices → user picks + labels each
- [ ] `coordinator.py`: connect with bleak, read battery characteristic, disconnect
- [ ] `sensor.py`: battery level entity per device
- [ ] Handle unavailability (device out of range / bike away)
- [ ] Device registry: manufacturer = SRAM, name = device name, serial = numeric part

### Phase 2 — Explore proprietary services

- [ ] Enumerate characteristics inside `d905xxxx` services
- [ ] Identify any readable values (gear position, shift count, post position)
- [ ] Add additional sensor entities if useful data found

### Phase 3 — Reverse engineer proprietary SRAM services

Goal: understand what the `d905xxxx` services contain beyond battery level (gear position, shift count, command post position, etc.).

**Legal note**: Open source, non-commercial, own hardware, Sweden (EU Software Directive Article 6 — interoperability reverse engineering is explicitly permitted).

Steps in recommended order:

- [ ] **nRF Connect characteristic scan** — connect to each component, expand every `d905xxxx` service, tap Read on each characteristic. Note UUID + raw value for any that respond. Zero risk, no app involved.
- [ ] **Android HCI snoop log** — enable Bluetooth HCI snoop in Android developer options, open the SRAM AXS app and interact with both components (shift, raise/lower post), then pull the `btsnoop_hci.log` and analyse in Wireshark. Shows exactly what the app reads/writes without decompiling anything.
- [ ] **APK decompilation with jadx** — only needed if the HCI log contains payloads that are opaque without knowing the parsing logic. Download APK, run `jadx -d out/ armyknife.apk`, search for characteristic UUIDs.
- [ ] Map discovered data to new sensor entities (gear position, shift count, post position %)

App on Google Play: `com.sram.armyknife`

### Phase 4 — Polish

- [ ] HA repair issues for critically low battery
- [ ] `strings.json` / translations
- [ ] HACS-compatible `hacs.json` + README

---

## File Structure

```text
custom_components/sram_axs/
├── __init__.py          # setup_entry / unload_entry
├── manifest.json        # domain, bluetooth dependency
├── config_flow.py       # BLE scan + device picker
├── coordinator.py       # bleak connection + data fetch
├── sensor.py            # battery sensor entities
├── const.py             # UUIDs, domain, component type map
└── strings.json
```

---

## Key Constants (confirmed)

```python
DOMAIN = "sram_axs"
DEVICE_NAME_PREFIX = "SRAM "

# Standard BLE Battery Service
BATTERY_SERVICE_UUID = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL_CHAR_UUID = "00002a19-0000-1000-8000-00805f9b34fb"

# SRAM proprietary service prefix (for device detection in advertisements)
SRAM_SERVICE_PREFIX = "d905"
SRAM_SERVICE_BASE = "90aa-4c7c-b036-1e01fb8eb7ee"
```

---

## Key Constraints

- Components only broadcast when awake (after a button press / movement). Battery values will be hours old between rides — this is acceptable.
- BLE MAC addresses are randomised; use device name for stable identification.
- HA must run on a host with Bluetooth (RPi built-in, or USB BLE adapter). Most HassOS installs qualify.
- Only one BLE client connection at a time per device. Keep connections short (connect → read → disconnect).
