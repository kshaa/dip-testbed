#!/usr/bin/env python
"""Module to test all Python-to/from-JSON serializer-specific logic"""

import unittest
from uuid import UUID
import protocol
import s11n


class TestS11n(unittest.TestCase):
    """Test suite for Python-to/from-JSON serializers"""

    def test_upload_message_codec(self):
        """Test UploadMessage (un)serializer codec"""
        codec = s11n.UPLOAD_MESSAGE_CODEC
        message = protocol.UploadMessage(UUID("96b838b2-282d-11ec-ba20-478e3959b3ad"))
        real_serialized_message = codec.encode(message)
        expected_serialized_message = "{}"
        self.assertEqual(real_serialized_message, expected_serialized_message)


if __name__ == '__main__':
    unittest.main()
