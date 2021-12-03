"""Module containing any JSON-from/to-Python serialization-specific logic"""

import uuid
from functools import partial
from typing import Type, TypeVar, Dict, Tuple
from result import Result, Err, Ok
from codec import CodecParseException
from codec_json import EncoderJSON, DecoderJSON, CodecJSON, JSON
import protocol
import backend_domain
from serial_util import SerialConfig


# String
def string_decode_json(value: JSON) -> Result[str, CodecParseException]:
    """Decode string from JSON"""
    if not isinstance(value, str):
        return Err(CodecParseException("Message must be string"))
    return value


STRING_ENCODER_JSON: EncoderJSON[str] = EncoderJSON(lambda x: x)
STRING_DECODER_JSON: DecoderJSON[str] = DecoderJSON(string_decode_json)
STRING_CODEC_JSON: CodecJSON[str] = CodecJSON(STRING_DECODER_JSON, STRING_ENCODER_JSON)

# protocol.NamedMessage
NAMED_MESSAGE = TypeVar('NAMED_MESSAGE')
NAMED_MESSAGE_UNION = TypeVar('NAMED_MESSAGE_UNION')


def named_message_decode_json(name: str, value: JSON) -> Result[JSON, CodecParseException]:
    """Un-serialize named message from JSON"""
    if isinstance(value, dict):
        command = value.get("command")
        if not isinstance(command, str):
            return Err(CodecParseException("Message requires string 'command' field"))
        if not command == name:
            return Err(CodecParseException("Unknown message command name"))
        if "payload" not in value:
            return Err(CodecParseException("Message requires 'payload' field"))
        payload = value.get("payload")
        return Ok(payload)
    else:
        return Err(CodecParseException("Message must be an object"))


def named_message_decoder_json(name: str) -> DecoderJSON[JSON]:
    """Create named message decoder"""
    return DecoderJSON(partial(named_message_encode_json, name))


def named_message_union_decode(
    decoders: Dict[Type[NAMED_MESSAGE], Tuple[str, DecoderJSON[NAMED_MESSAGE]]],
    value: JSON
) -> NAMED_MESSAGE_UNION:
    """Decode named message union"""
    for _, (name, decoder) in decoders.items():
        payload_result = named_message_decode_json(name, value)
        if isinstance(payload_result, Ok):
            result = decoder.decode(payload_result.value)
            if isinstance(result, Ok):
                return Ok(result.value)
    return Err(CodecParseException("Failed to decode any named message from decoder union"))


def named_message_union_decoder_json(
    decoders: Dict[Type[NAMED_MESSAGE], Tuple[str, DecoderJSON[NAMED_MESSAGE]]]
) -> DecoderJSON[NAMED_MESSAGE]:
    """Create named message union decoder"""
    return DecoderJSON(partial(named_message_union_decode, decoders))


def named_message_encode_json(name: str, value: JSON) -> JSON:
    """Serialize named message to JSON"""
    return {
        "command": name,
        "payload": value
    }


def named_message_encoder_json(name: str) -> EncoderJSON[JSON]:
    """Create named message encoder"""
    return EncoderJSON(partial(named_message_encode_json, name))


def named_message_union_encode_json(
    encoders: Dict[Type[NAMED_MESSAGE], Tuple[str, EncoderJSON[NAMED_MESSAGE]]],
    value: NAMED_MESSAGE_UNION
) -> JSON:
    """Encode named message union"""
    for clazz, (name, encoder) in encoders.items():
        if isinstance(value, clazz):
            return named_message_encode_json(name, encoder.encode(value))
    # Not very functional, if this becomes a problem, refactor Encoder result type :/
    raise CodecParseException(f"This encoder can't encode {type(value).__name__}")


def named_message_union_encoder_json(
    encoders: Dict[Type[NAMED_MESSAGE], Tuple[str, EncoderJSON[NAMED_MESSAGE]]],
) -> EncoderJSON[NAMED_MESSAGE]:
    """Create named message union encoder"""
    return EncoderJSON(partial(named_message_union_encode_json, encoders))


# protocol.UploadMessage
def upload_message_encode_json(value: protocol.UploadMessage) -> JSON:
    """Serialize UploadMessage to JSON"""
    return {
        "softwareId": str(value.software_id)
    }


def upload_message_decode_json(value: JSON) -> Result[protocol.UploadMessage, CodecParseException]:
    """Un-serialize UploadMessage from JSON"""
    if isinstance(value, dict):
        firmware_id = value.get("softwareId")
        if isinstance(firmware_id, str):
            try:
                return Ok(protocol.UploadMessage(uuid.UUID(firmware_id)))
            except Exception as e:
                return Err(CodecParseException(f"UploadMessage .firmware_id isn't valid UUID: {e}"))
        else:
            return Err(CodecParseException("UploadMessage must have .firmware_id string"))
    else:
        return Err(CodecParseException("UploadMessage must be an object"))


UPLOAD_MESSAGE_ENCODER_JSON: EncoderJSON[protocol.UploadMessage] = EncoderJSON(upload_message_encode_json)
UPLOAD_MESSAGE_DECODER_JSON: DecoderJSON[protocol.UploadMessage] = DecoderJSON(upload_message_decode_json)
UPLOAD_MESSAGE_CODEC_JSON: CodecJSON[protocol.UploadMessage] = \
    CodecJSON(UPLOAD_MESSAGE_DECODER_JSON, UPLOAD_MESSAGE_ENCODER_JSON)


# protocol.UploadResultMessage
def upload_result_message_encode_json(value: protocol.UploadResultMessage) -> JSON:
    """Serialize UploadResultMessage to JSON"""
    return {
        "error": value.error
    }


def upload_result_message_decode_json(value: JSON) -> Result[protocol.UploadResultMessage, CodecParseException]:
    """Un-serialize UploadResultMessage from JSON"""
    if isinstance(value, dict):
        error = value.get("error")
        if isinstance(error, str) or error is None:
            return Ok(protocol.UploadResultMessage(error))
        else:
            return Err(CodecParseException("UploadResultMessage must have .error as null or string"))
    else:
        return Err(CodecParseException("UploadResultMessage must be an object"))


UPLOAD_RESULT_MESSAGE_ENCODER_JSON: EncoderJSON[protocol.UploadResultMessage] = \
    EncoderJSON(upload_result_message_encode_json)
UPLOAD_RESULT_MESSAGE_DECODER_JSON: DecoderJSON[protocol.UploadResultMessage] = \
    DecoderJSON(upload_result_message_decode_json)
UPLOAD_RESULT_MESSAGE_CODEC_JSON: CodecJSON[protocol.UploadResultMessage] = \
    CodecJSON(UPLOAD_RESULT_MESSAGE_DECODER_JSON, UPLOAD_RESULT_MESSAGE_ENCODER_JSON)


# protocol.PingMessage
def ping_message_encode_json(_: protocol.PingMessage) -> JSON:
    """Serialize PingMessage to JSON"""
    return {}


def ping_message_decode_json(value: JSON) -> Result[protocol.PingMessage, CodecParseException]:
    """Un-serialize PingMessage from JSON"""
    if isinstance(value, dict):
        return Ok(protocol.PingMessage())
    else:
        return Err(CodecParseException("PingMessage must be an object"))


PING_MESSAGE_ENCODER_JSON: EncoderJSON[protocol.PingMessage] = \
    EncoderJSON(ping_message_encode_json)
PING_MESSAGE_DECODER_JSON: DecoderJSON[protocol.PingMessage] = \
    DecoderJSON(ping_message_decode_json)
PING_MESSAGE_CODEC_JSON: CodecJSON[protocol.UploadResultMessage] = \
    CodecJSON(UPLOAD_RESULT_MESSAGE_DECODER_JSON, UPLOAD_RESULT_MESSAGE_ENCODER_JSON)


# protocol.CreateUserMessage
def create_user_message_encode_json(value: protocol.CreateUserMessage) -> JSON:
    """Serialize CreateUserMessage to JSON"""
    return {
        "username": value.username,
        "password": value.password
    }


CREATE_USER_MESSAGE_ENCODER_JSON: EncoderJSON[protocol.CreateUserMessage] = \
    EncoderJSON(create_user_message_encode_json)


# protocol.CreateUserMessage
def create_hardware_message_encode_json(value: protocol.CreateHardwareMessage) -> JSON:
    """Serialize CreateHardwareMessage to JSON"""
    return {
        "name": value.name
    }


CREATE_HARDWARE_MESSAGE_ENCODER_JSON: EncoderJSON[protocol.CreateHardwareMessage] = \
    EncoderJSON(create_hardware_message_encode_json)


# protocol.SuccessMessage
SUCCESS_GENERIC = TypeVar('SUCCESS_GENERIC')


def success_message_decode_json(
    decoder: DecoderJSON[SUCCESS_GENERIC],
    value: JSON
) -> Result[protocol.SuccessMessage[SUCCESS_GENERIC], CodecParseException]:
    """Un-serialize SuccessMessage from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SuccessMessage must be an object"))
    success = value.get("success")
    content_result = decoder.decode(success)
    if isinstance(content_result, Err):
        return Err(content_result.value)
    return Ok(protocol.SuccessMessage(content_result.value))


def success_message_decoder_json(
    decoder: DecoderJSON[SUCCESS_GENERIC]
) -> DecoderJSON[SUCCESS_GENERIC]:
    """Create a success message decoder function instance"""
    return DecoderJSON(partial(success_message_decode_json, decoder))


# protocol.FailureMessage
FAILURE_GENERIC = TypeVar('FAILURE_GENERIC')


def failure_message_decode_json(
    decoder: DecoderJSON[FAILURE_GENERIC],
    value: str
) -> Result[protocol.FailureMessage[FAILURE_GENERIC], CodecParseException]:
    """Un-serialize FailureMessage from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("FailureMessage must be an object"))
    failure = value.get("failure")
    content_result = decoder.decode(failure)
    if isinstance(content_result, Err):
        return Err(content_result.value)
    return Ok(protocol.FailureMessage(content_result.value))


def failure_message_decoder_json(
    decoder: DecoderJSON[FAILURE_GENERIC]
) -> DecoderJSON[protocol.FailureMessage[FAILURE_GENERIC]]:
    """Create a failure message decoder function instance"""
    return DecoderJSON(partial(failure_message_decode_json, decoder))


# protocol.SerialMonitorRequest
def serial_monitor_request_encode_json(value: protocol.SerialMonitorRequest) -> JSON:
    """Serialize SerialMonitorRequest to JSON"""
    return {
        "serialConfig": None if value.config is None else {
            "receiveSize": value.config.receive_size,
            "baudrate": value.config.baudrate,
            "timeout": value.config.timeout
        }
    }


def serial_monitor_request_decode_json(value: JSON) -> Result[protocol.SerialMonitorRequest, CodecParseException]:
    """Un-serialize UploadMessage from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SerialMonitorRequest must be an object"))

    serial_config = value.get("serialConfig")
    if serial_config is None:
        return Ok(protocol.SerialMonitorRequest(None))
    elif not isinstance(serial_config, dict):
        return Err(CodecParseException("SerialMonitorRequest .serialConfig must be null or object"))

    receive_size = serial_config.get("receiveSize")
    if not isinstance(receive_size, int):
        return Err(CodecParseException("SerialMonitorRequest .receiveSize must be integer"))

    baudrate = serial_config.get("baudrate")
    if not isinstance(baudrate, int):
        return Err(CodecParseException("SerialMonitorRequest .baudrate must be integer"))

    timeout = serial_config.get("timeout")
    if not isinstance(timeout, int):
        return Err(CodecParseException("SerialMonitorRequest .timeout must be integer"))

    return Ok(protocol.SerialMonitorRequest(SerialConfig(receive_size, baudrate, timeout)))


SERIAL_MONITOR_REQUEST_ENCODER_JSON: EncoderJSON[protocol.SerialMonitorRequest] = \
    EncoderJSON(serial_monitor_request_encode_json)
SERIAL_MONITOR_REQUEST_DECODER_JSON: DecoderJSON[protocol.SerialMonitorRequest] = \
    DecoderJSON(serial_monitor_request_decode_json)
SERIAL_MONITOR_REQUEST_CODEC_JSON: CodecJSON[protocol.SerialMonitorRequest] = \
    CodecJSON(SERIAL_MONITOR_REQUEST_DECODER_JSON, SERIAL_MONITOR_REQUEST_ENCODER_JSON)


# protocol.SerialMonitorRequestStop
def serial_monitor_request_stop_encode_json(_: protocol.SerialMonitorRequestStop) -> JSON:
    """Serialize SerialMonitorRequestStop to JSON"""
    return {}


def serial_monitor_request_stop_decode_json(
    value: JSON
) -> Result[protocol.SerialMonitorRequestStop, CodecParseException]:
    """Un-serialize SerialMonitorRequestStop from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SerialMonitorRequestStop must have payload as object"))
    return Ok(protocol.SerialMonitorRequestStop())


SERIAL_MONITOR_REQUEST_STOP_ENCODER_JSON: EncoderJSON[protocol.SerialMonitorRequestStop] = \
    EncoderJSON(serial_monitor_request_stop_encode_json)
SERIAL_MONITOR_REQUEST_STOP_DECODER_JSON: DecoderJSON[protocol.SerialMonitorRequestStop] = \
    DecoderJSON(serial_monitor_request_stop_decode_json)
SERIAL_MONITOR_REQUEST_STOP_CODEC_JSON: CodecJSON[protocol.SerialMonitorRequestStop] = \
    CodecJSON(SERIAL_MONITOR_REQUEST_STOP_DECODER_JSON, SERIAL_MONITOR_REQUEST_STOP_ENCODER_JSON)


# protocol.SerialMonitorResult
def serial_monitor_result_encode_json(value: protocol.SerialMonitorResult) -> JSON:
    """Serialize SerialMonitorResult to JSON"""
    return {
        "error": value.error
    }


def serial_monitor_result_decode_json(value: JSON) -> Result[protocol.SerialMonitorResult, CodecParseException]:
    """Un-serialize SerialMonitorRequest from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SerialMonitorRequest must be an object"))
    error = value.get("error")
    if not isinstance(error, str) and error is not None:
        return Err(CodecParseException("SerialMonitorRequest must have .error as null or string"))
    return Ok(protocol.SerialMonitorResult(error))


SERIAL_MONITOR_RESULT_ENCODER_JSON: EncoderJSON[protocol.SerialMonitorResult] = \
    EncoderJSON(serial_monitor_result_encode_json)
SERIAL_MONITOR_RESULT_DECODER_JSON: DecoderJSON[protocol.SerialMonitorResult] = \
    DecoderJSON(serial_monitor_result_decode_json)
SERIAL_MONITOR_RESULT_CODEC_JSON: CodecJSON[protocol.SerialMonitorResult] = \
    CodecJSON(SERIAL_MONITOR_RESULT_DECODER_JSON, SERIAL_MONITOR_RESULT_ENCODER_JSON)


# protocol.SerialMonitorMessageToAgent
def serial_monitor_message_to_agent_encode_json(value: protocol.SerialMonitorMessageToAgent) -> JSON:
    """Serialize SerialMonitorMessageToAgent to JSON"""
    return {
        "message": {
            "base64Bytes": value.base64Bytes
        }
    }


def serial_monitor_message_to_agent_decode_json(
    value: JSON
) -> Result[protocol.SerialMonitorMessageToAgent, CodecParseException]:
    """Un-serialize SerialMonitorRequest from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SerialMonitorMessageToAgent must be an object"))
    message = value.get("message")
    if not isinstance(message, dict):
        return Err(CodecParseException("SerialMonitorMessageToAgent must have .message as object"))
    base64_bytes = message.get("base64Bytes")
    if not isinstance(base64_bytes, str):
        return Err(CodecParseException("SerialMonitorMessageToAgent must have .base64Bytes as string"))
    return Ok(protocol.SerialMonitorMessageToAgent(base64_bytes))


SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_JSON: EncoderJSON[protocol.SerialMonitorMessageToAgent] = \
    EncoderJSON(serial_monitor_message_to_agent_encode_json)
SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_JSON: DecoderJSON[protocol.SerialMonitorMessageToAgent] = \
    DecoderJSON(serial_monitor_message_to_agent_decode_json)
SERIAL_MONITOR_MESSAGE_TO_AGENT_CODEC_JSON: CodecJSON[protocol.SerialMonitorMessageToAgent] = \
    CodecJSON(SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_JSON, SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_JSON)


# protocol.SerialMonitorMessageToClient
def serial_monitor_message_to_client_encode_json(value: protocol.SerialMonitorMessageToClient) -> JSON:
    """Serialize SerialMonitorMessageToClient to JSON"""
    return {
        "message": {
            "base64Bytes": value.base64Bytes
        }
    }


def serial_monitor_message_to_client_decode_json(
    value: JSON
) -> Result[protocol.SerialMonitorMessageToClient, CodecParseException]:
    """Un-serialize SerialMonitorMessageToClient from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SerialMonitorMessageToClient must be an object"))
    message = value.get("message")
    if not isinstance(message, dict):
        return Err(CodecParseException("SerialMonitorMessageToClient must have .message as object"))
    base64_bytes = message.get("base64Bytes")
    if not isinstance(base64_bytes, str):
        return Err(CodecParseException("SerialMonitorMessageToClient must have .base64Bytes as string"))
    return Ok(protocol.SerialMonitorMessageToClient(base64_bytes))


SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_JSON: EncoderJSON[protocol.SerialMonitorMessageToClient] = \
    EncoderJSON(serial_monitor_message_to_client_encode_json)
SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_JSON: DecoderJSON[protocol.SerialMonitorMessageToClient] = \
    DecoderJSON(serial_monitor_message_to_client_decode_json)
SERIAL_MONITOR_MESSAGE_TO_CLIENT_CODEC_JSON: CodecJSON[protocol.SerialMonitorMessageToClient] = \
    CodecJSON(SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_JSON, SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_JSON)


# protocol.MonitorUnavailable
def monitor_unavailable_encode_json(value: protocol.MonitorUnavailable) -> JSON:
    """Serialize MonitorUnavailable to JSON"""
    return {
        "reason": value.reason
    }


def monitor_unavailable_decode_json(
    value: JSON
) -> Result[protocol.MonitorUnavailable, CodecParseException]:
    """Un-serialize MonitorUnavailable from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("MonitorUnavailable must be an object"))
    reason = value.get("reason")
    if not isinstance(reason, str):
        return Err(CodecParseException("MonitorUnavailable must have .reason as string"))
    return Ok(protocol.MonitorUnavailable(reason))


MONITOR_UNAVAILABLE_ENCODER_JSON: EncoderJSON[protocol.MonitorUnavailable] = \
    EncoderJSON(monitor_unavailable_encode_json)
MONITOR_UNAVAILABLE_DECODER_JSON: DecoderJSON[protocol.MonitorUnavailable] = \
    DecoderJSON(monitor_unavailable_decode_json)
MONITOR_UNAVAILABLE_CODEC_JSON: CodecJSON[protocol.MonitorUnavailable] = \
    CodecJSON(MONITOR_UNAVAILABLE_DECODER_JSON, MONITOR_UNAVAILABLE_ENCODER_JSON)


# protocol.CommonIncomingMessage
COMMON_INCOMING_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    protocol.UploadMessage: ("uploadSoftwareRequest", UPLOAD_MESSAGE_ENCODER_JSON),
    protocol.SerialMonitorRequest: ("serialMonitorRequest", SERIAL_MONITOR_REQUEST_ENCODER_JSON),
    protocol.SerialMonitorRequestStop: ("serialMonitorRequestStop", SERIAL_MONITOR_REQUEST_STOP_ENCODER_JSON),
    protocol.SerialMonitorMessageToAgent: ("serialMonitorRequestToAgent", SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_JSON)
})
COMMON_INCOMING_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    protocol.UploadMessage: ("uploadSoftwareRequest", UPLOAD_MESSAGE_DECODER_JSON),
    protocol.SerialMonitorRequest: ("serialMonitorRequest", SERIAL_MONITOR_REQUEST_DECODER_JSON),
    protocol.SerialMonitorRequestStop: ("serialMonitorRequestStop", SERIAL_MONITOR_REQUEST_STOP_DECODER_JSON),
    protocol.SerialMonitorMessageToAgent: ("serialMonitorRequestToAgent", SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_JSON)
})
COMMON_INCOMING_MESSAGE_CODEC_JSON = CodecJSON(
    COMMON_INCOMING_MESSAGE_DECODER_JSON,
    COMMON_INCOMING_MESSAGE_ENCODER_JSON)

# protocol.CommonOutgoingMessage
COMMON_OUTGOING_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    protocol.UploadResultMessage: ("uploadSoftwareRequest", UPLOAD_RESULT_MESSAGE_ENCODER_JSON),
    protocol.PingMessage: ("ping", PING_MESSAGE_ENCODER_JSON),
    protocol.SerialMonitorResult: ("serialMonitorResult", SERIAL_MONITOR_RESULT_ENCODER_JSON),
    protocol.SerialMonitorMessageToClient: ("serialMonitorMessageToClient", SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_JSON)
})
COMMON_OUTGOING_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    protocol.UploadResultMessage: ("uploadSoftwareRequest", UPLOAD_RESULT_MESSAGE_DECODER_JSON),
    protocol.PingMessage: ("ping", PING_MESSAGE_DECODER_JSON),
    protocol.SerialMonitorResult: ("serialMonitorResult", SERIAL_MONITOR_RESULT_DECODER_JSON),
    protocol.SerialMonitorMessageToClient: ("serialMonitorMessageToClient", SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_JSON)
})
COMMON_OUTGOING_MESSAGE_CODEC_JSON = CodecJSON(
    COMMON_OUTGOING_MESSAGE_DECODER_JSON,
    COMMON_OUTGOING_MESSAGE_ENCODER_JSON)

# protocol.MonitorListenerIncomingMessage
MONITOR_LISTENER_INCOMING_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    protocol.MonitorUnavailable: ("monitorUnavailable", MONITOR_UNAVAILABLE_ENCODER_JSON),
    protocol.SerialMonitorMessageToClient: ("serialMessageToClient", SERIAL_MONITOR_MESSAGE_TO_CLIENT_ENCODER_JSON)
})
MONITOR_LISTENER_INCOMING_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    protocol.MonitorUnavailable: ("monitorUnavailable", MONITOR_UNAVAILABLE_DECODER_JSON),
    protocol.SerialMonitorMessageToClient: ("serialMessageToClient", SERIAL_MONITOR_MESSAGE_TO_CLIENT_DECODER_JSON)
})
MONITOR_LISTENER_INCOMING_MESSAGE_CODEC_JSON = CodecJSON(
    MONITOR_LISTENER_INCOMING_MESSAGE_DECODER_JSON,
    MONITOR_LISTENER_INCOMING_MESSAGE_ENCODER_JSON)

# protocol.MonitorListenerOutgoingMessage
MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    protocol.SerialMonitorMessageToAgent: ("serialMessageToAgent", SERIAL_MONITOR_MESSAGE_TO_AGENT_ENCODER_JSON)
})
MONITOR_LISTENER_OUTGOING_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    protocol.SerialMonitorMessageToAgent: ("serialMessageToAgent", SERIAL_MONITOR_MESSAGE_TO_AGENT_DECODER_JSON)
})
MONITOR_LISTENER_OUTGOING_MESSAGE_CODEC_JSON = CodecJSON(
    MONITOR_LISTENER_OUTGOING_MESSAGE_DECODER_JSON,
    MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER_JSON)


# backend_domain.User
def user_encode_json(value: backend_domain.User) -> JSON:
    """Encode User into JSON"""
    return {
        "id": str(value.id),
        "username": value.username
    }


def user_decode_json(
    value: JSON,
) -> Result[backend_domain.User, CodecParseException]:
    """Un-serialize User from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("User must be an object"))
    try:
        user_id = uuid.UUID(value.get("id"))
    except Exception as e:
        return Err(CodecParseException(f"User id isn't valid UUID: {e}"))
    username = value.get("username")
    if username is None:
        return Err(CodecParseException("User must contain username"))
    return Ok(backend_domain.User(user_id, username))


USER_ENCODER_JSON = EncoderJSON(user_encode_json)
USER_DECODER_JSON = DecoderJSON(user_decode_json)
USER_CODEC_JSON = CodecJSON(USER_DECODER_JSON, USER_ENCODER_JSON)

# backend_domain.Hardware
def hardware_encode_json(value: backend_domain.Hardware) -> JSON:
    """Serialize hardware into JSON"""
    return {
        "id": str(value.id),
        "name": value.name,
        "ownerId": str(value.owner_id)
    }


def hardware_decode_json(
    value: JSON,
) -> Result[backend_domain.Hardware, CodecParseException]:
    """Un-serialize Hardware from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("Hardware must be an object"))
    try:
        hardware_id = uuid.UUID(value.get("id"))
    except Exception as e:
        return Err(CodecParseException(f"Hardware id isn't valid UUID: {e}"))
    name = value.get("name")
    if name is None:
        return Err(CodecParseException("Hardware must contain name"))
    try:
        owner_uuid = uuid.UUID(value.get("ownerId"))
    except Exception as e:
        return Err(CodecParseException(f"Hardware owner id isn't valid UUID: {e}"))
    return Ok(backend_domain.Hardware(hardware_id, name, owner_uuid))


HARDWARE_ENCODER_JSON = EncoderJSON(hardware_encode_json)
HARDWARE_DECODER_JSON = DecoderJSON(hardware_decode_json)
HARDWARE_CODEC_JSON = CodecJSON(HARDWARE_DECODER_JSON, HARDWARE_ENCODER_JSON)


# backend_domain.Software
def software_encode_json(value: backend_domain.Software) -> JSON:
    """Serialize software into JSON"""
    return {
        "id": str(value.id),
        "name": value.name,
        "ownerId": str(value.owner_id)
    }


def software_decode_json(
    value: JSON,
) -> Result[backend_domain.Software, CodecParseException]:
    """Un-serialize Software from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("Software must be an object"))
    try:
        software_id = uuid.UUID(value.get("id"))
    except Exception as e:
        return Err(CodecParseException(f"Software id isn't valid UUID: {e}"))
    name = value.get("name")
    if name is None:
        return Err(CodecParseException("Software must contain name"))
    try:
        owner_id = uuid.UUID(value.get("ownerId"))
    except Exception as e:
        return Err(CodecParseException(f"Software owner id isn't valid UUID: {e}"))
    return Ok(backend_domain.Software(software_id, name, owner_id))


SOFTWARE_ENCODER_JSON = EncoderJSON(software_encode_json)
SOFTWARE_DECODER_JSON = DecoderJSON(software_decode_json)
SOFTWARE_CODEC_JSON = CodecJSON(SOFTWARE_DECODER_JSON, SOFTWARE_ENCODER_JSON)