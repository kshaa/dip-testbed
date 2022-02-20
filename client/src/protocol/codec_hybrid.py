"""Generic codec definition from/to JSON string & binary bytes"""

from __future__ import annotations
from typing import TypeVar, Callable, Any, Union
from result import Result, Err
from src.protocol.codec import Decoder, CodecParseException, Encoder, Codec
from src.protocol.codec_json import DecoderJSON, EncoderJSON

D = TypeVar('D')


class DecoderHybrid(Decoder[Union[str, bytes], D]):
    """Generic data decoder between Union[str of JSON, bytes] <-> Domain"""

    def __init__(self, decode: Callable[[Union[str, bytes]], Result[D, CodecParseException]]):
        self.decode = decode

    def raw_decode(self, value: Union[str, bytes]) -> Result[D, CodecParseException]:
        """Decode raw directly to domain"""
        serializable = value
        if not isinstance(value, bytes):
            json_result = DecoderJSON.raw_as_serializable(value)
            if isinstance(json_result, Err):
                return serializable
            serializable = json_result.value
        return self.decode(serializable)


class EncoderHybrid(Encoder[Union[str, bytes], D]):
    """Generic data encoder between Union[str of JSON, bytes] <-> Domain"""

    def __init__(self, encode: Callable[[D], Any]):
        self.encode = encode

    def raw_encode(self, value: D) -> Any:
        """Serialize domain directly to raw"""
        serializable = self.encode(value)
        if isinstance(serializable, bytes):
            return serializable
        else:
            return EncoderJSON.serializable_as_raw(serializable)


class CodecHybrid(Codec[Union[str, bytes], D]):
    """Serialization codec between Raw <-> Serializable <-> Domain"""
    decoder: DecoderHybrid[D]
    encoder: EncoderHybrid[D]

    def __init__(self, decoder: DecoderHybrid[D], encoder: EncoderHybrid[D]):
        self.decoder = decoder
        self.encoder = encoder
