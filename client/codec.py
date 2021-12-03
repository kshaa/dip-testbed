"""Generic data serializer between Raw <-> Serializable <-> Domain"""

from __future__ import annotations
from typing import TypeVar, Generic, Callable
from result import Result, Err


class CodecParseException(Exception):
    """Exception thrown by failing decoders"""
    def __eq__(self, other) -> bool:
        return str(self) == str(other)


R = TypeVar('R')
S = TypeVar('S')
D = TypeVar('D')
D2 = TypeVar('D2')


class Decoder(Generic[R, S, D]):
    """Generic data decoder between Raw <-> Serializable <-> Domain"""

    def __init__(self, decode: Callable[[S], Result[D, CodecParseException]]):
        self.decode = decode

    def raw_decode(self, value: R) -> Result[D, CodecParseException]:
        """Decode raw directly to domain"""
        serializable = self.raw_as_serializable(value)
        if isinstance(serializable, Err):
            return serializable
        return self.decode(serializable.value)

    @staticmethod
    def raw_as_serializable(raw: R) -> Result[S, CodecParseException]:
        """Unserialize raw type into a serializable type"""
        pass

    @staticmethod
    def identity() -> Decoder[R, S, S]:
        """Decoder where domain is same as serializable"""
        pass


class Encoder(Generic[R, S, D]):
    """Generic data encoder between Raw <-> Serializable <-> Domain"""

    def __init__(self, encode: Callable[[D], S]):
        self.encode = encode

    def raw_encode(self, value: D) -> R:
        """Serialize domain directly to raw"""
        serializable = self.encode(value)
        return self.serializable_as_raw(serializable)

    @staticmethod
    def serializable_as_raw(serializable: S) -> R:
        """Serialize serializable type into a raw type"""
        pass

    @staticmethod
    def identity() -> Encoder[R, S, S]:
        """Encoder where domain is same as serializable"""
        pass


class Codec(Generic[R, S, D]):
    """Serialization codec between Raw <-> Serializable <-> Domain"""
    decoder: Decoder[R, S, D]
    encoder: Encoder[R, S, D]

    def __init__(self, decoder: Decoder[R, S, D], encoder: Encoder[R, S, D]):
        self.decoder = decoder
        self.encoder = encoder

    @staticmethod
    def serializable_as_raw(self, serializable: S) -> R:
        """Serialize raw type into a serializable type"""
        pass
