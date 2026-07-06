from __future__ import annotations

from protocol.common import decode_12bit_value, decode_page_line
from protocol.decoders.base import WordDecoder


class DataValueDecoder(WordDecoder):
    word_type = 0

    def decode(self, packet: bytes):
        frame = self.base_frame(packet)
        if len(packet) >= 8:
            page, line = decode_page_line(packet[5])
            raw, negative, sensor_fault = decode_12bit_value(packet[6], packet[7])
            frame.fields.update({
                "measuring_point": packet[4],
                "page": page,
                "line": line,
                "raw_value": raw,
                "negative": negative,
                "sensor_fault": sensor_fault,
                "key": f"{packet[4]}:{page}:{line}",
            })
        return frame
