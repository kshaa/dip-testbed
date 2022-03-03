"""Module containing events consumed by engines"""
from logging import Logger
from typing import TypeVar, Union, Optional
from dataclasses import dataclass

from src.domain.death import Death
from src.domain.dip_client_error import DIPClientError
from src.domain.failure_event import FailureEvent
from src.domain.hardware_shared_event import LifecycleStarted, LifecycleEnded
from src.domain.noisy_event import NoisyEvent
from src.service.managed_video_stream import ManagedVideoStream, VideoStreamConfig

PI = TypeVar('PI')
PO = TypeVar('PO')


@dataclass(frozen=True)
class StartingVideoStream:
    config: VideoStreamConfig


@dataclass
class StartedStream:
    stream: ManagedVideoStream
    death: Death


@dataclass(frozen=True)
class ReceivedChunk(NoisyEvent):
    """Message containing video stream bytes"""
    chunk: bytes


@dataclass
class EndingStream:
    reason: DIPClientError


@dataclass
class EndedStream:
    pass


COMMON_ENGINE_EVENT = Union[
    LifecycleStarted,
    LifecycleEnded,
    StartingVideoStream,
    StartedStream,
]


def log_event(logger: Logger, event: COMMON_ENGINE_EVENT):
    # Log event
    if isinstance(event, NoisyEvent):
        logger.debug(f"Engine event: {event}")
    elif isinstance(event, FailureEvent):
        logger.error(f"Engine event: {event}")
    else:
        logger.info(f"Engine event: {event}")
