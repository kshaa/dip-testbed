#!/usr/bin/env python
"""Test Anvyl client functionality"""

import unittest
from sh import root_relative_path
from agent_anvyl import firmware_upload_args, FIRMWARE_UPLOAD_PATH


class TestAnvyl(unittest.TestCase):
    """Anvyl client test suite"""

    def test_firmware_upload_args(self):
        """Test whether upload arguments are constructed properly"""
        reality = firmware_upload_args("/home/me/code/anvyl/run.hex", "Anvyl", 0)
        upload_script_path = root_relative_path(FIRMWARE_UPLOAD_PATH)
        expectations = [
            'bash',
            '-c',
            f'{upload_script_path} -d "Anvyl" -s "0" -f "/home/me/code/anvyl/run.hex"']
        self.assertEqual(reality, expectations)


if __name__ == '__main__':
    unittest.main()
