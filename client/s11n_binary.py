"""Module containing any binary-from/to-Python serialization-specific logic"""

import protocol
from result import Result, Ok
from codec import CodecParseException
from codec_binary import BINARY, EncoderBinary, DecoderBinary, CodecBinary


# protocol.SerialMonitorMessageToAgent
def serial_monitor_message_to_agent_encode_binary(value: protocol.SerialMonitorMessageToAgent) -> BINARY:
    """Serialize SerialMonitorMessageToAgent to BINARY"""
    return value.to_bytes()


def serial_monitor_message_to_agent_decode_binary(
    value: BINARY
) -> Result[protocol.SerialMonitorMessageToAgent, CodecParseException]:
    """Un-serialize SerialMonitorRequest from BINARY"""
    return Ok(protocol.SerialMonitorMessageToAgent.from_bytes(value))


SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_BINARY: EncoderBinary[protocol.SerialMonitorMessageToAgent] = \
    EncoderBinary(serial_monitor_message_to_agent_encode_binary)
SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_BINARY: DecoderBinary[protocol.SerialMonitorMessageToAgent] = \
    DecoderBinary(serial_monitor_message_to_agent_decode_binary)
SERIAL_MONITOR_MESSAGE_TO_AGENT_CODEC_BINARY: CodecBinary[protocol.SerialMonitorMessageToAgent] = \
    CodecBinary(SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_BINARY, SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_BINARY)


# protocol.SerialMonitorMessageToClient
def serial_monitor_message_to_client_encode_binary(value: protocol.SerialMonitorMessageToClient) -> BINARY:
    """Serialize SerialMonitorMessageToClient to JSON"""
    return value.to_bytes()


def serial_monitor_message_to_client_decode_binary(
    value: BINARY
) -> Result[protocol.SerialMonitorMessageToClient, CodecParseException]:
    """Un-serialize SerialMonitorMessageToClient from JSON"""
    return Ok(protocol.SerialMonitorMessageToClient.from_bytes(value))


SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_BINARY: EncoderBinary[protocol.SerialMonitorMessageToClient] = \
    EncoderBinary(serial_monitor_message_to_client_encode_binary)
SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_BINARY: DecoderBinary[protocol.SerialMonitorMessageToClient] = \
    DecoderBinary(serial_monitor_message_to_client_decode_binary)
SERIAL_MONITOR_MESSAGE_TO_CLIENT_CODEC_BINARY: CodecBinary[protocol.SerialMonitorMessageToClient] = \
    CodecBinary(SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_BINARY, SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_BINARY)
