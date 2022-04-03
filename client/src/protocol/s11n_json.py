"""Module containing any JSON-from/to-Python serialization-specific logic"""
import base64
from functools import partial
from typing import Type, TypeVar, Dict, Tuple, List
from result import Result, Err, Ok

from src.domain.fancy_byte import FancyByte
from src.domain.managed_uuid import ManagedUUID
from src.domain.minos_chunks import TextChunk, ParsedChunk, DisplayChunk, LEDChunk, SwitchChunk, IndexedButtonChunk
from src.engine.monitor.minos.minos_suite import MinOSSuite, MinOSSuitePacket
from src.protocol.codec import CodecParseException
from src.domain import hardware_control_message, backend_entity, backend_management_message, monitor_message, config, \
    hardware_shared_message, hardware_video_message
from src.protocol.codec_json import JSON, EncoderJSON, DecoderJSON, CodecJSON
from src.service.backend_config import UserPassAuthConfig
from src.service.config_service import ConfigService
from src.service.managed_serial_config import ManagedSerialConfig


# Unit
def unit_decode_json(value: JSON) -> Result[Dict, CodecParseException]:
    """Decode string from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("Message must be object"))
    return Ok(value)


UNIT_DECODER_JSON: DecoderJSON[str] = DecoderJSON(unit_decode_json)


# String
def string_decode_json(value: JSON) -> Result[str, CodecParseException]:
    """Decode string from JSON"""
    if not isinstance(value, str):
        return Err(CodecParseException("Message must be string"))
    return Ok(value)


STRING_ENCODER_JSON: EncoderJSON[str] = EncoderJSON(lambda x: x)
STRING_DECODER_JSON: DecoderJSON[str] = DecoderJSON(string_decode_json)
STRING_CODEC_JSON: CodecJSON[str] = CodecJSON(STRING_DECODER_JSON, STRING_ENCODER_JSON)

# List
RAW = TypeVar('RAW')
DOMAIN = TypeVar('DOMAIN')


def list_decode_json(
    decoder: DecoderJSON[DOMAIN],
    serializable: JSON
) -> Result[List[DOMAIN], CodecParseException]:
    """Un-serialize list of serializable types as domain types"""
    if isinstance(serializable, list):
        domain_results = []
        for serializable in serializable:
            domain_result = decoder.json_decode(serializable)
            if isinstance(domain_result, Err):
                return domain_result
            else:
                domain_results.append(domain_result.value)
        return Ok(domain_results)
    else:
        return Err(CodecParseException("Object must be a list"))


def list_decoder_json(
    decoder: DecoderJSON[DOMAIN]
) -> DecoderJSON[List[DOMAIN]]:
    """Decoder for un-serializing list of serializable types as domain types"""
    return DecoderJSON(partial(list_decode_json, decoder))


def list_encode_json(
    encoder: EncoderJSON[DOMAIN],
    domains: List[DOMAIN]
) -> List[JSON]:
    """Serialize list of domain types as serializable types"""
    serializables = []
    for domain in domains:
        serializable = encoder.json_encode(domain)
        serializables.append(serializable)
    return serializables


def list_encoder_json(
    encoder: EncoderJSON[DOMAIN]
) -> EncoderJSON[List[DOMAIN]]:
    """Encoder for serializing list of domain types as serializable types"""
    return EncoderJSON(partial(list_encode_json, encoder))


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
        payload_result_json = named_message_decode_json(name, value)
        if isinstance(payload_result_json, Ok):
            result = decoder.json_decode(payload_result_json.value)
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
            return named_message_encode_json(name, encoder.json_encode(value))
    # Not very functional, if this becomes a problem, refactor Encoder result type :/
    raise CodecParseException(f"This encoder can't encode {type(value).__name__}")


def named_message_union_encoder_json(
    encoders: Dict[Type[NAMED_MESSAGE], Tuple[str, EncoderJSON[NAMED_MESSAGE]]],
) -> EncoderJSON[NAMED_MESSAGE]:
    """Create named message union encoder"""
    return EncoderJSON(partial(named_message_union_encode_json, encoders))


# protocol.UploadMessage
def upload_message_encode_json(value: hardware_control_message.UploadMessage) -> JSON:
    """Serialize UploadMessage to JSON"""
    return {
        "softwareId": str(value.software_id.value)
    }


def upload_message_decode_json(value: JSON) -> Result[hardware_control_message.UploadMessage, CodecParseException]:
    """Un-serialize UploadMessage from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("UploadMessage must be an object"))
    firmware_id_result = ManagedUUID.build(value.get("softwareId"))
    if isinstance(firmware_id_result, Err):
        return Err(CodecParseException(f"UploadMessage .firmware_id isn't valid UUID: {firmware_id_result.value.text()}"))
    return Ok(hardware_control_message.UploadMessage(firmware_id_result.value))


UPLOAD_MESSAGE_ENCODER_JSON: EncoderJSON[hardware_control_message.UploadMessage] = EncoderJSON(upload_message_encode_json)
UPLOAD_MESSAGE_DECODER_JSON: DecoderJSON[hardware_control_message.UploadMessage] = DecoderJSON(upload_message_decode_json)
UPLOAD_MESSAGE_CODEC_JSON: CodecJSON[hardware_control_message.UploadMessage] = \
    CodecJSON(UPLOAD_MESSAGE_DECODER_JSON, UPLOAD_MESSAGE_ENCODER_JSON)


# protocol.UploadResultMessage
def upload_result_message_encode_json(value: hardware_control_message.UploadResultMessage) -> JSON:
    """Serialize UploadResultMessage to JSON"""
    return {
        "error": value.error
    }


def upload_result_message_decode_json(value: JSON) -> Result[hardware_control_message.UploadResultMessage, CodecParseException]:
    """Un-serialize UploadResultMessage from JSON"""
    if isinstance(value, dict):
        error = value.get("error")
        if isinstance(error, str) or error is None:
            return Ok(hardware_control_message.UploadResultMessage(error))
        else:
            return Err(CodecParseException("UploadResultMessage must have .error as null or string"))
    else:
        return Err(CodecParseException("UploadResultMessage must be an object"))


UPLOAD_RESULT_MESSAGE_ENCODER_JSON: EncoderJSON[hardware_control_message.UploadResultMessage] = \
    EncoderJSON(upload_result_message_encode_json)
UPLOAD_RESULT_MESSAGE_DECODER_JSON: DecoderJSON[hardware_control_message.UploadResultMessage] = \
    DecoderJSON(upload_result_message_decode_json)
UPLOAD_RESULT_MESSAGE_CODEC_JSON: CodecJSON[hardware_control_message.UploadResultMessage] = \
    CodecJSON(UPLOAD_RESULT_MESSAGE_DECODER_JSON, UPLOAD_RESULT_MESSAGE_ENCODER_JSON)


# protocol.PingMessage
def ping_message_encode_json(_: hardware_shared_message.PingMessage) -> JSON:
    """Serialize PingMessage to JSON"""
    return {}


def ping_message_decode_json(value: JSON) -> Result[hardware_shared_message.PingMessage, CodecParseException]:
    """Un-serialize PingMessage from JSON"""
    if isinstance(value, dict):
        return Ok(hardware_shared_message.PingMessage())
    else:
        return Err(CodecParseException("PingMessage must be an object"))


PING_MESSAGE_ENCODER_JSON: EncoderJSON[hardware_shared_message.PingMessage] = \
    EncoderJSON(ping_message_encode_json)
PING_MESSAGE_DECODER_JSON: DecoderJSON[hardware_shared_message.PingMessage] = \
    DecoderJSON(ping_message_decode_json)
PING_MESSAGE_CODEC_JSON: CodecJSON[hardware_control_message.UploadResultMessage] = \
    CodecJSON(UPLOAD_RESULT_MESSAGE_DECODER_JSON, UPLOAD_RESULT_MESSAGE_ENCODER_JSON)


# protocol.CreateUserMessage
def create_user_message_encode_json(value: backend_management_message.CreateUserMessage) -> JSON:
    """Serialize CreateUserMessage to JSON"""
    return {
        "username": value.username,
        "password": value.password
    }


CREATE_USER_MESSAGE_ENCODER_JSON: EncoderJSON[backend_management_message.CreateUserMessage] = \
    EncoderJSON(create_user_message_encode_json)


# protocol.CreateUserMessage
def create_hardware_message_encode_json(value: backend_management_message.CreateHardwareMessage) -> JSON:
    """Serialize CreateHardwareMessage to JSON"""
    return {
        "name": value.name
    }


CREATE_HARDWARE_MESSAGE_ENCODER_JSON: EncoderJSON[backend_management_message.CreateHardwareMessage] = \
    EncoderJSON(create_hardware_message_encode_json)


# protocol.SuccessMessage
SUCCESS_GENERIC = TypeVar('SUCCESS_GENERIC')


def success_message_decode_json(
    decoder: DecoderJSON[SUCCESS_GENERIC],
    value: JSON
) -> Result[backend_management_message.SuccessMessage[SUCCESS_GENERIC], CodecParseException]:
    """Un-serialize SuccessMessage from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SuccessMessage must be an object"))
    success = value.get("success")
    content_result = decoder.json_decode(success)
    if isinstance(content_result, Err):
        return Err(content_result.value)
    return Ok(backend_management_message.SuccessMessage(content_result.value))


def success_message_decoder_json(
    decoder: DecoderJSON[SUCCESS_GENERIC]
) -> DecoderJSON[backend_management_message.SuccessMessage[SUCCESS_GENERIC]]:
    """Create a success message decoder function instance"""
    return DecoderJSON(partial(success_message_decode_json, decoder))


# protocol.FailureMessage
FAILURE_GENERIC = TypeVar('FAILURE_GENERIC')


def failure_message_decode_json(
    decoder: DecoderJSON[FAILURE_GENERIC],
    value: str
) -> Result[backend_management_message.FailureMessage[FAILURE_GENERIC], CodecParseException]:
    """Un-serialize FailureMessage from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("FailureMessage must be an object"))
    failure = value.get("failure")
    content_result = decoder.json_decode(failure)
    if isinstance(content_result, Err):
        return Err(content_result.value)
    return Ok(backend_management_message.FailureMessage(content_result.value))


def failure_message_decoder_json(
    decoder: DecoderJSON[FAILURE_GENERIC]
) -> DecoderJSON[backend_management_message.FailureMessage[FAILURE_GENERIC]]:
    """Create a failure message decoder function instance"""
    return DecoderJSON(partial(failure_message_decode_json, decoder))


# hardware_shared_message.AuthRequest
def auth_request_encode_json(value: hardware_shared_message.AuthRequest) -> JSON:
    """Serialize AuthRequest to JSON"""
    return {
        "username": value.username,
        "password": value.password
    }


def auth_request_decode_json(
    value: JSON
) -> Result[hardware_shared_message.AuthRequest, CodecParseException]:
    """Un-serialize AuthRequest from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("AuthRequest must be an object"))

    username = value.get("username")
    if not isinstance(username, str):
        return Err(CodecParseException("AuthRequest .username must be string"))

    password = value.get("password")
    if not isinstance(password, str):
        return Err(CodecParseException("AuthRequest .password must be string"))

    return Ok(hardware_shared_message.AuthRequest(username, password))


AUTH_REQUEST_ENCODER_JSON: EncoderJSON[hardware_shared_message.AuthRequest] = \
    EncoderJSON(auth_request_encode_json)
AUTH_REQUEST_DECODER_JSON: DecoderJSON[hardware_shared_message.AuthRequest] = \
    DecoderJSON(auth_request_decode_json)
AUTH_REQUEST_CODEC_JSON: CodecJSON[hardware_shared_message.AuthRequest] = \
    CodecJSON(AUTH_REQUEST_DECODER_JSON, AUTH_REQUEST_ENCODER_JSON)


# hardware_shared_message.AuthResult
def auth_result_encode_json(value: hardware_shared_message.AuthResult) -> JSON:
    """Serialize AuthResult to JSON"""
    return {
        "error": value.error
    }


def auth_result_decode_json(
    value: JSON
) -> Result[hardware_shared_message.AuthResult, CodecParseException]:
    """Un-serialize AuthResult from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("AuthRequest must be an object"))

    error = value.get("error")
    if not isinstance(error, str) and error is not None:
        return Err(CodecParseException("AuthRequest .error must be string or null"))

    return Ok(hardware_shared_message.AuthResult(error))


AUTH_RESULT_ENCODER_JSON: EncoderJSON[hardware_shared_message.AuthResult] = \
    EncoderJSON(auth_result_encode_json)
AUTH_RESULT_DECODER_JSON: DecoderJSON[hardware_shared_message.AuthResult] = \
    DecoderJSON(auth_result_decode_json)
AUTH_RESULT_CODEC_JSON: CodecJSON[hardware_shared_message.AuthResult] = \
    CodecJSON(AUTH_RESULT_DECODER_JSON, AUTH_RESULT_ENCODER_JSON)


# hardware_control_message.SerialMonitorRequest
def serial_monitor_request_encode_json(value: hardware_control_message.SerialMonitorRequest) -> JSON:
    """Serialize SerialMonitorRequest to JSON"""
    return {
        "serialConfig": None if value.config is None else {
            "receiveSize": value.config.receive_size,
            "baudrate": value.config.baudrate,
            "timeout": value.config.timeout
        }
    }


def serial_monitor_request_decode_json(
    value: JSON
) -> Result[hardware_control_message.SerialMonitorRequest, CodecParseException]:
    """Un-serialize UploadMessage from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SerialMonitorRequest must be an object"))

    serial_config = value.get("serialConfig")
    if serial_config is None:
        return Ok(hardware_control_message.SerialMonitorRequest(None))
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

    return Ok(hardware_control_message.SerialMonitorRequest(ManagedSerialConfig(receive_size, baudrate, timeout)))


SERIAL_MONITOR_REQUEST_ENCODER_JSON: EncoderJSON[hardware_control_message.SerialMonitorRequest] = \
    EncoderJSON(serial_monitor_request_encode_json)
SERIAL_MONITOR_REQUEST_DECODER_JSON: DecoderJSON[hardware_control_message.SerialMonitorRequest] = \
    DecoderJSON(serial_monitor_request_decode_json)
SERIAL_MONITOR_REQUEST_CODEC_JSON: CodecJSON[hardware_control_message.SerialMonitorRequest] = \
    CodecJSON(SERIAL_MONITOR_REQUEST_DECODER_JSON, SERIAL_MONITOR_REQUEST_ENCODER_JSON)


# protocol.SerialMonitorRequestStop
def serial_monitor_request_stop_encode_json(_: hardware_control_message.SerialMonitorRequestStop) -> JSON:
    """Serialize SerialMonitorRequestStop to JSON"""
    return {}


def serial_monitor_request_stop_decode_json(
    value: JSON
) -> Result[hardware_control_message.SerialMonitorRequestStop, CodecParseException]:
    """Un-serialize SerialMonitorRequestStop from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SerialMonitorRequestStop must have payload as object"))
    return Ok(hardware_control_message.SerialMonitorRequestStop())


SERIAL_MONITOR_REQUEST_STOP_ENCODER_JSON: EncoderJSON[hardware_control_message.SerialMonitorRequestStop] = \
    EncoderJSON(serial_monitor_request_stop_encode_json)
SERIAL_MONITOR_REQUEST_STOP_DECODER_JSON: DecoderJSON[hardware_control_message.SerialMonitorRequestStop] = \
    DecoderJSON(serial_monitor_request_stop_decode_json)
SERIAL_MONITOR_REQUEST_STOP_CODEC_JSON: CodecJSON[hardware_control_message.SerialMonitorRequestStop] = \
    CodecJSON(SERIAL_MONITOR_REQUEST_STOP_DECODER_JSON, SERIAL_MONITOR_REQUEST_STOP_ENCODER_JSON)


# protocol.SerialMonitorResult
def serial_monitor_result_encode_json(value: hardware_control_message.SerialMonitorResult) -> JSON:
    """Serialize SerialMonitorResult to JSON"""
    return {
        "error": value.error
    }


def serial_monitor_result_decode_json(
    value: JSON
) -> Result[hardware_control_message.SerialMonitorResult, CodecParseException]:
    """Un-serialize SerialMonitorRequest from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("SerialMonitorRequest must be an object"))
    error = value.get("error")
    if not isinstance(error, str) and error is not None:
        return Err(CodecParseException("SerialMonitorRequest must have .error as null or string"))
    return Ok(hardware_control_message.SerialMonitorResult(error))


SERIAL_MONITOR_RESULT_ENCODER_JSON: EncoderJSON[hardware_control_message.SerialMonitorResult] = \
    EncoderJSON(serial_monitor_result_encode_json)
SERIAL_MONITOR_RESULT_DECODER_JSON: DecoderJSON[hardware_control_message.SerialMonitorResult] = \
    DecoderJSON(serial_monitor_result_decode_json)
SERIAL_MONITOR_RESULT_CODEC_JSON: CodecJSON[hardware_control_message.SerialMonitorResult] = \
    CodecJSON(SERIAL_MONITOR_RESULT_DECODER_JSON, SERIAL_MONITOR_RESULT_ENCODER_JSON)


# protocol.MonitorUnavailable
def monitor_unavailable_encode_json(value: monitor_message.MonitorUnavailable) -> JSON:
    """Serialize MonitorUnavailable to JSON"""
    return {
        "reason": value.reason
    }


def monitor_unavailable_decode_json(
    value: JSON
) -> Result[monitor_message.MonitorUnavailable, CodecParseException]:
    """Un-serialize MonitorUnavailable from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("MonitorUnavailable must be an object"))
    reason = value.get("reason")
    if not isinstance(reason, str):
        return Err(CodecParseException("MonitorUnavailable must have .reason as string"))
    return Ok(monitor_message.MonitorUnavailable(reason))


MONITOR_UNAVAILABLE_ENCODER_JSON: EncoderJSON[monitor_message.MonitorUnavailable] = \
    EncoderJSON(monitor_unavailable_encode_json)
MONITOR_UNAVAILABLE_DECODER_JSON: DecoderJSON[monitor_message.MonitorUnavailable] = \
    DecoderJSON(monitor_unavailable_decode_json)
MONITOR_UNAVAILABLE_CODEC_JSON: CodecJSON[monitor_message.MonitorUnavailable] = \
    CodecJSON(MONITOR_UNAVAILABLE_DECODER_JSON, MONITOR_UNAVAILABLE_ENCODER_JSON)

# protocol.CommonIncomingMessage
COMMON_INCOMING_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    hardware_shared_message.AuthResult: ("authResult", AUTH_RESULT_ENCODER_JSON),
    hardware_control_message.UploadMessage: ("uploadSoftwareRequest", UPLOAD_MESSAGE_ENCODER_JSON),
    hardware_control_message.SerialMonitorRequest: ("serialMonitorRequest", SERIAL_MONITOR_REQUEST_ENCODER_JSON),
    hardware_control_message.SerialMonitorRequestStop:
        ("serialMonitorRequestStop", SERIAL_MONITOR_REQUEST_STOP_ENCODER_JSON),
})
COMMON_INCOMING_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    hardware_shared_message.AuthResult: ("authResult", AUTH_RESULT_DECODER_JSON),
    hardware_control_message.UploadMessage: ("uploadSoftwareRequest", UPLOAD_MESSAGE_DECODER_JSON),
    hardware_control_message.SerialMonitorRequest: ("serialMonitorRequest", SERIAL_MONITOR_REQUEST_DECODER_JSON),
    hardware_control_message.SerialMonitorRequestStop:
        ("serialMonitorRequestStop", SERIAL_MONITOR_REQUEST_STOP_DECODER_JSON)
})
COMMON_INCOMING_MESSAGE_CODEC_JSON = CodecJSON(
    COMMON_INCOMING_MESSAGE_DECODER_JSON,
    COMMON_INCOMING_MESSAGE_ENCODER_JSON)

# protocol.CommonOutgoingMessage
COMMON_OUTGOING_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    hardware_shared_message.AuthRequest: ("authRequest", AUTH_REQUEST_ENCODER_JSON),
    hardware_control_message.UploadResultMessage: ("uploadSoftwareResult", UPLOAD_RESULT_MESSAGE_ENCODER_JSON),
    hardware_shared_message.PingMessage: ("ping", PING_MESSAGE_ENCODER_JSON),
    hardware_control_message.SerialMonitorResult: ("serialMonitorResult", SERIAL_MONITOR_RESULT_ENCODER_JSON),
    monitor_message.MonitorUnavailable: ("monitorUnavailable", MONITOR_UNAVAILABLE_ENCODER_JSON)
})
COMMON_OUTGOING_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    hardware_shared_message.AuthRequest: ("authRequest", AUTH_REQUEST_DECODER_JSON),
    hardware_control_message.UploadResultMessage: ("uploadSoftwareResult", UPLOAD_RESULT_MESSAGE_DECODER_JSON),
    hardware_shared_message.PingMessage: ("ping", PING_MESSAGE_DECODER_JSON),
    hardware_control_message.SerialMonitorResult: ("serialMonitorResult", SERIAL_MONITOR_RESULT_DECODER_JSON),
    monitor_message.MonitorUnavailable: ("monitorUnavailable", MONITOR_UNAVAILABLE_DECODER_JSON)
})
COMMON_OUTGOING_MESSAGE_CODEC_JSON = CodecJSON(
    COMMON_OUTGOING_MESSAGE_DECODER_JSON,
    COMMON_OUTGOING_MESSAGE_ENCODER_JSON)


# hardware_video_message.CameraUnavailable
def camera_unavailable_encode_json(value: hardware_video_message.CameraUnavailable) -> JSON:
    """Encode CameraUnavailable into JSON"""
    return {
        "reason": value.reason.text()
    }
CAMERA_UNAVAILABLE_ENCODER_JSON: EncoderJSON[hardware_video_message.CameraUnavailable] = \
    EncoderJSON(camera_unavailable_encode_json)

# hardware_video_message.StopBroadcasting
def stop_broadcasting_decode_json(
    value: JSON
) -> Result[hardware_video_message.StopBroadcasting, CodecParseException]:
    """Un-serialize StopBroadcasting from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("CameraSubscription must be an object"))
    return Ok(hardware_video_message.StopBroadcasting())

STOP_BROADCASTING_MESSAGE_DECODER_JSON: DecoderJSON[hardware_video_message.StopBroadcasting] = \
    DecoderJSON(stop_broadcasting_decode_json)

# hardware_video_message.CameraSubscription
def camera_subscription_decode_json(
    value: JSON
) -> Result[hardware_video_message.CameraSubscription, CodecParseException]:
    """Un-serialize CameraSubscription from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("CameraSubscription must be an object"))
    return Ok(hardware_video_message.CameraSubscription())

CAMERA_SUBSCRIPTION_MESSAGE_DECODER_JSON: DecoderJSON[hardware_video_message.CameraSubscription] = \
    DecoderJSON(camera_subscription_decode_json)

# protocol.CommonIncomingVideoMessage
COMMON_INCOMING_VIDEO_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    hardware_shared_message.AuthResult: ("authResult", AUTH_RESULT_DECODER_JSON),
    hardware_video_message.StopBroadcasting: ("stopBroadcasting", STOP_BROADCASTING_MESSAGE_DECODER_JSON),
    hardware_video_message.CameraSubscription: ("cameraSubscription", CAMERA_SUBSCRIPTION_MESSAGE_DECODER_JSON),
})

# protocol.CommonOutgoingVideoMessage
COMMON_OUTGOING_VIDEO_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    hardware_shared_message.AuthRequest: ("authRequest", AUTH_REQUEST_ENCODER_JSON),
    hardware_shared_message.PingMessage: ("ping", PING_MESSAGE_ENCODER_JSON),
    hardware_video_message.CameraUnavailable: ("cameraUnavailable", CAMERA_UNAVAILABLE_ENCODER_JSON)
})

# protocol.MonitorListenerIncomingMessage
MONITOR_LISTENER_INCOMING_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    hardware_shared_message.AuthResult: ("authResult", AUTH_RESULT_ENCODER_JSON),
    monitor_message.MonitorUnavailable: ("monitorUnavailable", MONITOR_UNAVAILABLE_ENCODER_JSON),
})
MONITOR_LISTENER_INCOMING_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    hardware_shared_message.AuthResult: ("authResult", AUTH_RESULT_DECODER_JSON),
    monitor_message.MonitorUnavailable: ("monitorUnavailable", MONITOR_UNAVAILABLE_DECODER_JSON),
})
MONITOR_LISTENER_INCOMING_MESSAGE_CODEC_JSON = CodecJSON(
    MONITOR_LISTENER_INCOMING_MESSAGE_DECODER_JSON,
    MONITOR_LISTENER_INCOMING_MESSAGE_ENCODER_JSON)

# protocol.MonitorListenerOutgoingMessage
MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER_JSON = named_message_union_encoder_json({
    hardware_shared_message.PingMessage: ("ping", PING_MESSAGE_ENCODER_JSON),
    hardware_shared_message.AuthRequest: ("authRequest", AUTH_REQUEST_ENCODER_JSON)
})
MONITOR_LISTENER_OUTGOING_MESSAGE_DECODER_JSON = named_message_union_decoder_json({
    hardware_shared_message.AuthRequest: ("authRequest", AUTH_REQUEST_DECODER_JSON)
})
MONITOR_LISTENER_OUTGOING_MESSAGE_CODEC_JSON = CodecJSON(
    MONITOR_LISTENER_OUTGOING_MESSAGE_DECODER_JSON,
    MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER_JSON)


# backend_domain.User
def user_encode_json(value: backend_entity.User) -> JSON:
    """Encode User into JSON"""
    return {
        "id": str(value.id.value),
        "username": value.username
    }


def user_decode_json(
    value: JSON,
) -> Result[backend_entity.User, CodecParseException]:
    """Un-serialize User from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("User must be an object"))
    user_id_result = ManagedUUID.build(value.get("id"))
    if isinstance(user_id_result, Err):
        return Err(CodecParseException(f"User id isn't valid UUID: {user_id_result.value}"))
    username = value.get("username")
    if username is None:
        return Err(CodecParseException("User must contain username"))
    return Ok(backend_entity.User(user_id_result.value, username))


USER_ENCODER_JSON: EncoderJSON[backend_entity.User] = EncoderJSON(user_encode_json)
USER_DECODER_JSON: DecoderJSON[backend_entity.User] = DecoderJSON(user_decode_json)
USER_CODEC_JSON = CodecJSON(USER_DECODER_JSON, USER_ENCODER_JSON)


# backend_domain.Hardware
def hardware_encode_json(value: backend_entity.Hardware) -> JSON:
    """Serialize hardware into JSON"""
    return {
        "id": str(value.id.value),
        "name": value.name,
        "ownerId": str(value.owner_id.value)
    }


def hardware_decode_json(
    value: JSON,
) -> Result[backend_entity.Hardware, CodecParseException]:
    """Un-serialize Hardware from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("Hardware must be an object"))
    hardware_id_result = ManagedUUID.build(value.get("id"))
    if isinstance(hardware_id_result, Err):
        return Err(CodecParseException(f"Hardware id isn't valid UUID: {hardware_id_result.value}"))
    name = value.get("name")
    if name is None:
        return Err(CodecParseException("Hardware must contain name"))
    owner_id_result = ManagedUUID.build(value.get("ownerId"))
    if isinstance(owner_id_result, Err):
        return Err(CodecParseException(f"Hardware owner id isn't valid UUID: {owner_id_result.value}"))
    return Ok(backend_entity.Hardware(hardware_id_result.value, name, owner_id_result.value))


HARDWARE_ENCODER_JSON = EncoderJSON(hardware_encode_json)
HARDWARE_DECODER_JSON = DecoderJSON(hardware_decode_json)
HARDWARE_CODEC_JSON = CodecJSON(HARDWARE_DECODER_JSON, HARDWARE_ENCODER_JSON)


# backend_domain.Software
def software_encode_json(value: backend_entity.Software) -> JSON:
    """Serialize software into JSON"""
    return {
        "id": str(value.id.value),
        "name": value.name,
        "ownerId": str(value.owner_id.value)
    }


def software_decode_json(
    value: JSON,
) -> Result[backend_entity.Software, CodecParseException]:
    """Un-serialize Software from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("Software must be an object"))
    software_id_result = ManagedUUID.build(value.get("id"))
    if isinstance(software_id_result, Err):
        return Err(CodecParseException(f"Software id isn't valid UUID: {software_id_result.value}"))
    name = value.get("name")
    if name is None:
        return Err(CodecParseException("Software must contain name"))
    owner_id_result = ManagedUUID.build(value.get("ownerId"))
    if isinstance(owner_id_result, Err):
        return Err(CodecParseException(f"Hardware owner id isn't valid UUID: {owner_id_result.value}"))
    return Ok(backend_entity.Software(software_id_result.value, name, owner_id_result.value))


SOFTWARE_ENCODER_JSON = EncoderJSON(software_encode_json)
SOFTWARE_DECODER_JSON = DecoderJSON(software_decode_json)
SOFTWARE_CODEC_JSON = CodecJSON(SOFTWARE_DECODER_JSON, SOFTWARE_ENCODER_JSON)


# config.Config
def config_encode_json(value: config.Config) -> JSON:
    """Serialize UploadMessage to JSON"""
    # Static URL
    if value.static_url is None: static_url = None
    else:
        static_url_result = value.static_url.text()
        if isinstance(static_url_result, Err): static_url = None
        else: static_url = static_url_result.value
    # Control URL
    if value.control_url is None:
        control_url = None
    else:
        control_url_result = value.control_url.text()
        if isinstance(control_url_result, Err):
            control_url = None
        else:
            control_url = control_url_result.value
    # Auth
    if isinstance(value.auth, UserPassAuthConfig):
        username = value.auth.username
        password_b64 = base64.b64encode(value.auth.password.encode()).decode("utf-8")
    else:
        username = None
        password_b64 = None
    return {
        "staticUrl": static_url,
        "controlUrl": control_url,
        "username": username,
        "passwordBase64": password_b64
    }


CONFIG_ENCODER_JSON: EncoderJSON[config.Config] = EncoderJSON(config_encode_json)


# ConfigService
def config_service_encode_json(value: ConfigService) -> JSON:
    if value.source_file is None:
        source_file = None
    else:
        source_file = value.source_file.value
    return {
        "config": CONFIG_ENCODER_JSON.json_encode(value.config),
        "sourceFile": source_file
    }


CONFIG_SERVICE_ENCODER_JSON: EncoderJSON[ConfigService] = EncoderJSON(config_service_encode_json)


# MinOSSuitePacket
def minos_suite_packet_encode_json(value: MinOSSuitePacket) -> JSON:
    """Serialize MinOSSuitePacket into JSON"""
    chunk = value.parsed_chunk
    if isinstance(chunk, TextChunk):
        payload = chunk.text
    elif isinstance(chunk, DisplayChunk):
        payload = {
            "index": chunk.pixel_index,
            "bits": chunk.fancy_byte.to_binary_bits()
        }
    elif isinstance(chunk, LEDChunk):
        payload = chunk.fancy_byte.to_binary_bits()
    elif isinstance(chunk, SwitchChunk):
        payload = chunk.fancy_byte.to_binary_bits()
    elif isinstance(chunk, IndexedButtonChunk):
        payload = chunk.button_index
    else:
        raise CodecParseException(f"This encoder can't encode {type(value).__name__}")

    return {
        "type": value.parsed_chunk.type_text(),
        "payload": payload,
        "sentAt": value.sent_at,
        "outgoing": value.outgoing
    }


def minos_suite_packet_decode_json(
    value: JSON,
) -> Result[MinOSSuitePacket, CodecParseException]:
    """Un-serialize MinOSSuitePacket from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("MinOSPacket must be an object"))
    outgoing = value.get("outgoing")
    if outgoing is None:
        outgoing = True
    if not isinstance(outgoing, bool):
        return Err(CodecParseException("MinOSPacket outgoing must be a boolean or None"))
    sent_at = value.get("sentAt")
    if not isinstance(sent_at, int):
        return Err(CodecParseException("MinOSPacket sentAt must be an integer"))
    packet_type = value.get("type")
    payload = value.get("payload")
    parsed_chunk: ParsedChunk
    if packet_type == TextChunk.type_text():
        if not isinstance(payload, str):
            return Err(CodecParseException("MinOSPacket text chunk payload must be a string"))
        parsed_chunk = TextChunk(payload)
    elif packet_type == SwitchChunk.type_text():
        if not isinstance(payload, list):
            return Err(CodecParseException("MinOSPacket switch chunk payload must be a boolean array"))
        byte_result = FancyByte.from_bits(payload)
        if isinstance(byte_result, Err):
            return Err(CodecParseException(f"MinOSPacket switch chunk payload parse error: {byte_result.value}"))
        parsed_chunk = SwitchChunk(byte_result.value)
    elif packet_type == IndexedButtonChunk.type_text():
        if not isinstance(payload, int):
            return Err(CodecParseException("MinOSPacket switch chunk payload must be a boolean array"))
        parsed_chunk = IndexedButtonChunk(payload)
    else:
        return Err(CodecParseException(f"MinOSPacket type unknown"))
    return Ok(MinOSSuitePacket(parsed_chunk, sent_at, outgoing))


COMMON_MINOS_SUITE_PACKET_ENCODER_JSON: EncoderJSON[MinOSSuitePacket] = EncoderJSON(minos_suite_packet_encode_json)
COMMON_MINOS_SUITE_PACKET_DECODER_JSON: DecoderJSON[MinOSSuitePacket] = DecoderJSON(minos_suite_packet_decode_json)
COMMON_MINOS_SUITE_PACKET_CODEC_JSON: CodecJSON[MinOSSuitePacket] = CodecJSON(
    COMMON_MINOS_SUITE_PACKET_DECODER_JSON,
    COMMON_MINOS_SUITE_PACKET_ENCODER_JSON)


# MinOSSuite
def minos_suite_encode_json(value: MinOSSuite) -> JSON:
    """Serialize MinOSSuite into JSON"""
    packets = []
    for packet in value.chunks:
        encoded = COMMON_MINOS_SUITE_PACKET_ENCODER_JSON.json_encode(packet)
        packets.append(encoded)
    return {
        "chunks": packets,
        "tresholdTime": value.treshold_time,
        "tresholdChunks": value.treshold_chunks,
        "startTime": value.start_time
    }


def minos_suite_decode_json(
    value: JSON,
) -> Result[MinOSSuite, CodecParseException]:
    """Un-serialize MinOSSuite from JSON"""
    if not isinstance(value, dict):
        return Err(CodecParseException("MinOSSuite must be an object"))
    chunks = value.get("chunks")
    if not isinstance(chunks, list):
        return Err(CodecParseException(f"MinOSSuite packets must be a list"))
    suite_packets_result = list_decode_json(COMMON_MINOS_SUITE_PACKET_DECODER_JSON, chunks)
    if isinstance(suite_packets_result, Err):
        return Err(CodecParseException(f"MinOSSuite packets invalid: {suite_packets_result.value}"))
    treshold_time = value.get("tresholdTime")
    if not isinstance(treshold_time, int):
        return Err(CodecParseException(f"MinOSSuite tresholdTime must be an integer"))
    treshold_chunks = value.get("tresholdChunks")
    if not isinstance(treshold_chunks, int):
        return Err(CodecParseException(f"MinOSSuite tresholdChunks must be an integer"))
    start_time = value.get("startTime")
    if start_time is None:
        start_time = 0
    if not isinstance(start_time, int):
        return Err(CodecParseException("MinOSPacket startTime must be an integer"))
    return Ok(MinOSSuite(suite_packets_result.value, treshold_time, treshold_chunks, start_time))


COMMON_MINOS_SUITE_ENCODER_JSON: EncoderJSON[MinOSSuite] = EncoderJSON(minos_suite_encode_json)
COMMON_MINOS_SUITE_DECODER_JSON: DecoderJSON[MinOSSuite] = DecoderJSON(minos_suite_decode_json)
COMMON_MINOS_SUITE_CODEC_JSON: CodecJSON[MinOSSuite] = CodecJSON(
    COMMON_MINOS_SUITE_DECODER_JSON,
    COMMON_MINOS_SUITE_ENCODER_JSON)
