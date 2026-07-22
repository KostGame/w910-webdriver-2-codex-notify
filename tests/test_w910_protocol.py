import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from w910_protocol import (  # noqa: E402
    Frame,
    KeyboardEvent,
    LightingRecord,
    MAIN_CONTROLS,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    VENDOR_PROFILE_KEYS,
    VENDOR_SCROLL_KEYS,
    VISIBLE_SPECIAL_FUNCTIONS,
    decode_action,
    decode_macro,
    default_main_bank,
    default_fn_main_bank,
    default_scroll_bank,
    encode_macro,
    encode_macro_action,
    encode_ui_function,
    generation_token_bytes,
    lighting_frames,
    macro_write_frames,
    profile_apply_frames,
    timeout_bytes,
    vendor_macro_events,
    vendor_profile_banks,
    vendor_profile_lighting,
)


def vendor_lighting_records(selected: int = 7) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for _ in range(9):
        record: dict[str, object] = {
            "curselmode": selected,
            "frequencyvalue": 5,
            "directionsel": 1,
            "brightnessvalue": 6,
        }
        for index in range(7):
            record[f"ctrl_KBLed_Col{index}"] = [1, 0xFFFF05B8]
        records.append(record)
    return records


def vendor_profile_fixture() -> dict[str, object]:
    normal = {
        VENDOR_PROFILE_KEYS[name]: control.default_ui_value
        for name, control in MAIN_CONTROLS.items()
    }
    function = dict(normal)
    function[VENDOR_PROFILE_KEYS["rgb_light_switch"]] = 255
    function[VENDOR_PROFILE_KEYS["mode_switch_press"]] = 255
    function[VENDOR_PROFILE_KEYS["key_tab"]] = 491
    normal[VENDOR_SCROLL_KEYS["scroll_up"]] = 0xE9
    normal[VENDOR_SCROLL_KEYS["scroll_down"]] = 0xEA
    function[VENDOR_SCROLL_KEYS["scroll_up"]] = 0xEA
    function[VENDOR_SCROLL_KEYS["scroll_down"]] = 0xE9
    return {
        "KBconfig": {
            "KBKey": normal,
            "FnKey": function,
            "KBKeyMacro": {},
            "FnKeyMacro": {},
            "KBled": vendor_lighting_records(),
        }
    }


class FrameTests(unittest.TestCase):
    def test_dynamic_b_to_a_capture(self):
        frame = Frame(0x04, 0x00, 0, 0x20, b"\x02\x04\x00\x00")
        report = frame.to_report()
        self.assertEqual(report[:13].hex(), "06000104000020000402040000")
        self.assertEqual(Frame.from_report(report), frame)

    def test_read_request(self):
        frame = Frame.read_request(0x04, 7, selector=1, address=0x20, length=4)
        self.assertEqual((frame.command, frame.selector, frame.address), (0x84, 1, 0x20))
        self.assertEqual(len(frame.data), 4)


class ActionTests(unittest.TestCase):
    def test_all_visible_special_functions_encode(self):
        self.assertEqual(len(VISIBLE_SPECIAL_FUNCTIONS), 30)
        for _name, value in VISIBLE_SPECIAL_FUNCTIONS:
            self.assertEqual(len(encode_ui_function(value)), 4)

    def test_dynamic_action_captures(self):
        self.assertEqual(encode_ui_function(0xE9), bytes.fromhex("04 E9 00 00"))
        self.assertEqual(encode_ui_function(307), bytes.fromhex("07 02 00 00"))
        self.assertEqual(encode_ui_function(491), bytes.fromhex("0E 03 00 00"))
        self.assertEqual(encode_ui_function(255), bytes(4))
        self.assertEqual(encode_ui_function(312), bytes.fromhex("09 03 00 00"))

    def test_macro_playback_modes(self):
        self.assertEqual(encode_macro_action(0, 0), bytes.fromhex("0A 00 00 00"))
        self.assertEqual(encode_macro_action(0, 1), bytes.fromhex("0A 01 00 00"))
        self.assertEqual(encode_macro_action(0, 2), bytes.fromhex("0A 02 00 00"))
        self.assertEqual(decode_action(bytes.fromhex("0A 02 03 00"))["slot"], 3)

    def test_physical_matrix_addresses(self):
        self.assertEqual(len(MAIN_CONTROLS), 18)
        self.assertEqual(MAIN_CONTROLS["key_b"].address, 0x20)
        self.assertEqual(MAIN_CONTROLS["mode_switch_right"].address, 0xA8)
        bank = default_main_bank()
        self.assertEqual(bank[8], bytes.fromhex("02 05 00 00"))
        self.assertEqual(bank[10], bytes.fromhex("09 03 00 00"))


class MacroTests(unittest.TestCase):
    def test_dynamic_minimal_macro_capture(self):
        stream = encode_macro([KeyboardEvent(0x29, True, 20)], repeat_count=1)
        self.assertEqual(stream, bytes.fromhex("01 00 02 00 29 14"))
        frame = macro_write_frames(0, 0xBC, stream)[0]
        self.assertEqual((frame.command, frame.selector, frame.address, frame.data), (8, 0, 0, stream))

    def test_all_event_forms_round_trip(self):
        events = [
            KeyboardEvent(0x04, True, 0),
            KeyboardEvent(0x04, False, 127),
            KeyboardEvent(0x05, True, 128),
            KeyboardEvent(0x05, False, 500),
            MouseButtonEvent("left", True, 0),
            MouseButtonEvent("right", False, 400),
            MouseButtonEvent("middle", True, 10),
            MouseButtonEvent("back", False, 127),
            MouseButtonEvent("forward", True, 128),
            MouseWheelEvent(1, 0),
            MouseWheelEvent(0xFF, 400),
            MouseMoveEvent(-123, 456, 255),
            MouseMoveEvent(32767, -32768, 256),
        ]
        stream = encode_macro(events, repeat_count=17)
        self.assertEqual(decode_macro(stream), (17, events))

    def test_dynamic_mouse_capture_and_static_button_table(self):
        self.assertEqual(
            encode_macro(
                [
                    MouseButtonEvent("left", True, 10),
                    MouseButtonEvent("right", True, 10),
                    MouseButtonEvent("left", True, 10),
                ]
            ),
            bytes.fromhex("01 00 06 00 E8 0A EA 0A E8 0A"),
        )

    def test_vendor_macro_json_mouse_and_xy(self):
        data = {
            "num": 4,
            "macVal": [0xF1, 0xF3, 0xF8, 0xF6],
            "macSta": [1, 2, 0, 4],
            "macDly": [10, 20, 30, 40],
            "extVal": [[0, 0], [0, 0], [0xFF, 0], [12, 34]],
        }
        self.assertEqual(
            vendor_macro_events(data),
            [
                MouseButtonEvent("left", True, 10),
                MouseButtonEvent("middle", False, 20),
                MouseWheelEvent(0xFF, 30),
                MouseMoveEvent(-12, 34, 40),
            ],
        )

    def test_vendor_profile_macro_resolves_end_to_end(self):
        profile = vendor_profile_fixture()
        root = profile["KBconfig"]
        assert isinstance(root, dict)
        normal = root["KBKey"]
        macro_layer = root["KBKeyMacro"]
        assert isinstance(normal, dict)
        assert isinstance(macro_layer, dict)
        normal[VENDOR_PROFILE_KEYS["key_b"]] = 0x04
        normal[VENDOR_PROFILE_KEYS["key_c"]] = 700
        macro_layer[VENDOR_PROFILE_KEYS["key_c"]] = {
            "grpGuid": "group-1",
            "macGuid": "macro-1",
            "MemMacId": 0,
        }
        macros = {
            "MacroGrpInfo": [
                {
                    "GrpGuid": "group-1",
                    "MacroInfo": [
                        {
                            "MacroGuid": "macro-1",
                            "macData": {
                                "num": 1,
                                "macVal": [0x29],
                                "macSta": [1],
                                "macDly": [20],
                                "extVal": [[0, 0]],
                                "macRpt": 1,
                                "rptType": 2,
                            },
                        }
                    ],
                }
            ]
        }
        banks = vendor_profile_banks(profile, macros)
        self.assertEqual(banks.normal_main[8], bytes.fromhex("02 04 00 00"))
        self.assertEqual(banks.normal_main[16], bytes.fromhex("0A 02 00 00"))
        self.assertEqual(banks.macro_streams[0], bytes.fromhex("01 00 02 00 29 14"))
        self.assertEqual(
            encode_macro(
                [
                    MouseButtonEvent("right", True, 10),
                    MouseButtonEvent("middle", True, 10),
                    MouseButtonEvent("back", True, 10),
                    MouseButtonEvent("forward", True, 10),
                ]
            )[4:],
            bytes.fromhex("EA 0A E9 0A EB 0A EC 0A"),
        )


class LightingAndProfileTests(unittest.TestCase):
    def test_dynamic_mode_2_golden_record(self):
        record = LightingRecord(
            speed=4,
            direction=1,
            brightness=6,
            enabled=(True,) * 7,
            colors=(
                (0xFF, 0xFF, 0x00),
                (0x00, 0x00, 0xFF),
                (0xFF, 0xA5, 0x00),
                (0x00, 0xFF, 0x00),
                (0xFF, 0x00, 0x00),
                (0x00, 0xFF, 0xFF),
                (0x80, 0x00, 0x80),
            ),
        )
        expected = bytes.fromhex(
            "04 01 00 7F FF FF 00 00 00 FF A5 FF 00 FF 00 00 00 FF 00 FF 00 FF 00 80 80"
        )
        self.assertEqual(record.encode(), expected)
        self.assertEqual(LightingRecord.decode(expected), record)
        frames = lighting_frames(0x82, record, 0x5A)
        self.assertEqual(frames[0].data, bytes.fromhex("82 FF 01") + bytes(22))
        self.assertEqual(frames[1].address, 0x32)

    def test_off_has_header_only(self):
        frames = lighting_frames(0x89, None, 1)
        self.assertEqual(len(frames), 1)

    def test_profile_fields_endianness(self):
        self.assertEqual(generation_token_bytes(0x3F56), bytes.fromhex("3F 56"))
        self.assertEqual(timeout_bytes(5), bytes.fromhex("2C 01"))

    def test_vendor_profile_apply_order(self):
        normal = default_main_bank()
        fn = default_fn_main_bank()
        frames = profile_apply_frames(
            1,
            0xB411,
            normal,
            fn,
            default_scroll_bank(False),
            default_scroll_bank(True),
            sequence=5,
        )
        self.assertEqual(len(frames), 50)
        self.assertEqual((frames[0].command, frames[0].selector, frames[0].data), (2, 2, b"\x01"))
        self.assertEqual((frames[1].selector, frames[1].address, frames[1].data), (1, 2, b"\xB4\x11"))
        self.assertEqual((frames[2].command, frames[2].selector, frames[2].data), (5, 1, bytes.fromhex("04 EA 00 00")))
        self.assertEqual((frames[6].command, frames[6].selector, frames[6].data), (5, 0, bytes.fromhex("04 E9 00 00")))
        self.assertEqual((frames[10].command, frames[10].selector, len(frames[10].data)), (4, 0, 32))
        self.assertEqual((frames[30].command, frames[30].selector, len(frames[30].data)), (4, 1, 32))
        self.assertEqual(fn[2], bytes.fromhex("02 00 00 00"))
        self.assertEqual(fn[10], bytes.fromhex("02 00 00 00"))
        self.assertEqual(fn[40], bytes.fromhex("0E 03 00 00"))

    def test_vendor_lighting_record_matches_direct_readback(self):
        profile = vendor_profile_fixture()
        mode, record = vendor_profile_lighting(profile)
        self.assertEqual(mode, 0x88)
        self.assertIsNotNone(record)
        assert record is not None
        self.assertEqual(
            record.encode(),
            bytes.fromhex(
                "05 01 00 7F "
                "05 FF B8 05 FF B8 05 FF B8 05 FF B8 "
                "05 FF B8 05 FF B8 05 FF B8"
            ),
        )


if __name__ == "__main__":
    unittest.main()
