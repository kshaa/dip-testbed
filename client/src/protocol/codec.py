"""Generic data serializer between Raw <-> Serializable <-> Domain"""

from __future__ import annotations
from typing import TypeVar, Generic, Callable
from result import Result


class CodecParseException(Exception):
    """Exception thrown by failing decoders"""
    def __eq__(self, other) -> bool:
        return str(self) == str(other)


R = TypeVar('R')
D = TypeVar('D')


class Decoder(Generic[R, D]):
    """Generic data decoder between Raw <-> Domain"""

    def __init__(self, decode: Callable[[R], Result[D, CodecParseException]]):
        self.decode = decode


class Encoder(Generic[R, D]):
    """Generic data encoder between Raw <->  Domain"""

    def __init__(self, encode: Callable[[D], R]):
        self.encode = encode


class Codec(Generic[R, D]):
    """Serialization codec between Raw <-> Domain"""
    decoder: Decoder[R, D]
    encoder: Encoder[R, D]

    def __init__(self, decoder: Decoder[R, D], encoder: Encoder[R, D]):
        self.decoder = decoder
        self.encoder = encoder
