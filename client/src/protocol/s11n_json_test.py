#!/usr/bin/env python
"""Module to test all Python-to/from-JSON serializer-specific logic"""

import unittest
from uuid import UUID
from result import Ok, Err

from src.domain.managed_uuid import ManagedUUID
from src.domain.minos_chunks import TextChunk
from src.engine.monitor.minos.minos_suite import MinOSSuite, MinOSSuitePacket
from src.protocol import s11n_json
from src.protocol.codec import CodecParseException
from src.domain import hardware_control_message


class TestS11nJSON(unittest.TestCase):
    """Test suite for Python-to/from-JSON serializers"""

    def test_upload_message_json_codec(self):
        """Test UploadMessage (un)serializer codec"""
        codec = s11n_json.UPLOAD_MESSAGE_CODEC_JSON

        # Test valid message scenario
        message = hardware_control_message.UploadMessage(ManagedUUID(UUID("96b838b2-282d-11ec-ba20-478e3959b3ad")))

        real_serialized_message = codec.encoder.json_encode(message)
        expected_serialized_message = {
            "softwareId": "96b838b2-282d-11ec-ba20-478e3959b3ad"
         }
        self.assertEqual(real_serialized_message, expected_serialized_message)

        unserialized_message = codec.decoder.json_decode(real_serialized_message)
        self.assertTrue(isinstance(unserialized_message, Ok))
        self.assertEqual(message, unserialized_message.value)

        # Test de-serializing invalid data
        bad_unserialization = codec.decoder.json_decode("\"potat\"")
        bad_unserialization_expectation = CodecParseException("UploadMessage must be an object")
        self.assertTrue(isinstance(bad_unserialization, Err))
        self.assertEqual(bad_unserialization.value, bad_unserialization_expectation)

    def test_common_incoming_message_json_union_codec(self):
        """Test CommonIncomingMessage (un)serializer union codec using UploadMessage"""
        codec = s11n_json.COMMON_INCOMING_MESSAGE_CODEC_JSON

        # Test valid message scenario
        message = hardware_control_message.UploadMessage(ManagedUUID(UUID("96b838b2-282d-11ec-ba20-478e3959b3ad")))

        real_serialized_message = codec.encoder.json_encode(message)
        expected_serialized_message = {
            "command": "uploadSoftwareRequest",
            "payload": {
                "softwareId": "96b838b2-282d-11ec-ba20-478e3959b3ad"
            }
        }
        self.assertEqual(real_serialized_message, expected_serialized_message)

        unserialized_message = codec.decoder.json_decode(real_serialized_message)
        self.assertTrue(isinstance(unserialized_message, Ok))
        self.assertEqual(message, unserialized_message.value)

        # Test de-serializing invalid data
        bad_unserialization = codec.decoder.json_decode("\"potat\"")
        bad_unserialization_expectation = \
            CodecParseException("Failed to decode any named message from decoder union")
        self.assertTrue(isinstance(bad_unserialization, Err))
        self.assertEqual(bad_unserialization.value, bad_unserialization_expectation)

    def test_minos_suite_codec(self):
        codec = s11n_json.COMMON_MINOS_SUITE_CODEC_JSON
        input = MinOSSuite([
            MinOSSuitePacket(
                TextChunk("potat"),
                1000,
                True
            ),
            MinOSSuitePacket(
                TextChunk("potat2"),
                1001,
                False
            )
        ], 5000, 1)

        serialized_json = codec.encoder.json_encode(input)
        expected_json = {
            "chunks": [
                {
                    "type": "text",
                    "payload": "potat",
                    "sentAt": 1000,
                    "outgoing": True,
                },
                {
                    "type": "text",
                    "payload": "potat2",
                    "sentAt": 1001,
                    "outgoing": False
                },
            ],
            "tresholdChunks": 1,
            "tresholdTime": 5000
        }
        self.assertEqual(serialized_json, expected_json)

        output = codec.decoder.json_decode(serialized_json)
        self.assertEqual(Ok(input), output)


if __name__ == '__main__':
    unittest.main()
