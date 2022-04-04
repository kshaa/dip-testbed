from dataclasses import dataclass
from typing import Any, Callable

from src.domain.dip_client_error import DIPClientError
from src.domain.fancy_byte import FancyByte
from src.domain.minos_chunks import Chunk, ParsedChunk
from src.domain.noisy_event import NoisyEvent
from src.util.sh import LOGGER


class MinOSMonitorEvent:
    """Marker trait for MinOS monitor events"""
    pass


@dataclass(frozen=True)
class StartingTUI(MinOSMonitorEvent):
    pass


class AddingTUISideEffect(MinOSMonitorEvent):
    event_handler: Any

    def __init__(self, event_handler: Callable[[Any, Any], None]):
        self.event_handler = event_handler


@dataclass(frozen=True)
class IndexButtonClicked(MinOSMonitorEvent):
    button_index: int


@dataclass(frozen=True)
class MinOSSuiteTimedOut(MinOSMonitorEvent):
    pass


@dataclass(frozen=True)
class SwitchesChanged(MinOSMonitorEvent):
    fancy_byte: FancyByte


@dataclass(frozen=True)
class ReceivedChunkBytes(MinOSMonitorEvent):
    old_stream: bytes
    incoming: bytes


@dataclass(frozen=True)
class LeftoverChanged(MinOSMonitorEvent):
    leftover: bytes


@dataclass(frozen=True)
class BadChunkReceived(MinOSMonitorEvent):
    bad_chunk: Chunk
    error: DIPClientError


@dataclass(frozen=True)
class GoodChunkReceived(MinOSMonitorEvent):
    parsed_chunk: ParsedChunk


@dataclass(frozen=True)
class SendingParsedChunk(MinOSMonitorEvent):
    parsed_chunk: ParsedChunk


@dataclass(frozen=True)
class ModeSwitched(MinOSMonitorEvent):
    is_text_mode: bool


@dataclass(frozen=True)
class TextToAgent(MinOSMonitorEvent):
    text: str


@dataclass(frozen=True)
class TextChanged(MinOSMonitorEvent):
    text: str


def log_monitor_event(logger: LOGGER, message: Any):
    if isinstance(message, NoisyEvent):
        logger.debug(f"Monitor event: {message}")
    else:
        logger.info(f"Monitor event: {message}")
