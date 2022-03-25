import math
from dataclasses import dataclass
from typing import List
from result import Result, Err, Ok


@dataclass
class FancyByte:
    value: int

    @staticmethod
    def fromBytes(b: bytes) -> Result['FancyByte', str]:
        if len(b) > 1:
            return Err("Only one byte allowed")
        try:
            return Ok(FancyByte(int.from_bytes(b, "big")))
        except Exception as e:
            return Err(f"Can't build byte: {e}")

    @staticmethod
    def fromInt(n: int) -> Result['FancyByte', str]:
        if n < 0:
            return Err("Byte too small")
        elif n >= math.pow(2, 8):
            return Err("Byte too large")
        return Ok(FancyByte(n))

    def toggle_bit(self, index: int) -> Result['FancyByte', str]:
        if index < 0 or index > 7:
            return Err("Bad bit index")
        bits = self.to_binary_bits()
        diff = pow(2, 7 - index)
        if bits[index]:
            return Ok(FancyByte(self.value - diff))
        else:
            return Ok(FancyByte(self.value + diff))

    def to_binary_bits(self) -> List[bool]:
        str_bits_8 = bin(self.value)[2:].zfill(8)
        return list(map(lambda x: x == "1", str_bits_8))

    def to_hex_str(self) -> str:
        return str(hex(self.value))

    def to_char(self) -> str:
        return chr(self.value)

    def to_bytes(self) -> bytes:
        return self.value.to_bytes(1, byteorder='big')
