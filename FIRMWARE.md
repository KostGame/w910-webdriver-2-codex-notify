# W910 firmware extraction status

- Analysis date: 2026-07-22 KST.
- MCU firmware dump: not extracted.
- Software-only dump path: not found.
- Exact per-LED animation algorithms: **`UNKNOWN`**.

## Evidence

- Official package: `20250806171839.zip`.
- Installer: `SXS-W910_V1.0.4.exe` only.
- Extracted host payload: 803 UI, configuration, executable, and library files.
- Firmware payloads: no `.bin`, `.hex`, `.fw`, `.rom`, or `.dfu` files.
- Nested ZIP files: `Ndevice.json` UI resources only.
- `AutoUpdate`: host-application updater using `VersionInfo.json` and an omitted `AutoUpdate.exe`.
- `RemoteFirmWareVersion` and `DongleFirmWareVersion`: unused generic DevDock fields.
- Connected device: `YXT K100 Keyboard`, `B6A4:4100`, `bcdDevice 0x0100`.
- USB interfaces: three composite HID interfaces only.
- Missing interfaces: DFU, mass storage, serial, and vendor bootloader.
- `dfu-util -l`: no DFU device.
- `probe-rs list`: no debug probe.
- Lighting traffic: 25-byte mode header and parameter records only.
- Missing lighting traffic: LED frames and program bytecode.

## Firmware identity

| Command / selector | Length | Response | Meaning |
| --- | ---: | --- | --- |
| `F0 / 1` | 8 | `2.3.0001` | MCU firmware version |
| `F0 / 2` | 16 | `K2008-250612` plus NUL padding | Custom/build identifier |
| `F1 / 1` | 8 | all zero | Dongle firmware not reported |

- Earlier selector-0 result: empty request echo.
- Status: superseded by selector-specific readback.
- Identity responses: strings only; no flash-read primitive.

## Lighting records

| Code | Vendor mode | Stored controls |
| ---: | --- | --- |
| `81` | Constant | Brightness, one color |
| `82` | Flowing Water | Brightness, speed, direction, seven colors |
| `83` | Horse Race | Brightness, speed, direction |
| `84` | Single-color Breathing | Brightness, speed, one color |
| `85` | Cycle Breathing | Brightness, speed, seven colors |
| `86` | Tetris Blocks | Brightness, speed, seven colors |
| `87` | Neon | Brightness, speed |
| `88` | Ambilight | Brightness, speed, direction |
| `89` | Off | None |

- Detail record: speed, direction, inverted brightness, color mask, and seven `[G,R,B]` colors.
- Confirmed source: vendor UI state, HID captures, and direct readback.
- Manual claim: nine lighting modes only.
- Unavailable details: LED order, phase, easing, update rate, interpolation, and exact brightness curve.

## Safety boundary

- Unknown HID writes: not attempted.
- Risks: bootloader entry, configuration erasure, undocumented flash operation, or device loss.
- Allowed probes: known read-format requests only.
- Hardware under test: single connected keyboard.

## Required hardware work

1. Open the case.
2. Photograph both PCB sides.
3. Identify the MCU and test pads.
4. Confirm power, ground, reset, and SWD/JTAG/ISP pins from the MCU datasheet.
5. Connect a compatible debug probe without voltage contention.
6. Read identification and protection registers before erase or unlock operations.
7. Dump flash only when readout protection permits non-destructive access.
8. Correlate disassembly with controlled recordings of all nine lighting modes.

- Readout protection warning: unlocking commonly erases flash.
- Completion boundary: PCB access, MCU identification, and a compatible debug probe.
