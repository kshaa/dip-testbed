"""Module containing any JSON-from/to-Python serialization-specific logic"""

import json
from codec import Encoder, Decoder, Codec
from fp import Either
import protocol


# protocol.UploadMessage
def upload_message_encode(value: protocol.UploadMessage) -> str:
    """Serialize UploadMessage to JSON"""
    return json.dumps({"firmware_id": str(value.firmware_id)}, cls=Encoder)


def upload_message_decode(value: str) -> Either[Exception, protocol.UploadMessage]:
    """Un-serialize UploadMessage from JSON"""
    try:
        return Either.as_right(json.loads(value))
    except Exception as e:
        return Either.as_left(e)


UPLOAD_MESSAGE_ENCODER: Encoder[protocol.UploadMessage] = Encoder(upload_message_encode)
UPLOAD_MESSAGE_DECODER: Decoder[protocol.UploadMessage] = Decoder(upload_message_decode)
UPLOAD_MESSAGE_CODEC: Codec[protocol.UploadMessage] = \
    Codec(UPLOAD_MESSAGE_DECODER, UPLOAD_MESSAGE_ENCODER)

# def object_decoder(obj):
#     if '__type__' in obj and obj['__type__'] == 'User':
#         return User(obj['name'], obj['username'])
#     return obj
#
#
# json.loads('{"__type__": "User", "name": "John Smith", "username": "jsmith"}',
#            object_hook=object_decoder)
