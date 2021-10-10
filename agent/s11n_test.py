#!/usr/bin/env python
"""Module to test all Python-to/from-JSON serializer-specific logic"""

import unittest
from uuid import UUID
from result import Ok, Err
from codec import CodecParseException
import protocol
import s11n


class TestS11n(unittest.TestCase):
    """Test suite for Python-to/from-JSON serializers"""

    def upload_message_codec_scenario(self, codec):
        """Common scenario of (de)serializing an UploadMessage w/ a given codec"""
        # Raw message
        message = protocol.UploadMessage(UUID("96b838b2-282d-11ec-ba20-478e3959b3ad"))
        # Serialization
        real_serialized_message = codec.encode(message)
        expected_serialized_message = '{"firmware_id":"96b838b2-282d-11ec-ba20-478e3959b3ad"}'
        self.assertEqual(real_serialized_message, expected_serialized_message)
        # De-serialization
        unserialized_message = codec.decode(real_serialized_message)
        self.assertTrue(isinstance(unserialized_message, Ok))
        self.assertEqual(message, unserialized_message.value)

    def test_upload_message_codec(self):
        """Test UploadMessage (un)serializer codec"""
        codec = s11n.UPLOAD_MESSAGE_CODEC

        # Test valid message scenario
        self.upload_message_codec_scenario(codec)

        # Test de-serializing invalid data
        bad_unserialization = codec.decode("\"potat\"")
        bad_unserialization_expectation = CodecParseException("UploadMessage must be an object")
        self.assertTrue(isinstance(bad_unserialization, Err))
        self.assertEqual(bad_unserialization.value, bad_unserialization_expectation)

    def test_union_codec(self):
        """Test CommonIncomingMessage (un)serializer union codec using UploadMessage"""
        codec = s11n.COMMON_INCOMING_MESSAGE_CODEC

        # Test valid message scenario
        self.upload_message_codec_scenario(codec)

        # Test de-serializing invalid data
        bad_unserialization = codec.decode("\"potat\"")
        bad_unserialization_expectation = \
            CodecParseException("Failed to decode any message from decoder union")
        self.assertTrue(isinstance(bad_unserialization, Err))
        self.assertEqual(bad_unserialization.value, bad_unserialization_expectation)


if __name__ == '__main__':
    unittest.main()
