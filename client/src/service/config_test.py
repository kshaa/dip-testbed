import dataclasses
import os
import unittest
from src.domain.config import Config
from src.domain.existing_file_path import ExistingFilePath
from src.protocol.s11n_json import CONFIG_ENCODER_JSON
from src.service.config_service import ConfigService
from src.service.managed_url import ManagedURL
from src.util.sh import src_relative_path


class TestConfigService(unittest.TestCase):
    def test_config_service(self):
        test_config_path = src_relative_path("static/test/config.yaml")

        # Clean-up old test
        if ExistingFilePath.exists(test_config_path):
            os.remove(test_config_path)

        # Create test config from empty file
        open(test_config_path, 'w').close()
        test_config_file = ExistingFilePath(test_config_path)
        config_service = ConfigService.from_file(CONFIG_ENCODER_JSON, test_config_file).value
        self.assertEqual(config_service, ConfigService(Config(
            None,
            None,
            None
        ), CONFIG_ENCODER_JSON, test_config_file))

        # Modify config
        static_url = ManagedURL.build("http://localhost:9000").value
        changed_config_reality = config_service.with_config(
            config_service.config.with_static_url(static_url))
        changed_config_expectation = \
            ConfigService(Config(static_url, None, None), CONFIG_ENCODER_JSON, test_config_file, True)
        self.assertEqual(changed_config_expectation, changed_config_reality)

        # Save config
        error = changed_config_reality.to_file()
        self.assertEqual(error, None)
        with open(test_config_path, 'r') as file:
            config_data = file.read()
        config_expectations = \
            "controlUrl: null\n" + \
            "passwordBase64: null\n" + \
            "staticUrl: http://localhost:9000\n" + \
            "username: null\n"
        self.assertEqual(config_data, config_expectations)

        # Re-load config
        reloaded_config_service = ConfigService.from_file(CONFIG_ENCODER_JSON, test_config_file).value
        changed_config_expectation.changed = False
        self.assertEqual(reloaded_config_service, changed_config_expectation)

        # Flush test data
        if ExistingFilePath.exists(test_config_path):
            os.remove(test_config_path)


if __name__ == '__main__':
    unittest.main()
