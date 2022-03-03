"""Module containing events consumed by engines"""
from typing import Optional
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.engine.engine_state import EngineState


@dataclass(frozen=True)
class LifecycleStarted:
    """First message emitted into engines"""
    state: EngineState


@dataclass(frozen=True)
class LifecycleEnded:
    """Last message emitted into engines"""
    reason: Optional[DIPClientError] = None

