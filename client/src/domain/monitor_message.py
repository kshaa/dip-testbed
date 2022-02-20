"""Module containing messages sent in monitor connections"""
import base64
from typing import Union
from dataclasses import dataclass

from src.domain.noisy_message import NoisyMessage


@dataclass(frozen=True)
class MonitorMessage:
    """Marker trait for monitor messages"""
    pass


@dataclass(frozen=True)
class MonitorUnavailable(MonitorMessage):
    """Message regarding hardware monitor unavailability"""
    reason: str


@dataclass(frozen=True)
class SerialMonitorMessageToAgent(MonitorMessage, NoisyMessage):
    """Message from client to hardware serial monitor"""
    content_bytes: bytes


@dataclass(frozen=True)
class SerialMonitorMessageToClient(MonitorMessage, NoisyMessage):
    """Message from hardware serial monitor to client"""
    content_bytes: bytes


MONITOR_LISTENER_INCOMING_MESSAGE = Union[MonitorUnavailable, SerialMonitorMessageToClient]
MONITOR_LISTENER_OUTGOING_MESSAGE = Union[SerialMonitorMessageToAgent]
