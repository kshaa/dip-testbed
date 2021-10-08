from typing import TypeVar, Generic, Callable
from fp import Either

T = TypeVar('T')


class Decoder(Generic[T]):
    def __init__(self, transform: Callable[[str], Either[Exception, T]]):
        self.transform = transform


class Encoder(Generic[T]):
    def __init__(self, transform: Callable[[T], str]):
        self.transform = transform


class Codec(Generic[T]):
    decoder: Decoder[T]
    encoder: Encoder[T]

    def __init__(self, decoder: Decoder[T], encoder: Encoder[T]):
        self.decoder = decoder
        self.encoder = encoder

    def encode(self, value: T) -> str:
        return self.encoder.transform(value)

    def decode(self, value: str) -> Either[Exception, T]:
        return self.decoder.transform(value)


identityEncoder: Encoder[str] = Encoder(lambda x: x)
identityDecoder: Decoder[str] = Decoder(lambda x: Either.as_right(x))
identityCodec: Codec[str] = Codec(identityDecoder, identityEncoder)
