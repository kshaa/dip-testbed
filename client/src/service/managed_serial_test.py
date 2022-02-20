#!/usr/bin/env python
"""Module to test serial utilities"""

import unittest
from src.service.managed_serial_config import ManagedSerialConfig


class TestSerialUtil(unittest.TestCase):
    """Test suite for serial utilities"""

    def test_config_equality_check(self):
        """Check that config equality works at least a little bit"""

        config1 = ManagedSerialConfig(1, 2, 3.0)
        config2 = ManagedSerialConfig(1, 2, 4.0)

        self.assertTrue(config1 == config1)
        self.assertFalse(config1 == config2)


if __name__ == '__main__':
    unittest.main()
