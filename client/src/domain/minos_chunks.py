from dataclasses import dataclass
from result import Result, Err, Ok
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.fancy_byte import FancyByte


@dataclass
class ParsedChunk:
    pass


@dataclass
class Chunk:
    # Type must be >= 2
    type: int
    content: bytes


@dataclass
class LEDChunk(ParsedChunk):
    fancy_byte: FancyByte
    type: int = 2

    @staticmethod
    def from_chunk(chunk: Chunk) -> Result['LEDChunk', DIPClientError]:
        if chunk.type != LEDChunk.type:
            return Err(GenericClientError("Invalid chunk type for LEDChunk"))
        fancy_byte_result = FancyByte.fromBytes(chunk.content)
        if isinstance(fancy_byte_result, Err):
            return Err(GenericClientError(f"Invalid content for LEDChunk, reason: {fancy_byte_result.value}"))
        return Ok(LEDChunk(fancy_byte_result.value))


@dataclass
class IndexedButtonChunk(ParsedChunk):
    button_index: int
    type: int = 3

    def to_chunk(self) -> Result[Chunk, DIPClientError]:
        fancy_byte_result = FancyByte.fromInt(self.button_index)
        if isinstance(fancy_byte_result, Err):
            return Err(GenericClientError(
                f"Failed to construct indexed button chunk, reason: {fancy_byte_result.value}"))
        return Chunk(self.type, fancy_byte_result.value.to_bytes())


@dataclass
class SwitchChunk(ParsedChunk):
    fancy_byte: FancyByte
    type: int = 4

    def to_chunk(self) -> Result[Chunk, DIPClientError]:
        return Chunk(self.type, self.fancy_byte.to_bytes())


@dataclass
class TextChunk(ParsedChunk):
    text: str
    type: int = 5

    def to_chunk(self) -> Result[Chunk, DIPClientError]:
        text_bytes = str.encode(self.text)
        return Chunk(self.type, text_bytes)

    @staticmethod
    def from_chunk(chunk: Chunk) -> Result['TextChunk', DIPClientError]:
        if chunk.type != TextChunk.type:
            return Err(GenericClientError("Invalid chunk type for TextChunk"))

        try:
            text = chunk.content.decode("utf-8")
            return Ok(TextChunk(text))
        except Exception as e:
            return Err(GenericClientError(f"Failed to parse chunk text: {e}"))


@dataclass
class DisplayChunk(ParsedChunk):
    pixel_index: int
    fancy_byte: FancyByte
    type: int = 6

    @staticmethod
    def from_chunk(chunk: Chunk) -> Result['DisplayChunk', DIPClientError]:
        if chunk.type != DisplayChunk.type:
            return Err(GenericClientError("Invalid chunk type for DisplayChunk"))
        if len(chunk.content) != 2:
            return Err(GenericClientError("Invalid chunk length for DisplayChunk"))
        pixel_index_byte_result = FancyByte.fromBytes(chunk.content[0:1])
        if isinstance(pixel_index_byte_result, Err):
            return Err(GenericClientError(f"Invalid content for DisplayChunk, reason: {pixel_index_byte_result.value}"))
        fancy_byte_result = FancyByte.fromBytes(chunk.content[1:2])
        if isinstance(fancy_byte_result, Err):
            return Err(GenericClientError(f"Invalid content for DisplayChunk, reason: {fancy_byte_result.value}"))
        return Ok(DisplayChunk(pixel_index_byte_result.value.value, fancy_byte_result.value))

    def r(self):
        bits = self.fancy_byte.to_binary_bits()
        return bits[2] * pow(2, 1) + bits[3] * pow(2, 0)

    def g(self):
        bits = self.fancy_byte.to_binary_bits()
        return bits[4] * pow(2, 1) + bits[5] * pow(2, 0)

    def b(self):
        bits = self.fancy_byte.to_binary_bits()
        return bits[6] * pow(2, 1) + bits[7] * pow(2, 0)
