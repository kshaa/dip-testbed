from typing import List, Tuple
from result import Result, Err, Ok
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.minos_chunks import ParsedChunk, LEDChunk, Chunk


class MinOSChunker:
    @staticmethod
    def parse_chunk(chunk: Chunk) -> Result[ParsedChunk, DIPClientError]:
        result = Err("Unknown chunk type")
        if chunk.type == LEDChunk.type:
            result = LEDChunk.from_chunk(chunk)
        return result

    @staticmethod
    def encode(chunk: Chunk) -> bytes:
        null_byte: bytes = (0).to_bytes(1, byteorder='big')
        one_byte: bytes = (1).to_bytes(1, byteorder='big')
        chunk_type: bytes = chunk.type.to_bytes(1, byteorder='big')
        chunk_start = null_byte + chunk_type
        chunk_content = chunk.content.replace(null_byte, null_byte + null_byte)
        chunk_end = null_byte + one_byte
        chunk = chunk_start + chunk_content + chunk_end
        return chunk

    @staticmethod
    def decode(chunk: bytes) -> Result[Chunk, DIPClientError]:
        null_byte: bytes = (0).to_bytes(1, byteorder='big')
        one_byte: bytes = (1).to_bytes(1, byteorder='big')
        try:
            start_null = chunk[0:1]
            if start_null != null_byte: return Err("Chunk must start w/ escaped type")
            chunk_type = int.from_bytes(chunk[1:2], byteorder='big')
            if chunk_type == 0 or chunk_type == 1: return Err("Chunk type cannot be 0x00 or 0x01")
            content = chunk[2:-2]
            content_decoded = content.replace(null_byte + null_byte, null_byte)
            end = chunk[-2:]
            if end != null_byte + one_byte: return Err("Chunk must end w/ 0x00, 0x01")
            return Ok(Chunk(chunk_type, content))
        except Exception as e:
            print(e)
            return Err(GenericClientError(f"Failed to decode chunk, reason: {e}"))

    @staticmethod
    def decode_stream(stream: bytes) -> Tuple[List[Chunk], bytes]:
        """Parses as many chunks as possible in the stream and also returns the unfinished chunk"""
        null_byte: bytes = (0).to_bytes(1, byteorder='big')
        one_byte: bytes = (1).to_bytes(1, byteorder='big')

        end_index = None
        chunks = []
        leftover = stream
        a = 0
        while ((end_index is None) or (end_index != -1)) and (a < 5):
            a = a + 1
            is_init = end_index is None
            end_index = leftover.find(null_byte + one_byte)
            if is_init:
                continue
            chunk_bytes = leftover[0:(end_index + 2)]
            leftover = leftover[(end_index + 2):]
            chunk_result = MinOSChunker.decode(chunk_bytes)
            if isinstance(chunk_result, Ok):
                chunks.append(chunk_result.value)
        return chunks, leftover