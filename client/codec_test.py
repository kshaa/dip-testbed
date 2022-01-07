#!/usr/bin/env python
"""Module to test JSON codec logic"""

import unittest
from codec_json import DecoderJSON, EncoderJSON
from result import Ok


class TestCodec(unittest.TestCase):
    """Test suite for JSON codec base"""

    def test_json_codec(self):
        """Test JSON can be parsed and serialized"""
        text = "{\"key\":\"value\"}"
        data = {"key": "value"}

        as_json = DecoderJSON.raw_as_serializable(text)
        as_str = EncoderJSON.serializable_as_raw(data)

        self.assertEqual(text, as_str)
        self.assertEqual(Ok(data), as_json)


if __name__ == '__main__':
    unittest.main()
