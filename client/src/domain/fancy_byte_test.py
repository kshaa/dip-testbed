import math
import unittest

from result import Ok, Err

from src.domain.fancy_byte import FancyByte


class TestFancyByte(unittest.TestCase):
    def test_fancy_int_bytes(self):
        io = [
            (-1, Err("Byte too small")),
            (math.pow(2, 8), Err("Byte too large")),
            (0, Ok([False, False, False, False, False, False, False, False])),
            (1, Ok([False, False, False, False, False, False, False, True])),
        ]
        for (input, output) in io:
            reality = FancyByte.fromInt(input).map(lambda x: x.to_binary_bits())
            self.assertEqual(reality, output, input)

    def test_fancy_byte_bytes(self):
        io = [
            ((0).to_bytes(1, byteorder='big'), Ok([False, False, False, False, False, False, False, False])),
            ((1).to_bytes(1, byteorder='big'), Ok([False, False, False, False, False, False, False, True])),
            ((int(math.pow(2, 8) - 1)).to_bytes(1, byteorder='big'), Ok([True, True, True, True, True, True, True, True])),
        ]
        for (input, output) in io:
            reality = FancyByte.fromBytes(input).map(lambda x: x.to_binary_bits())
            self.assertEqual(reality, output, input)

    def test_bits(self):
        self.assertEqual(
            FancyByte.from_bits([0, 0, 0, 0, 0, 0, 0, 0]),
            FancyByte.fromInt(0)
        )
        self.assertEqual(
            FancyByte.from_bits([0,0,0,0,0,0,0,1]),
            FancyByte.fromInt(1)
        )
        self.assertEqual(
            FancyByte.from_bits([1,0,0,0,0,0,0,0]),
            FancyByte.fromInt(128)
        )
        self.assertEqual(
            FancyByte.from_bits([1,1,1,1,1,1,1,1]),
            FancyByte.fromInt(255)
        )

if __name__ == '__main__':
    unittest.main()
