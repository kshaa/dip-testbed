"""Generic Python class instance from/to JSON object codec definition"""

from __future__ import annotations
from typing import TypeVar, Callable
from result import Result
from codec import CodecParseException, Codec, Decoder, Encoder

BINARY = bytes
D = TypeVar('D')
NO_WHITESPACE_SEPERATORS = (',', ':')


class DecoderBinary(Decoder[BINARY, BINARY, D]):
    """Generic data decoder between Raw <-> Serializable <-> Domain"""

    def __init__(self, decode: Callable[[BINARY], Result[D, CodecParseException]]):
        self.decode = decode


class EncoderBinary(Encoder[BINARY, BINARY, D]):
    """Generic data encoder between Raw <-> Serializable <-> Domain"""

    def __init__(self, encode: Callable[[D], BINARY]):
        self.encode = encode


class CodecBinary(Codec[BINARY, BINARY, D]):
    """Serialization codec between Raw <-> Serializable <-> Domain"""
    decoder: DecoderBinary[D]
    encoder: EncoderBinary[D]

    def __init__(self, decoder: DecoderBinary[D], encoder: EncoderBinary[D]):
        self.decoder = decoder
        self.encoder = encoder
