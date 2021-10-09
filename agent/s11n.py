"""Module containing any JSON-from/to-Python serialization-specific logic"""

import json
from typing import Callable, Dict
from result import Result, Err, Ok
from codec import Encoder, Decoder, Codec
import protocol

NO_WHITESPACE_SEPERATORS = (',', ':')


# protocol.UploadMessage
def upload_message_encode(value: protocol.UploadMessage) -> str:
    """Serialize UploadMessage to JSON"""
    return json.dumps({"firmware_id": str(value.firmware_id)}, separators=NO_WHITESPACE_SEPERATORS)


def upload_message_decode(value: str) -> Result[protocol.UploadMessage, Exception]:
    """Un-serialize UploadMessage from JSON"""
    decoder: Callable[[Dict], protocol.UploadMessage] = \
        lambda x:  protocol.UploadMessage(x['firmware_id'])
    try:
        return Ok(json.loads(value, object_hook=decoder))
    except Exception as e:
        return Err(e)


UPLOAD_MESSAGE_ENCODER: Encoder[protocol.UploadMessage] = Encoder(upload_message_encode)
UPLOAD_MESSAGE_DECODER: Decoder[protocol.UploadMessage] = Decoder(upload_message_decode)
UPLOAD_MESSAGE_CODEC: Codec[protocol.UploadMessage] = \
    Codec(UPLOAD_MESSAGE_DECODER, UPLOAD_MESSAGE_ENCODER)
