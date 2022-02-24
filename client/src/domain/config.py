import dataclasses
from typing import Optional
from dataclasses import dataclass
from src.service.backend_config import AuthConfig
from src.service.managed_url import ManagedURL


@dataclass
class Config:
    static_url: Optional[ManagedURL] = None
    control_url: Optional[ManagedURL] = None
    auth: Optional[AuthConfig] = None

    def with_static_url(self, value: Optional[ManagedURL]):
        return dataclasses.replace(self, static_url=value)

    def with_control_url(self, value: Optional[ManagedURL]):
        return dataclasses.replace(self, control_url=value)

    def with_auth(self, value: Optional[AuthConfig]):
        return dataclasses.replace(self, auth=value)
