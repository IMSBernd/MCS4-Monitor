from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from protocol.common import decode_12bit_value, decode_page_line, decode_word_flags, decode_word_type
from protocol.dispatcher import decode_frame
from protocol.frame_reader import FrameReader


def packet_data_value(mp: int, page: int, line: int, raw: int, *, fault: bool = False, negative: bool = False) -> bytes:
    raw_abs = abs(int(raw)) & 0x0FFF
    b6 = ((page & 0x1F) << 3) | (line & 0x07)
    b7 = ((0x40 if fault else 0) | (0x20 if negative else 0) | ((raw_abs >> 7) & 0x1F))
    b8 = raw_abs & 0x7F
    return bytes([0xFF, 0x00, 0x01, 0x02, mp & 0x7F, b6, b7, b8])


def assert_equal(actual, expected, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def test_common_bit_decoding() -> None:
    assert_equal(decode_word_type(0xA7), 7, "word type D3..D0")
    assert_equal(decode_word_flags(0xA7), 10, "word flags D7..D4")
    assert_equal(decode_page_line(0x40), (8, 0), "page/line page 8 line 0")
    assert_equal(decode_page_line(0x18), (3, 0), "page/line page 3 line 0")

    raw, negative, fault = decode_12bit_value(0x06, 0x45)
    assert_equal((raw, negative, fault), (837, False, False), "12-bit positive")

    raw, negative, fault = decode_12bit_value(0x66, 0x45)
    assert_equal((raw, negative, fault), (-837, True, True), "12-bit negative with sensor fault")


def test_frame_reader_mixed_lengths() -> None:
    data = packet_data_value(3, 8, 0, 837)
    alarm_like = bytes([0xFF, 0x02, 0x01, 0x02, 0x09])  # WordType 2 -> 5 bytes
    stream = b"\x11\x22" + data + alarm_like + packet_data_value(4, 3, 0, 781)
    frames = FrameReader().feed(stream)
    assert_equal([len(f) for f in frames], [8, 5, 8], "mixed word lengths")
    assert_equal(frames[0], data, "first data frame")
    assert_equal(frames[1], alarm_like, "5-byte alarm-like frame")


def test_wordtype0_decoder() -> None:
    frame = decode_frame(packet_data_value(3, 8, 0, 837))
    assert_equal(frame.word_type, 0, "word type 0")
    assert_equal(frame.word_type_name, "Data Value", "word name")
    assert_equal(frame.fields.get("measuring_point"), 3, "measuring point")
    assert_equal(frame.fields.get("page"), 8, "page")
    assert_equal(frame.fields.get("line"), 0, "line")
    assert_equal(frame.fields.get("raw_value"), 837, "raw value")
    assert_equal(frame.fields.get("key"), "3:8:0", "sensor key")
    assert frame.is_valid, "data frame should be valid"


def test_appendix12_database() -> None:
    path = ROOT / "database" / "appendix12.json"
    if not path.exists():
        raise AssertionError("database/appendix12.json does not exist")
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in ("3:0", "1:1", "8:0", "4:0"):
        if key not in data:
            raise AssertionError(f"Appendix 12 missing required simulator key {key}")
        entry = data[key]
        for field in ("unit", "range", "factor"):
            if field not in entry:
                raise AssertionError(f"Appendix 12 {key} missing field {field}")


def parse_mcslog(path: Path) -> list[bytes]:
    frames: list[bytes] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.strip().split()
        if not parts:
            continue
        hex_text = parts[-1].replace(" ", "")
        if len(hex_text) % 2:
            continue
        try:
            frames.append(bytes.fromhex(hex_text))
        except ValueError:
            continue
    return frames


def test_optional_mcslog_files(paths: list[str]) -> None:
    for p in paths:
        path = Path(p)
        frames = parse_mcslog(path)
        if not frames:
            raise AssertionError(f"No frames parsed from {path}")
        decoded = [decode_frame(frame) for frame in frames[:500]]
        valid = sum(1 for f in decoded if f.is_valid)
        if valid == 0:
            raise AssertionError(f"No valid frames decoded from {path}")
        print(f"MCSLOG {path.name}: checked={len(decoded)} valid={valid}")


def main() -> int:
    tests = [
        test_common_bit_decoding,
        test_frame_reader_mixed_lengths,
        test_wordtype0_decoder,
        test_appendix12_database,
    ]
    try:
        for test in tests:
            test()
            print(f"PASS {test.__name__}")
        if len(sys.argv) > 1:
            test_optional_mcslog_files(sys.argv[1:])
        print("ALL TESTS PASSED")
        return 0
    except Exception as exc:
        print(f"TEST FAILED: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
