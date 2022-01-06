"""Generic Python class instance from/to JSON object codec definition"""

from __future__ import annotations
from typing import TypeVar, Callable, Any
from result import Result, Err
from codec import CodecParseException, Codec, Decoder, Encoder
from codec_json import DecoderJSON, EncoderJSON

D = TypeVar('D')


class DecoderHybrid(Decoder[Any, Any, D]):
    """Generic data decoder between Raw <-> Serializable <-> Domain"""

    def __init__(self, decode: Callable[[Any], Result[D, CodecParseException]]):
        self.decode = decode

    def raw_decode(self, value: Any) -> Result[D, CodecParseException]:
        """Decode raw directly to domain"""
        serializable = value
        if not isinstance(value, bytes):
            json_result = DecoderJSON.raw_as_serializable(value)
            if isinstance(json_result, Err):
                return serializable
            serializable = json_result.value
        return self.decode(serializable)


class EncoderHybrid(Encoder[Any, Any, D]):
    """Generic data encoder between Raw <-> Serializable <-> Domain"""

    def __init__(self, encode: Callable[[D], Any]):
        self.encode = encode

    def raw_encode(self, value: D) -> str:
        """Serialize domain directly to raw"""
        serializable = self.encode(value)
        if isinstance(serializable, bytes):
            return serializable
        else:
            return EncoderJSON.serializable_as_raw(serializable)


class CodecHybrid(Codec[Any, Any, D]):
    """Serialization codec between Raw <-> Serializable <-> Domain"""
    decoder: DecoderHybrid[D]
    encoder: EncoderHybrid[D]

    def __init__(self, decoder: DecoderHybrid[D], encoder: EncoderHybrid[D]):
        self.decoder = decoder
        self.encoder = encoder
