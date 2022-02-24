import base64
import dataclasses
from typing import Optional
from dataclasses import dataclass
import yaml
from result import Result, Ok, Err
from src.domain.config import Config
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.protocol.codec_json import EncoderJSON
from src.service.backend_config import UserPassAuthConfig
from src.service.managed_url import ManagedURL


@dataclass
class ConfigError(DIPClientError):
    title: str
    reason: Optional[str] = None
    exception: Optional[Exception] = None
    error: Optional[DIPClientError] = None

    def text(self):
        clarification = f", reason: {self.error.text()}" if self.error is not None \
            else f", reason: {str(self.reason)}" if self.reason is not None \
            else f", reason: {str(self.exception)}" if self.exception is not None \
            else ""
        return f"Configuration error '{self.title}'{clarification}"


@dataclass
class ConfigServiceInterface:
    config: Config


@dataclass
class ConfigService(ConfigServiceInterface):
    config: Config
    config_encoder: EncoderJSON[Config]
    source_file: Optional[ExistingFilePath] = None
    changed: bool = False

    @staticmethod
    def from_file(config_encoder: EncoderJSON[Config], config_path: ExistingFilePath) -> Result['ConfigService', DIPClientError]:
        # Read YAML
        try:
            stream = open(config_path.value, 'r')
            stored = yaml.load(stream, Loader=yaml.FullLoader)
            stream.close()
        except Exception as e:
            return Err(ConfigError("Failed to load YAML from config", exception=e))
        # Handle empty YAML
        if stored is None:
            return Ok(ConfigService(Config(), config_encoder, config_path))
        # Handle bad YAML structure
        if not isinstance(stored, dict):
            return Err(ConfigError("Config contents are not empty and not a dictionary"))
        # Parameter: Static URL
        static_url = stored.get("staticUrl")
        if static_url is None:
            static_url_result = Ok(None)
        else:
            if not isinstance(static_url, str):
                return Err(ConfigError("Static URL not a string"))
            static_url_result = ManagedURL.build(static_url)
            if isinstance(static_url_result, Err):
                return Err(static_url_result.value.of_type("staticUrl"))
        # Parameter: Control URL
        control_url = stored.get("controlUrl")
        if control_url is None:
            control_url_result = Ok(None)
        else:
            if not isinstance(control_url, str):
                return Err(ConfigError("Control URL not a string"))
            control_url_result = ManagedURL.build(control_url)
            if isinstance(control_url_result, Err):
                return Err(control_url_result.value.of_type("controlUrl"))
        # Auth
        username = stored.get("username")
        password_b64 = stored.get("passwordBase64")
        password = base64.b64decode(password_b64).decode("utf-8") if password_b64 is not None else None
        if username is None and password is None:
            auth = None
        elif username is not None and password is not None:
            auth = UserPassAuthConfig(username, password)
        else:
            return Err(ConfigError("Username and password must both be empty or both defined"))

        # Built config service
        return Ok(ConfigService(Config(
            static_url_result.value,
            control_url_result.value,
            auth
        ), config_encoder, config_path))

    def to_file(self, config_path: Optional[ExistingFilePath] = None) -> Optional[ConfigError]:
        if self.source_file is not None:
            path = self.source_file
        elif config_path is not None:
            path = config_path
        else:
            return ConfigError("No save file provided")

        try:
            stream = open(path.value, 'w')
            json_config = self.config_encoder.json_encode(self.config)
            yaml.dump(json_config, stream)
            stream.close()
            self.changed = False
            return None
        except Exception as e:
            return ConfigError("Failed to write YAML to config", exception=e)

    def with_config(self, new_config: 'Config'):
        if self.config != new_config:
            self.changed = True
        return dataclasses.replace(self, config=new_config)