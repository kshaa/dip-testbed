"""Module containing any JSON-from/to-Python serialization-specific logic"""

from typing import Dict, Type, TypeVar, List
from result import Result, Err, Ok
from codec import CodecParseException
from codec import Encoder, Decoder
from functools import partial

RAW = TypeVar('RAW')
SERIALIZABLE = TypeVar('SERIALIZABLE')
DOMAIN = TypeVar('DOMAIN')


# List
def list_decode(
    decoder: Decoder[RAW, SERIALIZABLE, DOMAIN],
    serializable: SERIALIZABLE
) -> Result[List[SERIALIZABLE], CodecParseException]:
    """Un-serialize list of serializable types as domain types"""
    if isinstance(serializable, list):
        domain_results = []
        for serializable in serializable:
            domain_result = decoder.decode(serializable)
            if isinstance(domain_result, Err):
                return domain_result
            else:
                domain_results.append(domain_result.value)
        return Ok(domain_results)
    else:
        return Err(CodecParseException("Object must be a list"))


def list_decoder(
    decoder: Decoder[RAW, SERIALIZABLE, DOMAIN]
) -> Decoder[RAW, SERIALIZABLE, List[DOMAIN]]:
    """Decoder for un-serializing list of serializable types as domain types"""
    return Decoder(partial(list_decode, decoder))


def list_encode(
    encoder: Encoder[RAW, SERIALIZABLE, DOMAIN],
    domains: List[DOMAIN]
) -> List[SERIALIZABLE]:
    """Serialize list of domain types as serializable types"""
    serializables = []
    for domain in domains:
        serializable = encoder.encode(domain)
        serializables.append(serializable)
    return serializables


def list_encoder(
    encoder: Encoder[RAW, SERIALIZABLE, DOMAIN]
) -> Encoder[RAW, SERIALIZABLE, List[DOMAIN]]:
    """Encoder for serializing list of domain types as serializable types"""
    return Encoder(partial(list_encode, encoder))


# Union
DOMAIN_UNION = TypeVar('DOMAIN_UNION')
SERIALIZABLE_UNION = TypeVar('SERIALIZABLE_UNION')


def union_encode(
    encoders: Dict[Type[DOMAIN], Encoder[RAW, SERIALIZABLE, DOMAIN]],
    value: DOMAIN
) -> SERIALIZABLE_UNION:
    """Encode from domain from multiple separate encoders"""
    for clazz, encoder in encoders.items():
        if isinstance(value, clazz):
            return encoder.encode(value)
    # Not very functional, if this becomes a problem, refactor Encoder result type :/
    raise CodecParseException(f"This encoder can't encode {type(value).__name__}")


def union_encoder(
    encoders: Dict[Type[DOMAIN], Encoder[RAW, SERIALIZABLE, DOMAIN]]
) -> Encoder[RAW, SERIALIZABLE, DOMAIN_UNION]:
    """Creates one whole Encoder from multiple separate Encoders"""
    return Encoder(partial(union_encode, encoders))


def union_decode(
    decoders: Dict[Type[DOMAIN], Decoder[RAW, SERIALIZABLE, DOMAIN]],
    value: SERIALIZABLE
) -> Result[DOMAIN, CodecParseException]:
    """Creates one whole Decoder from multiple separate Decoders"""
    for _, decoder in decoders.items():
        result = decoder.decode(value)
        if isinstance(result, Ok):
            return Ok(result.value)
    return Err(CodecParseException("Failed to decode any message from decoder union"))


def union_decoder(
    decoders: Dict[Type[DOMAIN], Decoder[RAW, SERIALIZABLE, DOMAIN]]
) -> Decoder[RAW, SERIALIZABLE, DOMAIN_UNION]:
    """Creates one whole Decoder from multiple separate Decoders"""
    return Decoder(partial(union_decode, decoders))

