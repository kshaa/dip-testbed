#!/usr/bin/env python

from sh import script_relative_path
from agent_nrf52 import firmware_upload_args, firmware_upload_relative_path
import unittest


class TestNrf52(unittest.TestCase):
    def test_firmware_upload_args(self):
        reality = firmware_upload_args("/home/me/code/nrf/run.hex", "/dev/tty0", 115200)
        upload_script_path = script_relative_path(firmware_upload_relative_path)
        expectations = [
            'bash',
            '-c',
            f'{upload_script_path} -d /dev/tty0 -b 115200 -f /home/me/code/nrf/run.hex']
        self.assertEqual(reality, expectations)


if __name__ == '__main__':
    unittest.main()
