#!/usr/bin/env python
"""Test NRF52 client functionality"""

import unittest
from sh import root_relative_path
from agent_nrf52 import firmware_upload_args, FIRMWARE_UPLOAD_PATH


class TestNrf52(unittest.TestCase):
    """NRF52 client test suite"""

    def test_firmware_upload_args(self):
        """Test whether upload arguments are constructed properly"""
        reality = firmware_upload_args("/home/me/code/nrf/run.hex", "/dev/tty0", 115200)
        upload_script_path = root_relative_path(FIRMWARE_UPLOAD_PATH)
        expectations = [
            'bash',
            '-c',
            f'{upload_script_path} -d /dev/tty0 -b 115200 -f /home/me/code/nrf/run.hex']
        self.assertEqual(reality, expectations)


if __name__ == '__main__':
    unittest.main()
