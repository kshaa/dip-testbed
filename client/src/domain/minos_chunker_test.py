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
        chunk1 = Chunk(3, b'potat1')
        chunk2 = Chunk(4, b'potat2')
        chunk3 = Chunk(5, b'potat3')
        encoded1 = MinOSChunker.encode(chunk1)
        encoded2 = MinOSChunker.encode(chunk2)
        encoded3 = MinOSChunker.encode(chunk3)
        stream = encoded1[4:] + encoded1 + encoded2 + encoded3 + encoded3[0:-5]
        decoded_stream = MinOSChunker.decode_stream(stream)
        self.assertEqual(decoded_stream, ([chunk1, chunk2, chunk3], encoded3[0:-5]))

    def test_chunker(self):
        chunker = MinOSChunker()
        chunk1 = Chunk(3, b'potat1')
        encoded1 = MinOSChunker.encode(chunk1)
        chunk2 = Chunk(3, b'potat2')
        encoded2 = MinOSChunker.encode(chunk2)

        # Process a chunk for which we received only the end
        processed1 = chunker.process(encoded1[4:])
        self.assertEqual(processed1, [])
        self.assertEqual(chunker.stream, b"")

        # Process a chunk for which we received all bytes
        processed2 = chunker.process(encoded1)
        self.assertEqual(processed2, [chunk1])
        self.assertEqual(chunker.stream, b"")

        # Process a chunk for which we're receiving the start
        processed3 = chunker.process(encoded2[0:-5])
        self.assertEqual(processed3, [])
        self.assertEqual(chunker.stream, encoded2[0:-5])

        # Finish the chunk
        processed4 = chunker.process(encoded2[-5:])
        self.assertEqual(processed4, [chunk2])
        self.assertEqual(chunker.stream, b"")

        # Try receiving multiple chunks
        processed5 = chunker.process(encoded1 + encoded2)
        self.assertEqual(processed5, [chunk1, chunk2])
        self.assertEqual(chunker.stream, b"")



if __name__ == '__main__':
    unittest.main()
