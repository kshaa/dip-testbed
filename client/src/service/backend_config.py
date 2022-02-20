"""Module for backend management service configuration"""

from typing import Optional
from dataclasses import dataclass
from src.service.managed_url import ManagedURL


@dataclass(frozen=True)
class BackendConfig:
    """Backend management service configuration"""
    control_server: Optional[ManagedURL]
    static_server: Optional[ManagedURL]
    api_version = "v1"
    api_prefix = f"/api/{api_version}"
