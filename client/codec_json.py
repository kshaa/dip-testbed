"""Generic Python class instance from/to JSON object codec definition"""

from __future__ import annotations
from typing import TypeVar, Callable, Any
from result import Result, Ok, Err
import json
from codec import CodecParseException, Codec, Decoder, Encoder

JSON = Any
D = TypeVar('D')
NO_WHITESPACE_SEPERATORS = (',', ':')


class DecoderJSON(Decoder[str, JSON, D]):
    """Generic data decoder between Raw <-> Serializable <-> Domain"""

    def __init__(self, decode: Callable[[JSON], Result[D, CodecParseException]]):
        self.decode = decode

    def raw_decode(self, value: str) -> Result[D, CodecParseException]:
        """Decode raw directly to domain"""
        serializable = self.raw_as_serializable(value)
        if isinstance(serializable, Err):
            return serializable
        return self.decode(serializable.value)

    @staticmethod
    def raw_as_serializable(text: str) -> Result[JSON, CodecParseException]:
        """Unserialize JSON from a string"""
        try:
            return Ok(json.loads(text))
        except Exception as e:
            return Err(CodecParseException(str(e)))

    @staticmethod
    def identity() -> DecoderJSON[JSON]:
        """Decoder where domain is same as serializable"""
        return DecoderJSON(lambda x: x)


class EncoderJSON(Encoder[str, JSON, D]):
    """Generic data encoder between Raw <-> Serializable <-> Domain"""

    def __init__(self, encode: Callable[[D], JSON]):
        self.encode = encode

    def raw_encode(self, value: D) -> str:
        """Serialize domain directly to raw"""
        serializable = self.encode(value)
        return self.serializable_as_raw(serializable)

    @staticmethod
    def serializable_as_raw(data: JSON) -> str:
        """Serialize JSON into a string"""
        return json.dumps(data, separators=NO_WHITESPACE_SEPERATORS)

    @staticmethod
    def identity() -> EncoderJSON[JSON]:
        """Encoder where domain is same as serializable"""
        return EncoderJSON(lambda x: x)


class CodecJSON(Codec[str, JSON, D]):
    """Serialization codec between Raw <-> Serializable <-> Domain"""
    decoder: DecoderJSON[D]
    encoder: EncoderJSON[D]

    def __init__(self, decoder: DecoderJSON[D], encoder: EncoderJSON[D]):
        self.decoder = decoder
        self.encoder = encoder
