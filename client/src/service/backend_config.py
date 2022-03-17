"""Module for backend management service configuration"""
import base64
from typing import Optional, Dict
from dataclasses import dataclass
from src.service.managed_url import ManagedURL


@dataclass
class AuthConfig:
    def auth_headers(self) -> Dict:
        pass


@dataclass
class UserPassAuthConfig(AuthConfig):
    username: str
    password: str

    def __str__(self):
        return f"UserPassAuthConfig(...)"

    def __repr__(self):
        return self.__str__()

    def auth_headers(self) -> Dict:
        """Create authentication header"""
        token = base64.b64encode(f"{self.username}:{self.password}".encode()).decode("utf-8")
        return {
            "Authorization": f"Basic {token}"
        }


@dataclass(frozen=True)
class BackendConfig:
    """Backend management service configuration"""
    control_server: Optional[ManagedURL]
    static_server: Optional[ManagedURL]
    auth: Optional[AuthConfig]
    api_version = "v1"
    api_prefix = f"/api/{api_version}"
