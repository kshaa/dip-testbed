#!/usr/bin/env python
"""Module to test hybrid serializer logic"""

import unittest
from uuid import UUID
from result import Ok, Err
from src.protocol import s11n_hybrid
from src.protocol.codec import CodecParseException
from src.domain import hardware_control_message


class TestS11nHybrid(unittest.TestCase):
    """Test suite for hybrid serializers"""

    def test_upload_message_codec(self):
        """Test UploadMessage (un)serializer codec"""
        codec = s11n_hybrid.COMMON_INCOMING_MESSAGE_CODEC

        # Test valid JSON message
        message = hardware_control_message.UploadMessage(UUID("96b838b2-282d-11ec-ba20-478e3959b3ad"))
        real_serialized_message = codec.encoder.encode(message)
        expected_serialized_message = "{\"command\":\"uploadSoftwareRequest\",\"payload\":{\"softwareId\":\"96b838b2-282d-11ec-ba20-478e3959b3ad\"}}"
        self.assertEqual(real_serialized_message, expected_serialized_message)
        unserialized_message = codec.decoder.decode(real_serialized_message)
        self.assertTrue(isinstance(unserialized_message, Ok))
        self.assertEqual(message, unserialized_message.value)

        # Test invalid JSON message
        bad_unserialization = codec.decoder.decode("\"potat\"")
        bad_unserialization_expectation = CodecParseException("Failed to decode any named message from decoder union")
        self.assertTrue(isinstance(bad_unserialization, Err))
        self.assertEqual(bad_unserialization.value, bad_unserialization_expectation)

        # Test valid binary message
        binary_message = hardware_control_message.SerialMonitorMessageToAgent(b'potato')
        encoded_binary_message = codec.encoder.encode(binary_message)
        decoded_binary_message = codec.decoder.decode(encoded_binary_message)
        self.assertTrue(isinstance(decoded_binary_message, Ok))
        self.assertEqual(binary_message, decoded_binary_message.value)

if __name__ == '__main__':
    unittest.main()
