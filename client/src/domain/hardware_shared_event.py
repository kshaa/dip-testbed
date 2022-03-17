"""Module containing events consumed by engines"""
from typing import Optional
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.engine.engine_state import EngineState
from src.service.backend_config import UserPassAuthConfig


@dataclass(frozen=True)
class LifecycleStarted:
    """First message emitted into engines"""
    state: EngineState


@dataclass(frozen=True)
class StartingAuth:
    """First message emitted into engines"""
    auth: UserPassAuthConfig


@dataclass(frozen=True)
class LifecycleEnded:
    """Last message emitted into engines"""
    reason: Optional[DIPClientError] = None


@dataclass(frozen=True)
class AuthSucceeded:
    pass


@dataclass(frozen=True)
class AuthFailed:
    """First message emitted into engines"""
    reason: str

