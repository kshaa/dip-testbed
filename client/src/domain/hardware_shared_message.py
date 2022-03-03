"""Module containing messages sent between this client and the control server"""

from typing import Optional
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.domain.noisy_message import NoisyMessage


@dataclass(frozen=True)
class InternalStartLifecycle():
    pass


@dataclass(frozen=True)
class InternalEndLifecycle():
    reason: Optional[DIPClientError] = None


@dataclass(frozen=True)
class PingMessage(NoisyMessage):
    """Message for sending heartbeats to server"""
    pass
