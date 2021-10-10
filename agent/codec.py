"""Generic Python class instance from/to JSON object codec definition"""

from typing import TypeVar, Generic, Callable
from result import Result, Ok

T = TypeVar('T')


class CodecParseException(Exception):
    """Exception thrown by failing decoders"""
    def __eq__(self, other) -> bool:
        return str(self) == str(other)


class Decoder(Generic[T]):
    """JSON object to Python class instance un-serializer"""

    def __init__(self, transform: Callable[[str], Result[T, CodecParseException]]):
        self.transform = transform


class Encoder(Generic[T]):
    """Python class instance to JSON object serializer"""

    def __init__(self, transform: Callable[[T], str]):
        self.transform = transform


class Codec(Generic[T]):
    """Python class instance from/to JSON object codec"""
    decoder: Decoder[T]
    encoder: Encoder[T]

    def __init__(self, decoder: Decoder[T], encoder: Encoder[T]):
        self.decoder = decoder
        self.encoder = encoder

    def encode(self, value: T) -> str:
        """Alias method to serialize to JSON"""
        return self.encoder.transform(value)

    def decode(self, value: str) -> Result[T, CodecParseException]:
        """Alias method to un-serialize from JSON"""
        return self.decoder.transform(value)


stringEncoder: Encoder[str] = Encoder(lambda x: x)
stringDecoder: Decoder[str] = Decoder(Ok)
stringCodec: Codec[str] = Codec(stringDecoder, stringEncoder)
