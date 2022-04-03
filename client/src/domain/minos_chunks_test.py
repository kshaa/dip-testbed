import unittest

from result import Ok
from src.domain.minos_chunker import Chunk, MinOSChunker
from src.domain.minos_chunks import TextChunk


class TestMinOSChunks(unittest.TestCase):
    def test_text_chunk(self):
        a = TextChunk("potat")
        b = a.to_chunk()
        c = TextChunk.from_chunk(b)

        self.assertEqual(Ok(a), c)


if __name__ == '__main__':
    unittest.main()
