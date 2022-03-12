import math
from dataclasses import dataclass
from typing import Iterable
from result import Result, Err, Ok


@dataclass
class FancyByte:
    value: int

    @staticmethod
    def fromBytes(b: bytes) -> Result['FancyByte', str]:
        if len(b) > 1:
            return Err("Only one byte allowed")
        try:
            return Ok(FancyByte(int.from_bytes(b, "little")))
        except Exception as e:
            return Err(f"Can't build byte: {e}")

    @staticmethod
    def fromInt(n: int) -> Result['FancyByte', str]:
        if n < 0:
            return Err("Byte too small")
        elif n >= math.pow(2, 8):
            return Err("Byte too large")
        return Ok(FancyByte(n))

    def to_binary_bits(self) -> Iterable[bool]:
        str_bits_8 = bin(self.value)[2:].zfill(8)
        return list(map(lambda x: x == "1", str_bits_8))

    def to_hex_str(self) -> str:
        return str(hex(self.value))

    def to_char(self) -> str:
        return chr(self.value)
