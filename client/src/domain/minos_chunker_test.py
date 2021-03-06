import unittest

from result import Ok
from src.domain.minos_chunker import Chunk, MinOSChunker


class TestMinOSChunker(unittest.TestCase):
    def test_chunk_parser(self):
        type_int = 3
        content = b'potat'
        chunk = Chunk(type_int, content)
        encoded = MinOSChunker.encode(chunk)
        decoded = MinOSChunker.decode(encoded)
        self.assertEqual(Ok(chunk), decoded)

    def test_stream_parser(self):
        null_byte = (0).to_bytes(1, byteorder='big')
        chunk1 = Chunk(3, b'potat1')
        chunk2 = Chunk(4, b'pot' + null_byte + b'at2')
        chunk3 = Chunk(5, b'potat3')
        chunk4 = Chunk(5, b'potat4')
        encoded1 = MinOSChunker.encode(chunk1)
        encoded2 = MinOSChunker.encode(chunk2)
        encoded3 = MinOSChunker.encode(chunk3)
        encoded4 = MinOSChunker.encode(chunk4)
        stream = encoded1[4:] + encoded1 + encoded2 + encoded3 + encoded4 + encoded3[0:-5]
        chunks, garbage, leftover = MinOSChunker.decode_stream(stream)
        self.assertEqual(chunks, [chunk1, chunk2, chunk3, chunk4])
        self.assertEqual(leftover, encoded3[0:-5])


if __name__ == '__main__':
    unittest.main()
