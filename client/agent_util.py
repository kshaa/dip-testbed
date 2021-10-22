"""Module for common functionality between agents"""

from dataclasses import dataclass
from uuid import UUID
from backend_util import BackendConfig


# Generic client config
@dataclass(frozen=True, eq=False)
class AgentConfig:
    """Common i.e. microcontroller-non-specific client configuration options"""
    hardware_id: UUID
    backend: BackendConfig
    heartbeat_seconds: int
