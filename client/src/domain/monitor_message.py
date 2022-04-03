"""Module containing messages sent in monitor connections"""
from typing import Union, Any, Callable, List
from dataclasses import dataclass
from src.domain.hardware_shared_message import AuthRequest, AuthResult
from src.domain.minos_chunks import Chunk, ParsedChunk
from src.domain.noisy_message import NoisyMessage
from src.util.sh import LOGGER


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


@dataclass(frozen=True)
class StartTUI(MonitorMessage):
    pass


class AddTUISideEffect(MonitorMessage):
    event_handler: Any

    def __init__(self, event_handler: Callable[[Any, Any], None]):
        self.event_handler = event_handler


@dataclass(frozen=True)
class SendParsedChunk(MonitorMessage):
    parsed_chunk: ParsedChunk


@dataclass(frozen=True)
class ButtonPress(MonitorMessage):
    key: str


@dataclass(frozen=True)
class ReceiveChunks(MonitorMessage):
    chunks: List[Chunk]
    garbage: List[bytes]
    leftover: bytes


MONITOR_LISTENER_INCOMING_MESSAGE = Union[AuthResult, MonitorUnavailable, SerialMonitorMessageToClient]
MONITOR_LISTENER_OUTGOING_MESSAGE = Union[AuthRequest, SerialMonitorMessageToAgent]


def log_monitor_message(logger: LOGGER, message: Any):
    if isinstance(message, NoisyMessage):
        logger.debug(f"Monitor message: {message}")
    else:
        logger.info(f"Monitor message: {message}")
