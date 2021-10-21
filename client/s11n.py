"""Module containing any JSON-from/to-Python serialization-specific logic"""

import json
import uuid
from typing import Dict, Type, TypeVar, Any, Callable, List
from result import Result, Err, Ok
from codec import Encoder, Decoder, Codec, CodecParseException
import protocol
import backend_domain

NO_WHITESPACE_SEPERATORS = (',', ':')


# Raw JSON
def json_decode(value: str) -> Result[Any, CodecParseException]:
    """Decode json or return Err Result"""
    try:
        return Ok(json.loads(value))
    except Exception as e:
        return Err(CodecParseException(str(e)))


# String
def string_decode(value: str) -> Result[str, CodecParseException]:
    """Un-serialize list from JSON"""
    json_result = json_decode(value)
    if isinstance(json_result, Err):
        return Err(json_result.value)
    result = json_result.value

    if isinstance(result, str):
        return Ok(result)
    else:
        return Err(CodecParseException("Object must be string"))

# List
LIST_GENERIC = TypeVar('LIST_GENERIC')


def list_decode(
        value: str,
        content_decode: Callable[[str], Result[LIST_GENERIC, CodecParseException]]
) -> Result[List[LIST_GENERIC], CodecParseException]:
    """Un-serialize list from JSON"""
    json_result = json_decode(value)
    if isinstance(json_result, Err):
        return Err(json_result.value)
    results = json_result.value

    if isinstance(results, list):
        content_results = []
        for result in results:
            content_result = content_decode(json.dumps(
                result, separators=NO_WHITESPACE_SEPERATORS))
            if isinstance(content_result, Err):
                return content_result
            else:
                content_results.append(content_result.value)
        return Ok(content_results)
    else:
        return Err(CodecParseException("Object must be a list"))


def list_decoder(
        content_decoder: Callable[[Any], Result[LIST_GENERIC, CodecParseException]]
) -> Callable[[str], Result[List[LIST_GENERIC], CodecParseException]]:
    """Create a list decoder function instance"""
    def decode(value: str):
        return list_decode(value, content_decoder)

    return decode


# Command JSON
def named_message_extract(name: str, message: Any) -> Result[Any, CodecParseException]:
    """Extract payload from a named command"""
    if isinstance(message, dict):
        command = message.get("command")
        if not isinstance(command, str):
            return Err(CodecParseException("Message requires string 'command' field"))
        if not command == name:
            return Err(CodecParseException("Unknown message command name"))
        if "payload" not in message:
            return Err(CodecParseException("Message requires 'payload' field"))
        payload = message.get("payload")
        return Ok(payload)
    else:
        return Err(CodecParseException("Message must be an object"))


# UnionEncoder & UnionDecoder
UNION_GENERIC = TypeVar('UNION_GENERIC')


def union_encoder(
        class_encoders: Dict[Type[UNION_GENERIC], Encoder[UNION_GENERIC]]
) -> Encoder[UNION_GENERIC]:
    """Creates one whole Encoder from multiple separate Encoders"""

    def union_encode(value: UNION_GENERIC) -> str:
        for clazz, class_encoder in class_encoders.items():
            if isinstance(value, clazz):
                return class_encoder.transform(value)
        # Not very functional, if this becomes a problem, refactor Encoder result type :/
        raise CodecParseException(f"This encoder can't encode {type(value).__name__}")

    return Encoder(union_encode)


def union_decoder(
        class_decoders: Dict[Type[UNION_GENERIC], Decoder[UNION_GENERIC]]
) -> Decoder[UNION_GENERIC]:
    """Creates one whole Decoder from multiple separate Decoders"""

    def union_decode(value: str) -> Result[UNION_GENERIC, CodecParseException]:
        for _, class_decoder in class_decoders.items():
            result = class_decoder.transform(value)
            if isinstance(result, Ok):
                return Ok(result.value)
        return Err(CodecParseException("Failed to decode any message from decoder union"))

    return Decoder(union_decode)


# protocol.UploadMessage
def upload_message_encode(value: protocol.UploadMessage) -> str:
    """Serialize UploadMessage to JSON"""
    message = {
        "command": "uploadSoftwareRequest",
        "payload": {
            "softwareId": str(value.software_id)
        }
    }
    return json.dumps(message, separators=NO_WHITESPACE_SEPERATORS)


def upload_message_decode(value: str) -> Result[protocol.UploadMessage, CodecParseException]:
    """Un-serialize UploadMessage from JSON"""
    json_result = json_decode(value)
    if isinstance(json_result, Err):
        return Err(json_result.value)
    command_result = named_message_extract("uploadSoftwareRequest", json_result.value)
    if isinstance(command_result, Err):
        return Err(command_result.value)
    result = command_result.value

    if isinstance(result, dict):
        firmware_id = result.get("softwareId")
        if isinstance(firmware_id, str):
            try:
                return Ok(protocol.UploadMessage(uuid.UUID(firmware_id)))
            except Exception as e:
                return Err(CodecParseException(f"UploadMessage .firmware_id isn't valid UUID: {e}"))
        else:
            return Err(CodecParseException("UploadMessage must have .firmware_id string"))
    else:
        return Err(CodecParseException("UploadMessage must be an object"))


UPLOAD_MESSAGE_ENCODER: Encoder[protocol.UploadMessage] = Encoder(upload_message_encode)
UPLOAD_MESSAGE_DECODER: Decoder[protocol.UploadMessage] = Decoder(upload_message_decode)
UPLOAD_MESSAGE_CODEC: Codec[protocol.UploadMessage] = \
    Codec(UPLOAD_MESSAGE_DECODER, UPLOAD_MESSAGE_ENCODER)


# protocol.FailedUploadMessage
def failed_upload_message_encode(value: protocol.FailedUploadMessage) -> str:
    """Serialize FailedUploadMessage to JSON"""
    return json.dumps(
        {"error_message": str(value.error_message)},
        separators=NO_WHITESPACE_SEPERATORS)


def failed_upload_message_decode(
        value: str) -> Result[protocol.FailedUploadMessage, CodecParseException]:
    """Un-serialize FailedUploadMessage from JSON"""
    json_result = json_decode(value)
    if isinstance(json_result, Err):
        return Err(json_result.value)
    result = json_result.value

    if isinstance(result, dict):
        error_message = result.get("error_message")
        if isinstance(error_message, str):
            return Ok(protocol.FailedUploadMessage(error_message))
        else:
            pass
        return Err(CodecParseException("FailedUploadMessage must have .error_message string"))
    else:
        return Err(CodecParseException("FailedUploadMessage must be an object"))


FAILED_UPLOAD_MESSAGE_ENCODER: Encoder[protocol.FailedUploadMessage] = \
    Encoder(failed_upload_message_encode)
FAILED_UPLOAD_MESSAGE_DECODER: Decoder[protocol.FailedUploadMessage] = \
    Decoder(failed_upload_message_decode)
FAILED_UPLOAD_MESSAGE_CODEC: Codec[protocol.FailedUploadMessage] = \
    Codec(FAILED_UPLOAD_MESSAGE_DECODER, FAILED_UPLOAD_MESSAGE_ENCODER)


# protocol.CreateUserMessage
def create_user_message_encode(value: protocol.CreateUserMessage) -> str:
    """Serialize CreateUserMessage to JSON"""
    message = {
        "username": value.username,
        "password": value.password
    }
    return json.dumps(message, separators=NO_WHITESPACE_SEPERATORS)


CREATE_USER_MESSAGE_ENCODER: Encoder[protocol.CreateUserMessage] = \
    Encoder(create_user_message_encode)


# protocol.SuccessMessage
SUCCESS_GENERIC = TypeVar('SUCCESS_GENERIC')


def success_message_decode(
        value: str,
        content_decoder: Callable[[str], Result[SUCCESS_GENERIC, CodecParseException]]
) -> Result[protocol.SuccessMessage[SUCCESS_GENERIC], CodecParseException]:
    """Un-serialize SuccessMessage from JSON"""
    json_result = json_decode(value)
    if isinstance(json_result, Err):
        return Err(json_result.value)
    result = json_result.value

    if isinstance(result, dict):
        success = result.get("success")
        content_result = content_decoder(json.dumps(
            success, separators=NO_WHITESPACE_SEPERATORS))
        if isinstance(content_result, Err):
            return Err(json_result.value)
        else:
            return Ok(protocol.SuccessMessage(content_result.value))
    else:
        return Err(CodecParseException("SuccessMessage must be an object"))


def success_message_decoder(
        content_decoder: Callable[[str], Result[SUCCESS_GENERIC, CodecParseException]]
) -> Callable[[str], Result[protocol.SuccessMessage[SUCCESS_GENERIC], CodecParseException]]:
    """Create a success message decoder function instance"""
    def decode(value: str):
        return success_message_decode(value, content_decoder)
    return decode


# protocol.FailureMessage
FAILURE_GENERIC = TypeVar('FAILURE_GENERIC')


def failure_message_decode(
        value: str,
        content_decoder: Callable[[str], Result[FAILURE_GENERIC, CodecParseException]]
) -> Result[protocol.FailureMessage[FAILURE_GENERIC], CodecParseException]:
    """Un-serialize FailureMessage from JSON"""
    json_result = json_decode(value)
    if isinstance(json_result, Err):
        return Err(json_result.value)
    result = json_result.value

    if isinstance(result, dict):
        failure = result.get("failure")
        content_result = content_decoder(json.dumps(
            failure, separators=NO_WHITESPACE_SEPERATORS))
        if isinstance(content_result, Err):
            return Err(content_result.value)
        else:
            return Ok(protocol.FailureMessage(content_result.value))
    else:
        return Err(CodecParseException("FailureMessage must be an object"))


def failure_message_decoder(
        content_decoder: Callable[[str], Result[FAILURE_GENERIC, CodecParseException]]
) -> Callable[[str], Result[protocol.FailureMessage[FAILURE_GENERIC], CodecParseException]]:
    """Create a failure message decoder function instance"""
    def decode(value: str) -> Result[protocol.FailureMessage[FAILURE_GENERIC], CodecParseException]:
        return failure_message_decode(value, content_decoder)
    return decode


# protocol.CommonIncomingMessage
COMMON_INCOMING_MESSAGE_ENCODER = union_encoder({
    protocol.UploadMessage: UPLOAD_MESSAGE_ENCODER
})
COMMON_INCOMING_MESSAGE_DECODER = union_decoder({
    protocol.UploadMessage: UPLOAD_MESSAGE_DECODER
})
COMMON_INCOMING_MESSAGE_CODEC = Codec(
    COMMON_INCOMING_MESSAGE_DECODER,
    COMMON_INCOMING_MESSAGE_ENCODER)

# protocol.CommonOutgoingMessage
COMMON_OUTGOING_MESSAGE_ENCODER = union_encoder({
    protocol.FailedUploadMessage: FAILED_UPLOAD_MESSAGE_ENCODER
})
COMMON_OUTGOING_MESSAGE_DECODER = union_decoder({
    protocol.FailedUploadMessage: FAILED_UPLOAD_MESSAGE_DECODER
})
COMMON_OUTGOING_MESSAGE_CODEC = Codec(
    COMMON_OUTGOING_MESSAGE_DECODER,
    COMMON_OUTGOING_MESSAGE_ENCODER)


# backend_domain.User
def user_decode(
    value: str,
) -> Result[backend_domain.User, CodecParseException]:
    """Un-serialize FailureMessage from JSON"""
    json_result = json_decode(value)
    if isinstance(json_result, Err):
        return Err(json_result.value)
    result = json_result.value

    if isinstance(result, dict):
        user_id = result.get("id")
        username = result.get("username")

        if user_id is None:
            return Err(CodecParseException("User must contain id"))
        if username is None:
            return Err(CodecParseException("User must contain username"))

        return Ok(backend_domain.User(user_id, username))
    else:
        return Err(CodecParseException("User must be an object"))
