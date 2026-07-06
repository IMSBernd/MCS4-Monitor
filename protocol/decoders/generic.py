from __future__ import annotations

from protocol.common import decode_12bit_value, decode_page_line
from protocol.decoders.base import WordDecoder


class GenericWordDecoder(WordDecoder):
    def __init__(self, word_type: int):
        self.word_type = word_type

    def decode(self, packet: bytes):
        frame = self.base_frame(packet)
        frame.fields["number_or_code"] = frame.number
        frame.fields["flags"] = frame.flags
        if len(packet) >= 8:
            page, line = decode_page_line(packet[5])
            raw, negative, sensor_fault = decode_12bit_value(packet[6], packet[7])
            frame.fields.update({
                "page_candidate": page,
                "line_candidate": line,
                "raw_candidate": raw,
                "negative_candidate": negative,
                "sensor_fault_candidate": sensor_fault,
            })
        return frame
