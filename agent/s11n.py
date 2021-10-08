import json
from codec import Encoder, Decoder, Codec
import protocol

# # protocol.UploadMessage
# def uploadMessageEncode(value: protocol.UploadMessage) -> str:
#
#
# uploadMessageEncoder: Encoder[protocol.UploadMessage] = Encoder(uploadMessageEncode)
# uploadMessageDecoder: Decoder[protocol.UploadMessage] = Decoder(lambda x: Either.as_right(x))
# uploadMessageCodec: Codec[protocol.UploadMessage] = Codec(identityDecoder, identityEncoder)
#
#
# def object_decoder(obj):
#     if '__type__' in obj and obj['__type__'] == 'User':
#         return User(obj['name'], obj['username'])
#     return obj
#
#
# json.loads('{"__type__": "User", "name": "John Smith", "username": "jsmith"}',
#            object_hook=object_decoder)
