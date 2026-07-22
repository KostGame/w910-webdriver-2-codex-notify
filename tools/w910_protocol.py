#!/usr/bin/env python3
"""Codec and data model for the YXT/SXS W910 configuration protocol.

The module is transport independent.  ``Frame.to_report()`` produces the exact
41-byte Feature Report used by USB HID report ID 6; the same frame bytes are
hex-encoded by the vendor application for BLE FFF1.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Literal, Mapping, NamedTuple


REPORT_ID = 0x06
REPORT_SIZE = 41
MAX_DATA = 32
MAIN_RECORD_COUNT = 160
SCROLL_RECORD_COUNT = 4
ACTION_SIZE = 4
MACRO_MAX_SIZE = 512


@dataclass(frozen=True)
class Frame:
    command: int
    sequence: int
    selector: int = 0
    address: int = 0
    data: bytes = b""

    def __post_init__(self) -> None:
        for name, value, limit in (
            ("command", self.command, 0xFF),
            ("sequence", self.sequence, 0xFF),
            ("selector", self.selector, 0xFF),
            ("address", self.address, 0xFFFF),
        ):
            if not 0 <= value <= limit:
                raise ValueError(f"{name} out of range: {value}")
        if len(self.data) > MAX_DATA:
            raise ValueError(f"frame data exceeds {MAX_DATA} bytes")

    def to_report(self) -> bytes:
        report = bytearray(REPORT_SIZE)
        report[0:4] = bytes((REPORT_ID, 0x00, 0x01, self.command))
        report[4] = self.sequence
        report[5] = self.selector
        report[6:8] = self.address.to_bytes(2, "little")
        report[8] = len(self.data)
        report[9 : 9 + len(self.data)] = self.data
        return bytes(report)

    @classmethod
    def from_report(cls, report: bytes) -> "Frame":
        if len(report) != REPORT_SIZE:
            raise ValueError(f"feature report must be {REPORT_SIZE} bytes")
        if report[0] != REPORT_ID or report[1:3] != b"\x00\x01":
            raise ValueError("not a W910 report-ID-6 protocol frame")
        length = report[8]
        if length > MAX_DATA:
            raise ValueError(f"invalid frame payload length: {length}")
        return cls(
            command=report[3],
            sequence=report[4],
            selector=report[5],
            address=int.from_bytes(report[6:8], "little"),
            data=bytes(report[9 : 9 + length]),
        )

    @classmethod
    def read_request(
        cls,
        write_command: int,
        sequence: int,
        selector: int = 0,
        address: int = 0,
        length: int = 0,
    ) -> "Frame":
        if not 0 <= write_command < 0x80:
            raise ValueError("write command must be below 0x80")
        if not 0 <= length <= MAX_DATA:
            raise ValueError("read length out of range")
        # A read request advertises the requested size in byte 8 even though it
        # has no meaningful request payload.  Zero bytes reproduce that wire form.
        return cls(write_command | 0x80, sequence, selector, address, bytes(length))


class PhysicalControl(NamedTuple):
    index: int
    default_ui_value: int

    @property
    def address(self) -> int:
        return self.index * ACTION_SIZE


# The controller scans six rows of eight action slots.  Only the first three
# records in each row are connected on the W910; the remaining 142 records are
# generic DevDock capacity and are written as [02,00,00,00].
MAIN_CONTROLS: dict[str, PhysicalControl] = {
    "key_esc": PhysicalControl(0, 0x29),
    "key_x": PhysicalControl(1, 0x1B),
    "rgb_light_switch": PhysicalControl(2, 306),
    "key_b": PhysicalControl(8, 0x05),
    "key_v": PhysicalControl(9, 0x19),
    "mode_switch_press": PhysicalControl(10, 312),
    "key_c": PhysicalControl(16, 0x06),
    "key_enter": PhysicalControl(17, 0x28),
    "mode_switch_up": PhysicalControl(18, 0x52),
    "key_d": PhysicalControl(24, 0x07),
    "key_left_shift": PhysicalControl(25, 0xE1),
    "mode_switch_down": PhysicalControl(26, 0x51),
    "key_e": PhysicalControl(32, 0x08),
    "key_k": PhysicalControl(33, 0x0E),
    "mode_switch_left": PhysicalControl(34, 0x50),
    "key_tab": PhysicalControl(40, 0x2B),
    "key_r": PhysicalControl(41, 0x15),
    "mode_switch_right": PhysicalControl(42, 0x4F),
}

SCROLL_CONTROLS: dict[str, PhysicalControl] = {
    "scroll_up": PhysicalControl(0, 0xE9),
    "scroll_down": PhysicalControl(1, 0xEA),
}

VENDOR_PROFILE_KEYS: dict[str, str] = {
    "key_esc": "btn_KBKey_Esc",
    "key_x": "btn_KBKey_X",
    "rgb_light_switch": "btn_KBKey_LedModeLoop",
    "key_b": "btn_KBKey_B",
    "key_v": "btn_KBKey_V",
    "mode_switch_press": "btn_KBKey_ProfileLoop",
    "key_c": "btn_KBKey_C",
    "key_enter": "btn_KBKey_Enter",
    "mode_switch_up": "btn_KBKey_Up",
    "key_d": "btn_KBKey_D",
    "key_left_shift": "btn_KBKey_LShift",
    "mode_switch_down": "btn_KBKey_Down",
    "key_e": "btn_KBKey_E",
    "key_k": "btn_KBKey_K",
    "mode_switch_left": "btn_KBKey_Left",
    "key_tab": "btn_KBKey_Tab",
    "key_r": "btn_KBKey_R",
    "mode_switch_right": "btn_KBKey_Right",
}

VENDOR_SCROLL_KEYS: dict[str, str] = {
    "scroll_up": "btn_KB_Scr_Up0",
    "scroll_down": "btn_KB_Scr_Dn0",
}


# Values accepted by the vendor UI function encoder (FUN_0047e870).  This also
# includes generic DevDock entries hidden by the W910 skin, so an open client can
# round-trip imported profiles without losing them.
UI_FUNCTION_RECORDS: dict[int, bytes] = {
    255: b"\x00\x00\x00\x00",  # no function
    300: b"\x03\x01\x00\x00",  # system power
    301: b"\x03\x02\x00\x00",  # sleep
    302: b"\x03\x04\x00\x00",  # wake
    303: b"\x04\xE2\x00\x00",  # mute
    304: b"\x05\x01\x00\x00",  # vertical wheel one direction
    305: b"\x05\x81\x00\x00",  # vertical wheel other direction
    306: b"\x07\x01\x00\x00",  # LED mode loop
    307: b"\x07\x02\x00\x00",  # LED speed loop
    308: b"\x07\x03\x00\x00",  # LED brightness loop
    309: b"\x07\x04\x00\x00",  # LED on/off
    310: b"\x09\x01\x00\x00",  # profile next (generic/hidden)
    311: b"\x09\x02\x00\x00",  # profile previous (generic/hidden)
    312: b"\x09\x03\x00\x00",  # profile loop
    313: b"\x09\x04\x00\x00",  # onboard profile slot 1
    314: b"\x09\x04\x01\x00",  # onboard profile slot 2
    317: b"\x04\x6F\x00\x00",  # display brightness down
    318: b"\x04\x70\x00\x00",  # display brightness up
    319: b"\x07\x03\x01\x00",  # LED brightness up
    320: b"\x07\x03\x02\x00",  # LED brightness down
    321: b"\x07\x02\x01\x00",  # LED speed up
    322: b"\x07\x02\x02\x00",  # LED speed down
    323: b"\x0B\x01\x00\x00",  # horizontal wheel one direction
    324: b"\x0B\x81\x00\x00",  # horizontal wheel other direction
    325: b"\x07\x06\x00\x00",  # generic LED color loop
    326: b"\x07\x06\x01\x00",
    327: b"\x07\x06\x02\x00",
    328: b"\x07\x06\x03\x00",
    387: b"\x04\x83\x01\x00",  # media player
    394: b"\x04\x8A\x01\x00",  # mail
    402: b"\x04\x92\x01\x00",  # calculator
    404: b"\x04\x94\x01\x00",  # my computer
    480: b"\x0D\x01\x01\x00",  # Windows key locked
    481: b"\x0D\x01\x02\x00",  # Windows key unlocked
    482: b"\x0D\x01\x03\x00",  # Windows key lock toggle
    483: b"\x0D\x02\x01\x00",  # Alt+F4 locked
    484: b"\x0D\x02\x02\x00",  # Alt+F4 unlocked
    485: b"\x0D\x02\x03\x00",  # Alt+F4 lock toggle
    486: b"\x0D\x03\x01\x00",  # all keys locked
    487: b"\x0D\x03\x02\x00",  # all keys unlocked
    488: b"\x0D\x03\x03\x00",  # all-key lock toggle
    489: b"\x0E\x01\x00\x00",  # Windows mode
    490: b"\x0E\x02\x00\x00",  # macOS mode
    491: b"\x0E\x03\x00\x00",  # Windows/macOS toggle
    545: b"\x04\x21\x02\x00",  # web search
    547: b"\x04\x23\x02\x00",  # browser/home
    548: b"\x04\x24\x02\x00",  # web back
    549: b"\x04\x25\x02\x00",  # web forward
    550: b"\x04\x26\x02\x00",  # web stop
    551: b"\x04\x27\x02\x00",  # web refresh
    554: b"\x04\x2A\x02\x00",  # bookmarks (hidden by W910 XML)
}

VISIBLE_SPECIAL_FUNCTIONS: tuple[tuple[str, int], ...] = (
    ("volume_down", 0xEA),
    ("volume_up", 0xE9),
    ("mute", 303),
    ("previous_track", 0xB6),
    ("stop", 0xB7),
    ("next_track", 0xB5),
    ("web_forward", 549),
    ("web_back", 548),
    ("web_search", 545),
    ("web_stop", 550),
    ("web_refresh", 551),
    ("play_pause", 0xCD),
    ("mail", 394),
    ("my_computer", 404),
    ("calculator", 402),
    ("media_player", 387),
    ("browser", 547),
    ("windows_key_lock_toggle", 482),
    ("alt_f4_lock_toggle", 485),
    ("all_key_lock_toggle", 488),
    ("windows_macos_toggle", 491),
    ("led_speed_loop", 307),
    ("led_brightness_loop", 308),
    ("led_mode_loop", 306),
    ("led_on_off", 309),
    ("no_function", 255),
    ("system_power", 300),
    ("sleep", 301),
    ("wake", 302),
    ("profile_loop", 312),
)

_DIRECT_CONSUMER = {0xB5, 0xB6, 0xB7, 0xCD, 0xE9, 0xEA}


def encode_ui_function(value: int) -> bytes:
    """Encode the integer stored in the vendor profile JSON as one action."""
    if value in UI_FUNCTION_RECORDS:
        return UI_FUNCTION_RECORDS[value]
    if value == 0xF1:
        return b"\x0C\x01\x00\x00"  # Fn
    if value in _DIRECT_CONSUMER:
        return bytes((0x04, value, 0, 0))
    if 0 <= value < 0xFF:
        return bytes((0x02, value, 0, 0))
    raise ValueError(f"unsupported vendor UI function value: {value}")


def encode_macro_action(slot: int, playback_mode: int) -> bytes:
    """Create [0A, mode, slot, 00]; modes are count=0, hold=1, toggle=2."""
    if not 0 <= slot <= 0xFF:
        raise ValueError("macro slot out of range")
    if playback_mode not in (0, 1, 2):
        raise ValueError("macro playback mode must be 0, 1, or 2")
    return bytes((0x0A, playback_mode, slot, 0))


def decode_action(record: bytes) -> dict[str, int | str]:
    if len(record) != ACTION_SIZE:
        raise ValueError("action record must be four bytes")
    reverse = {value: key for key, value in UI_FUNCTION_RECORDS.items()}
    if record in reverse:
        return {"kind": "ui_function", "value": reverse[record]}
    kind, arg0, arg1, arg2 = record
    if kind == 0x02 and arg1 == arg2 == 0:
        return {"kind": "keyboard", "usage": arg0}
    if kind == 0x04 and arg2 == 0:
        return {"kind": "consumer", "usage": arg0 | (arg1 << 8)}
    if kind == 0x0A and arg2 == 0:
        return {"kind": "macro", "mode": arg0, "slot": arg1}
    return {"kind": "raw", "value": int.from_bytes(record, "little")}


@dataclass(frozen=True)
class KeyboardEvent:
    usage: int
    pressed: bool
    delay_ms: int


@dataclass(frozen=True)
class MouseButtonEvent:
    button: Literal["left", "right", "middle", "back", "forward"]
    pressed: bool
    delay_ms: int = 0


@dataclass(frozen=True)
class MouseWheelEvent:
    # The vendor JSON calls this byte extVal.  Keeping the raw 0..255 value
    # makes imported/recorded macros lossless; 1 and 0xFF are the usual signs.
    value: int
    delay_ms: int = 0


@dataclass(frozen=True)
class MouseMoveEvent:
    x: int
    y: int
    delay_ms: int = 0


MacroEvent = KeyboardEvent | MouseButtonEvent | MouseWheelEvent | MouseMoveEvent


# FUN_0047f620 converts the macro editor's F1..F5 pseudo key codes into these
# otherwise-reserved compact event tags.  The non-numeric order is intentional.
MOUSE_BUTTON_TAGS = {
    "left": 0xE8,
    "right": 0xEA,
    "middle": 0xE9,
    "back": 0xEB,
    "forward": 0xEC,
}
MOUSE_TAG_BUTTONS = {tag: button for button, tag in MOUSE_BUTTON_TAGS.items()}


def _delay24(value: int) -> bytes:
    if not 0 <= value <= 0xFFFFFF:
        raise ValueError("macro delay does not fit in 24 bits")
    return value.to_bytes(3, "little")


def encode_macro_event(event: MacroEvent) -> bytes:
    if isinstance(event, KeyboardEvent):
        if not 0x04 <= event.usage <= 0xEC:
            raise ValueError("keyboard macro usage must be 0x04..0xEC")
        if not 0 <= event.delay_ms <= 0x100007E:
            raise ValueError("keyboard macro delay out of range")
        if event.delay_ms < 0x80:
            state_delay = event.delay_ms | (0 if event.pressed else 0x80)
            return bytes((event.usage, state_delay))
        state = 0x7F if event.pressed else 0xFF
        return bytes((event.usage, state, 0xFF)) + _delay24(event.delay_ms - 0x7F)

    if isinstance(event, MouseButtonEvent):
        if event.button not in MOUSE_BUTTON_TAGS:
            raise ValueError(f"unknown mouse button: {event.button}")
        if not 0 <= event.delay_ms <= 0x100007E:
            raise ValueError("mouse-button macro delay out of range")
        tag = MOUSE_BUTTON_TAGS[event.button]
        if event.delay_ms < 0x80:
            state_delay = event.delay_ms | (0 if event.pressed else 0x80)
            return bytes((tag, state_delay))
        state = 0x7F if event.pressed else 0xFF
        return bytes((tag, state, 0xFF)) + _delay24(event.delay_ms - 0x7F)

    if isinstance(event, MouseWheelEvent):
        if not 0 <= event.value <= 0xFF:
            raise ValueError("mouse-wheel extVal must be one byte")
        if not 0 <= event.delay_ms <= 0xFFFFFF:
            raise ValueError("mouse-wheel macro delay out of range")
        if event.delay_ms == 0:
            return bytes((0xFD, event.value))
        return bytes((0xFD, event.value, 0xFF)) + _delay24(event.delay_ms)

    if isinstance(event, MouseMoveEvent):
        if not -0x8000 <= event.x <= 0x7FFF or not -0x8000 <= event.y <= 0x7FFF:
            raise ValueError("mouse movement must fit signed 16 bits")
        xy = event.x.to_bytes(2, "little", signed=True) + event.y.to_bytes(
            2, "little", signed=True
        )
        if not 0 <= event.delay_ms <= 0x10000FE:
            raise ValueError("mouse movement delay out of range")
        if event.delay_ms < 0x100:
            return bytes((0xFE, event.delay_ms)) + xy
        return b"\xFE\xFF" + xy + b"\xFF" + _delay24(event.delay_ms - 0xFF)

    raise TypeError(f"unknown macro event: {type(event).__name__}")


def encode_macro(events: Iterable[MacroEvent], repeat_count: int = 1) -> bytes:
    if not 0 <= repeat_count <= 0xFFFF:
        raise ValueError("macro repeat count out of range")
    payload = b"".join(encode_macro_event(event) for event in events)
    stream = repeat_count.to_bytes(2, "little") + len(payload).to_bytes(2, "little") + payload
    if len(stream) > MACRO_MAX_SIZE:
        raise ValueError("macro stream exceeds 512-byte device limit")
    return stream


def vendor_macro_events(mac_data: Mapping[str, Any]) -> list[MacroEvent]:
    """Convert one manufacturer macro JSON ``macData`` object losslessly."""
    count = int(mac_data["num"])
    values = mac_data["macVal"]
    states = mac_data["macSta"]
    delays = mac_data["macDly"]
    extended = mac_data["extVal"]
    if any(len(array) < count for array in (values, states, delays, extended)):
        raise ValueError("vendor macro arrays are shorter than num")

    events: list[MacroEvent] = []
    ui_mouse_buttons = {
        0xF1: "left",
        0xF2: "right",
        0xF3: "middle",
        0xF4: "back",
        0xF5: "forward",
    }
    for index in range(count):
        value = int(values[index])
        state = int(states[index])
        delay = int(delays[index])
        ext = extended[index]
        if value in ui_mouse_buttons:
            events.append(MouseButtonEvent(ui_mouse_buttons[value], state == 1, delay))  # type: ignore[arg-type]
        elif value == 0xF8:
            events.append(MouseWheelEvent(int(ext[0]) & 0xFF, delay))
        elif value == 0xF6:
            x, y = int(ext[0]), int(ext[1])
            if state in (3, 4):
                x = -x
            if state in (3, 5):
                y = -y
            events.append(MouseMoveEvent(x, y, delay))
        elif 0x04 <= value <= 0xEC:
            events.append(KeyboardEvent(value, state == 1, delay))
        else:
            raise ValueError(f"unsupported vendor macro value 0x{value:X}")
    return events


def vendor_macro_stream(mac_data: Mapping[str, Any]) -> bytes:
    return encode_macro(
        vendor_macro_events(mac_data), repeat_count=int(mac_data.get("macRpt", 1))
    )


def decode_macro(stream: bytes) -> tuple[int, list[MacroEvent]]:
    if len(stream) < 4:
        raise ValueError("macro stream is shorter than its header")
    repeat = int.from_bytes(stream[0:2], "little")
    payload_length = int.from_bytes(stream[2:4], "little")
    if len(stream) != payload_length + 4:
        raise ValueError("macro payload length does not match header")
    data = stream[4:]
    events: list[MacroEvent] = []
    offset = 0
    while offset < len(data):
        tag = data[offset]
        if tag in MOUSE_TAG_BUTTONS:
            if offset + 2 > len(data):
                raise ValueError("truncated mouse-button macro event")
            state_delay = data[offset + 1]
            long_form = (
                state_delay in (0x7F, 0xFF)
                and offset + 3 <= len(data)
                and data[offset + 2] == 0xFF
            )
            if long_form:
                if offset + 6 > len(data):
                    raise ValueError("truncated long mouse-button macro event")
                delay = 0x7F + int.from_bytes(data[offset + 3 : offset + 6], "little")
                pressed = state_delay == 0x7F
                offset += 6
            else:
                pressed = state_delay < 0x80
                delay = state_delay & 0x7F
                offset += 2
            events.append(MouseButtonEvent(MOUSE_TAG_BUTTONS[tag], pressed, delay))
            continue

        if 0x04 <= tag <= 0xEC:
            if offset + 2 > len(data):
                raise ValueError("truncated keyboard macro event")
            state_delay = data[offset + 1]
            long_form = (
                state_delay in (0x7F, 0xFF)
                and offset + 3 <= len(data)
                and data[offset + 2] == 0xFF
            )
            if long_form:
                if offset + 6 > len(data):
                    raise ValueError("truncated long keyboard macro event")
                delay = 0x7F + int.from_bytes(data[offset + 3 : offset + 6], "little")
                pressed = state_delay == 0x7F
                offset += 6
            else:
                pressed = state_delay < 0x80
                delay = state_delay & 0x7F
                offset += 2
            events.append(KeyboardEvent(tag, pressed, delay))
            continue

        if tag == 0xFD:
            if offset + 2 > len(data):
                raise ValueError("truncated mouse-wheel macro event")
            value = data[offset + 1]
            if offset + 3 <= len(data) and data[offset + 2] == 0xFF:
                if offset + 6 > len(data):
                    raise ValueError("truncated delayed mouse-wheel event")
                delay = int.from_bytes(data[offset + 3 : offset + 6], "little")
                offset += 6
            else:
                delay = 0
                offset += 2
            events.append(MouseWheelEvent(value, delay))
            continue

        if tag == 0xFE:
            if offset + 6 > len(data):
                raise ValueError("truncated mouse-move macro event")
            delay = data[offset + 1]
            x = int.from_bytes(data[offset + 2 : offset + 4], "little", signed=True)
            y = int.from_bytes(data[offset + 4 : offset + 6], "little", signed=True)
            if delay == 0xFF and offset + 7 <= len(data) and data[offset + 6] == 0xFF:
                if offset + 10 > len(data):
                    raise ValueError("truncated long mouse-move event")
                delay = 0xFF + int.from_bytes(data[offset + 7 : offset + 10], "little")
                offset += 10
            else:
                offset += 6
            events.append(MouseMoveEvent(x, y, delay))
            continue

        raise ValueError(f"unknown macro event tag 0x{tag:02X} at offset {offset}")
    return repeat, events


def macro_write_frames(slot: int, sequence: int, stream: bytes) -> list[Frame]:
    if not 0 <= slot <= 0xFF:
        raise ValueError("macro slot out of range")
    if len(stream) > MACRO_MAX_SIZE:
        raise ValueError("macro stream exceeds device limit")
    return [
        Frame(0x08, (sequence + offset // MAX_DATA) & 0xFF, slot, offset, stream[offset : offset + MAX_DATA])
        for offset in range(0, len(stream), MAX_DATA)
    ]


LED_MODE_NAMES: dict[int, str] = {
    0x81: "constant",
    0x82: "flowing_water",
    0x83: "horse_race",
    0x84: "single_color_breathing",
    0x85: "cycle_breathing",
    0x86: "tetris_blocks",
    0x87: "neon",
    0x88: "ambilight",
    0x89: "off",
}


@dataclass(frozen=True)
class LightingRecord:
    speed: int = 3
    direction: int = 0
    brightness: int = 4
    enabled: tuple[bool, bool, bool, bool, bool, bool, bool] = (True,) * 7
    colors: tuple[
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
        tuple[int, int, int],
    ] = (
        (0xFC, 0xFF, 0x00),
        (0x00, 0x00, 0xFF),
        (0xFF, 0xA5, 0x00),
        (0x00, 0xFF, 0x00),
        (0xFF, 0x00, 0x00),
        (0x00, 0xFF, 0xFF),
        (0x80, 0x00, 0x80),
    )

    def encode(self) -> bytes:
        if not 0 <= self.speed <= 0xFF:
            raise ValueError("lighting speed out of range")
        if not 0 <= self.direction <= 0xFF:
            raise ValueError("lighting direction out of range")
        if not 1 <= self.brightness <= 6:
            raise ValueError("W910 brightness must be 1..6")
        if len(self.enabled) != 7 or len(self.colors) != 7:
            raise ValueError("lighting record requires exactly seven colors")
        mask = sum((1 << index) for index, state in enumerate(self.enabled) if state)
        result = bytearray((self.speed, self.direction, 6 - self.brightness, mask))
        for red, green, blue in self.colors:
            if any(not 0 <= component <= 0xFF for component in (red, green, blue)):
                raise ValueError("RGB component out of range")
            # This is the vendor firmware's unusual order, verified dynamically.
            result.extend((green, red, blue))
        return bytes(result)

    @classmethod
    def decode(cls, data: bytes) -> "LightingRecord":
        if len(data) != 25:
            raise ValueError("lighting mode record must be 25 bytes")
        colors = tuple(
            (data[offset + 1], data[offset], data[offset + 2])
            for offset in range(4, 25, 3)
        )
        mask = data[3]
        return cls(
            speed=data[0],
            direction=data[1],
            brightness=6 - data[2],
            enabled=tuple(bool(mask & (1 << index)) for index in range(7)),  # type: ignore[arg-type]
            colors=colors,  # type: ignore[arg-type]
        )


def lighting_frames(
    mode_code: int,
    record: LightingRecord | None,
    sequence: int,
    supported_bitmap: int = 0x01FF,
) -> list[Frame]:
    if mode_code not in LED_MODE_NAMES:
        raise ValueError("W910 LED mode code must be 0x81..0x89")
    header = bytes((mode_code,)) + supported_bitmap.to_bytes(2, "little") + bytes(22)
    frames = [Frame(0x09, sequence, 0, 0, header)]
    mode_number = mode_code & 0x3F
    if mode_number < 9:
        if record is None:
            raise ValueError("non-off LED mode needs a detail record")
        frames.append(Frame(0x09, (sequence + 1) & 0xFF, 0, mode_number * 25, record.encode()))
    elif record is not None:
        raise ValueError("off mode has no detail record")
    return frames


def vendor_profile_lighting(
    profile: Mapping[str, Any],
) -> tuple[int, LightingRecord | None]:
    """Decode the selected mode and detail from manufacturer ProfileN JSON."""
    led_modes = profile["KBconfig"]["KBled"]
    if len(led_modes) < 9:
        raise ValueError("vendor profile has fewer than nine W910 LED records")
    selected = int(led_modes[0]["curselmode"])
    if not 0 <= selected <= 8:
        raise ValueError("vendor W910 LED selection must be 0..8")
    mode_code = 0x81 + selected
    if mode_code == 0x89:
        return mode_code, None
    source = led_modes[selected]
    enabled: list[bool] = []
    colors: list[tuple[int, int, int]] = []
    for index in range(7):
        state, argb = source[f"ctrl_KBLed_Col{index}"]
        value = int(argb)
        enabled.append(bool(state))
        colors.append(((value >> 16) & 0xFF, (value >> 8) & 0xFF, value & 0xFF))
    return mode_code, LightingRecord(
        speed=int(source["frequencyvalue"]),
        direction=int(source["directionsel"]),
        brightness=int(source["brightnessvalue"]),
        enabled=tuple(enabled),  # type: ignore[arg-type]
        colors=tuple(colors),  # type: ignore[arg-type]
    )


def generation_token_bytes(token: int) -> bytes:
    if not 0 <= token <= 0xFFFF:
        raise ValueError("generation token out of range")
    return token.to_bytes(2, "big")


def timeout_bytes(minutes: int) -> bytes:
    seconds = minutes * 60
    if not 0 <= seconds <= 0xFFFF:
        raise ValueError("timeout in seconds does not fit uint16")
    return seconds.to_bytes(2, "little")


def blank_main_bank() -> list[bytes]:
    return [b"\x02\x00\x00\x00" for _ in range(MAIN_RECORD_COUNT)]


def default_main_bank() -> list[bytes]:
    """Return the official Profile0 Normal-layer main bank."""
    bank = blank_main_bank()
    for control in MAIN_CONTROLS.values():
        bank[control.index] = encode_ui_function(control.default_ui_value)
    return bank


def default_fn_main_bank() -> list[bytes]:
    """Return the official Profile0 Fn-layer main bank."""
    bank = default_main_bank()
    bank[MAIN_CONTROLS["rgb_light_switch"].index] = b"\x02\x00\x00\x00"
    bank[MAIN_CONTROLS["mode_switch_press"].index] = b"\x02\x00\x00\x00"
    bank[MAIN_CONTROLS["key_tab"].index] = encode_ui_function(491)
    return bank


def default_scroll_bank(fn_layer: bool = False) -> list[bytes]:
    """Return the four command-05 records written by the manufacturer app."""
    up = encode_ui_function(0xEA if fn_layer else 0xE9)
    down = encode_ui_function(0xE9 if fn_layer else 0xEA)
    return [up, down, b"\x02\x00\x00\x00", b"\x02\x00\x00\x00"]


@dataclass(frozen=True)
class VendorProfileBanks:
    normal_main: tuple[bytes, ...]
    fn_main: tuple[bytes, ...]
    normal_scroll: tuple[bytes, ...]
    fn_scroll: tuple[bytes, ...]
    macro_streams: dict[int, bytes]
    lighting_mode: int
    lighting: LightingRecord | None


def _vendor_macros_by_guid(
    macro_config: Mapping[str, Any],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    result: dict[tuple[str, str], Mapping[str, Any]] = {}
    for group in macro_config.get("MacroGrpInfo", []):
        group_guid = str(group["GrpGuid"])
        for macro in group.get("MacroInfo", []):
            result[(group_guid, str(macro["MacroGuid"]))] = macro["macData"]
    return result


def vendor_profile_banks(
    profile: Mapping[str, Any],
    macro_config: Mapping[str, Any] | None = None,
) -> VendorProfileBanks:
    """Translate a manufacturer ``ProfileN.json`` into all device banks.

    Values 700 and above are macro references.  Resolving those requires the
    matching manufacturer ``macroConfig.json`` so the playback mode and stream
    can be recovered from its GUID reference.
    """
    root = profile["KBconfig"]
    macros = _vendor_macros_by_guid(macro_config) if macro_config is not None else {}
    streams: dict[int, bytes] = {}

    def action(layer: str, macro_layer: str, field: str) -> bytes:
        value = int(root[layer][field])
        if value < 700:
            return encode_ui_function(value)
        reference = root[macro_layer][field]
        group_guid = str(reference["grpGuid"])
        macro_guid = str(reference["macGuid"])
        try:
            mac_data = macros[(group_guid, macro_guid)]
        except KeyError as error:
            raise ValueError(
                f"macro reference {group_guid}/{macro_guid} is not in macroConfig"
            ) from error
        slot_key = "FnMemMacId" if layer == "FnKey" else "MemMacId"
        slot = int(reference[slot_key])
        stream = vendor_macro_stream(mac_data)
        if slot in streams and streams[slot] != stream:
            raise ValueError(f"two different macros claim device slot {slot}")
        streams[slot] = stream
        return encode_macro_action(slot, int(mac_data["rptType"]))

    def main_bank(layer: str, macro_layer: str) -> tuple[bytes, ...]:
        bank = blank_main_bank()
        for name, control in MAIN_CONTROLS.items():
            bank[control.index] = action(layer, macro_layer, VENDOR_PROFILE_KEYS[name])
        return tuple(bank)

    def scroll_bank(layer: str, macro_layer: str) -> tuple[bytes, ...]:
        bank = [b"\x02\x00\x00\x00" for _ in range(SCROLL_RECORD_COUNT)]
        for name, control in SCROLL_CONTROLS.items():
            bank[control.index] = action(layer, macro_layer, VENDOR_SCROLL_KEYS[name])
        return tuple(bank)

    lighting_mode, lighting = vendor_profile_lighting(profile)
    return VendorProfileBanks(
        normal_main=main_bank("KBKey", "KBKeyMacro"),
        fn_main=main_bank("FnKey", "FnKeyMacro"),
        normal_scroll=scroll_bank("KBKey", "KBKeyMacro"),
        fn_scroll=scroll_bank("FnKey", "FnKeyMacro"),
        macro_streams=streams,
        lighting_mode=lighting_mode,
        lighting=lighting,
    )


def iter_bank_write_frames(
    command: int,
    selector: int,
    records: Iterable[bytes],
    sequence: int,
) -> Iterator[Frame]:
    packed = b"".join(records)
    if len(packed) % ACTION_SIZE:
        raise ValueError("bank contains a non-four-byte action")
    for address in range(0, len(packed), MAX_DATA):
        yield Frame(
            command,
            (sequence + address // MAX_DATA) & 0xFF,
            selector,
            address,
            packed[address : address + MAX_DATA],
        )


def profile_apply_frames(
    onboard_slot: int,
    generation_token: int,
    normal_main: Iterable[bytes],
    fn_main: Iterable[bytes],
    normal_scroll: Iterable[bytes],
    fn_scroll: Iterable[bytes],
    sequence: int = 0,
) -> list[Frame]:
    """Build the exact bank ordering used when the vendor app applies a profile.

    The two onboard profile slots are selected by command 02/selector 2.  The
    selectors on commands 04 and 05 are layers (0=normal, 1=Fn), not profiles.
    """
    if onboard_slot not in (0, 1):
        raise ValueError("W910 onboard slot must be 0 or 1")
    normal_main_list = list(normal_main)
    fn_main_list = list(fn_main)
    normal_scroll_list = list(normal_scroll)
    fn_scroll_list = list(fn_scroll)
    if len(normal_main_list) != MAIN_RECORD_COUNT or len(fn_main_list) != MAIN_RECORD_COUNT:
        raise ValueError("each main layer must contain 160 records")
    if len(normal_scroll_list) != SCROLL_RECORD_COUNT or len(fn_scroll_list) != SCROLL_RECORD_COUNT:
        raise ValueError("each scroll layer must contain four records")

    frames = [
        Frame(0x02, sequence, 2, 0, bytes((onboard_slot,))),
        Frame(
            0x02,
            (sequence + 1) & 0xFF,
            1,
            onboard_slot * 2,
            generation_token_bytes(generation_token),
        ),
    ]
    next_sequence = (sequence + 2) & 0xFF
    # The app writes all four scroll records individually: Fn first, then normal.
    for selector, records in ((1, fn_scroll_list), (0, normal_scroll_list)):
        for index, record in enumerate(records):
            if len(record) != ACTION_SIZE:
                raise ValueError("scroll action must be four bytes")
            frames.append(Frame(0x05, next_sequence, selector, index * 4, record))
            next_sequence = (next_sequence + 1) & 0xFF
    # Main records are packed eight at a time (32 bytes): normal first, then Fn.
    for selector, records in ((0, normal_main_list), (1, fn_main_list)):
        layer_frames = list(iter_bank_write_frames(0x04, selector, records, next_sequence))
        frames.extend(layer_frames)
        next_sequence = (next_sequence + len(layer_frames)) & 0xFF
    return frames
