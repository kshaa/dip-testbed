"""Module containing any hybrid-format serialization logic"""

from typing import TypeVar, Type, Dict, Union
from functools import partial
from result import Result
from src.domain import hardware_control_message, monitor_message
from src.protocol import s11n_json, s11n_binary
from src.protocol.codec import Encoder, CodecParseException
from src.protocol.codec_binary import DecoderBinary
from src.protocol.codec_hybrid import EncoderHybrid, DecoderHybrid, CodecHybrid
from src.protocol.codec_json import DecoderJSON

# Binary or JSON serialization
HYBRID_MESSAGE = TypeVar('HYBRID_MESSAGE')


def hybrid_encode(
    encoders: Dict[Type[HYBRID_MESSAGE], Encoder[Union[str, bytes], HYBRID_MESSAGE]],
    value: HYBRID_MESSAGE
) -> Union[str, bytes]:
    """Encode hybrid message"""
    for clazz, encoder in encoders.items():
        if isinstance(value, clazz):
            return encoder.encode(value)
    # Not very functional, if this becomes a problem, refactor Encoder result type :/
    raise CodecParseException(f"This encoder can't encode {type(value).__name__}")


def hybrid_encoder(
    encoders: Dict[Type[HYBRID_MESSAGE], Encoder[Union[str, bytes], HYBRID_MESSAGE]],
) -> EncoderHybrid[HYBRID_MESSAGE]:
    """Build hybrid message format encoder"""
    return EncoderHybrid(partial(hybrid_encode, encoders))


def hybrid_decode(
    json_decoder: DecoderJSON[HYBRID_MESSAGE],
    binary_decoder: DecoderBinary[HYBRID_MESSAGE],
    value: Union[str, bytes]
) -> Result[HYBRID_MESSAGE, CodecParseException]:
    """Decode hybrid message"""
    if isinstance(value, bytes):
        return binary_decoder.decode(value)
    else:
        return json_decoder.decode(value)


def hybrid_decoder(
    binary_decoder: DecoderBinary[HYBRID_MESSAGE],
    json_decoder: DecoderJSON[HYBRID_MESSAGE]
) -> DecoderHybrid[HYBRID_MESSAGE]:
    """Build hybrid message format decoder"""
    return DecoderHybrid(partial(hybrid_decode, json_decoder, binary_decoder))


# protocol.CommonIncomingMessage
COMMON_INCOMING_MESSAGE_ENCODER = hybrid_encoder({
    hardware_control_message.UploadMessage: s11n_json.COMMON_INCOMING_MESSAGE_ENCODER_JSON,
    hardware_control_message.SerialMonitorRequest: s11n_json.COMMON_INCOMING_MESSAGE_ENCODER_JSON,
    hardware_control_message.SerialMonitorRequestStop: s11n_json.COMMON_INCOMING_MESSAGE_ENCODER_JSON,
    hardware_control_message.SerialMonitorMessageToAgent: s11n_binary.SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_BINARY
})
COMMON_INCOMING_MESSAGE_DECODER = hybrid_decoder(
    s11n_binary.SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_BINARY,
    s11n_json.COMMON_INCOMING_MESSAGE_DECODER_JSON)
COMMON_INCOMING_MESSAGE_CODEC = CodecHybrid(COMMON_INCOMING_MESSAGE_DECODER, COMMON_INCOMING_MESSAGE_ENCODER)

# protocol.CommonOutgoingMessage
COMMON_OUTGOING_MESSAGE_ENCODER = hybrid_encoder({
    hardware_control_message.UploadResultMessage: s11n_json.COMMON_OUTGOING_MESSAGE_ENCODER_JSON,
    hardware_control_message.PingMessage: s11n_json.COMMON_OUTGOING_MESSAGE_ENCODER_JSON,
    hardware_control_message.SerialMonitorResult: s11n_json.COMMON_OUTGOING_MESSAGE_ENCODER_JSON,
    monitor_message.MonitorUnavailable: s11n_json.COMMON_OUTGOING_MESSAGE_ENCODER_JSON,
    hardware_control_message.SerialMonitorMessageToClient: s11n_binary.SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_BINARY
})
COMMON_OUTGOING_MESSAGE_DECODER = hybrid_decoder(
    s11n_binary.SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_BINARY,
    s11n_json.COMMON_OUTGOING_MESSAGE_DECODER_JSON)
COMMON_OUTGOING_MESSAGE_CODEC = CodecHybrid(
    COMMON_OUTGOING_MESSAGE_DECODER,
    COMMON_OUTGOING_MESSAGE_ENCODER)

# protocol.MonitorListenerIncomingMessage
MONITOR_LISTENER_INCOMING_MESSAGE_ENCODER = hybrid_encoder({
    monitor_message.MonitorUnavailable: s11n_json.MONITOR_LISTENER_INCOMING_MESSAGE_ENCODER_JSON,
    monitor_message.SerialMonitorMessageToClient: s11n_binary.SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_BINARY
})
MONITOR_LISTENER_INCOMING_MESSAGE_DECODER = hybrid_decoder(
    s11n_binary.SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_BINARY,
    s11n_json.MONITOR_LISTENER_INCOMING_MESSAGE_DECODER_JSON)
MONITOR_LISTENER_INCOMING_MESSAGE_CODEC = CodecHybrid(
    MONITOR_LISTENER_INCOMING_MESSAGE_DECODER,
    MONITOR_LISTENER_INCOMING_MESSAGE_ENCODER)

# protocol.MonitorListenerOutgoingMessage
MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER = hybrid_encoder({
    monitor_message.SerialMonitorMessageToAgent: s11n_binary.SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_BINARY
})
MONITOR_LISTENER_OUTGOING_MESSAGE_DECODER = hybrid_decoder(
    s11n_binary.SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_BINARY,
    DecoderJSON(lambda x: CodecParseException("Invalid message type"))
)
MONITOR_LISTENER_OUTGOING_MESSAGE_CODEC = CodecHybrid(
    MONITOR_LISTENER_OUTGOING_MESSAGE_DECODER,
    MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER)
