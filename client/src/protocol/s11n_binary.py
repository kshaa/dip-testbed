"""Module containing any binary-from/to-Python serialization-specific logic"""

from src.domain import monitor_message
from result import Result, Ok
from src.protocol.codec import CodecParseException
from src.protocol.codec_binary import BINARY, EncoderBinary, DecoderBinary, CodecBinary


# protocol.SerialMonitorMessageToAgent
def serial_monitor_message_to_agent_encode_binary(value: monitor_message.SerialMonitorMessageToAgent) -> BINARY:
    """Serialize SerialMonitorMessageToAgent to BINARY"""
    return value.content_bytes


def serial_monitor_message_to_agent_decode_binary(
    value: BINARY
) -> Result[monitor_message.SerialMonitorMessageToAgent, CodecParseException]:
    """Un-serialize SerialMonitorRequest from BINARY"""
    return Ok(monitor_message.SerialMonitorMessageToAgent(value))


SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_BINARY: EncoderBinary[monitor_message.SerialMonitorMessageToAgent] = \
    EncoderBinary(serial_monitor_message_to_agent_encode_binary)
SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_BINARY: DecoderBinary[monitor_message.SerialMonitorMessageToAgent] = \
    DecoderBinary(serial_monitor_message_to_agent_decode_binary)
SERIAL_MONITOR_MESSAGE_TO_AGENT_CODEC_BINARY: CodecBinary[monitor_message.SerialMonitorMessageToAgent] = \
    CodecBinary(SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_BINARY, SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_BINARY)


# protocol.SerialMonitorMessageToClient
def serial_monitor_message_to_client_encode_binary(value: monitor_message.SerialMonitorMessageToClient) -> BINARY:
    """Serialize SerialMonitorMessageToClient to JSON"""
    return value.content_bytes


def serial_monitor_message_to_client_decode_binary(
    value: BINARY
) -> Result[monitor_message.SerialMonitorMessageToClient, CodecParseException]:
    """Un-serialize SerialMonitorMessageToClient from JSON"""
    return Ok(monitor_message.SerialMonitorMessageToClient(value))


SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_BINARY: EncoderBinary[monitor_message.SerialMonitorMessageToClient] = \
    EncoderBinary(serial_monitor_message_to_client_encode_binary)
SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_BINARY: DecoderBinary[monitor_message.SerialMonitorMessageToClient] = \
    DecoderBinary(serial_monitor_message_to_client_decode_binary)
SERIAL_MONITOR_MESSAGE_TO_CLIENT_CODEC_BINARY: CodecBinary[monitor_message.SerialMonitorMessageToClient] = \
    CodecBinary(SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_BINARY, SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_BINARY)
