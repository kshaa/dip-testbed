#!/usr/bin/env python
"""Test command line interface definition for agent"""

import unittest
from uuid import UUID

from result import Ok

from src.domain.existing_file_path import ExistingFilePath
from src.service.cli import CLI
from src.service.managed_url import ManagedURL
from src.util.sh import src_relative_path


class TestCLI(unittest.TestCase):
    """CLI test suite"""

    test_hardware_id = UUID("967502c6-8c10-11ec-8985-2b117ff533fc")
    test_control_server = ManagedURL.build("ws://localhost:9000/base/path").value.text().value
    test_static_server = ManagedURL.build("http://localhost:9000/base/path").value.text().value
    test_heartbeat_seconds = 30
    test_device_path = ExistingFilePath(src_relative_path("static/test/device")).value
    def test_good_common_agent_params(self):
        """Test whether upload arguments are constructed properly"""

        result = CLI.parsed_agent_input(
            str(self.test_hardware_id),
            self.test_control_server,
            self.test_static_server,
            self.test_heartbeat_seconds,
            self.test_device_path
        )
        self.assertTrue(isinstance(result, Ok), result.value)

        [hwid, csrv, ssrv, hs, dp] = result.value
        self.assertTrue(hwid, self.test_hardware_id)
        self.assertTrue(csrv, self.test_control_server)
        self.assertTrue(ssrv, self.test_static_server)
        self.assertTrue(hs, self.test_heartbeat_seconds)
        self.assertTrue(dp, self.test_device_path)


if __name__ == '__main__':
    unittest.main()
