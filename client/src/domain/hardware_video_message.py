"""Module containing messages sent between this client and the control server"""
from typing import TypeVar, Union, Optional, Any
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.domain.hardware_shared_message import InternalStartLifecycle, InternalEndLifecycle, PingMessage
from src.domain.noisy_message import NoisyMessage
from src.service.managed_video_stream import ManagedVideoStream
from src.util import log

LOGGER = log.timed_named_logger("video_message")
T = TypeVar('T')


@dataclass(frozen=True)
class HardwareVideoMessage:
    """Marker trait for hardware video messages"""
    pass


@dataclass(frozen=True)
class InternalHardwareVideoMessage(HardwareVideoMessage):
    """Marker trait for internal hardware video messages"""
    pass


@dataclass(frozen=True)
class ExternalHardwareVideoMessage(HardwareVideoMessage):
    """Marker trait for external hardware control messages"""
    pass


@dataclass(frozen=True)
class CameraSubscription(ExternalHardwareVideoMessage):
    """Message regarding stream being actively listened to"""
    pass


@dataclass(frozen=True)
class StreamSpawnSuccess(InternalHardwareVideoMessage):
    """Message regarding spawned stream process"""
    stream: ManagedVideoStream


@dataclass(frozen=True)
class StreamSpawnFailure(InternalHardwareVideoMessage):
    """Message regarding stream process init failure"""
    reason: DIPClientError


@dataclass(frozen=True)
class FinishedEndingStream(InternalHardwareVideoMessage):
    pass


@dataclass(frozen=True)
class CameraChunk(ExternalHardwareVideoMessage, NoisyMessage):
    """Message containing video stream bytes"""
    chunk: bytes


@dataclass(frozen=True)
class CameraUnavailable(ExternalHardwareVideoMessage):
    """Message regarding stream going down i.e. becoming unavailable"""
    reason: DIPClientError


@dataclass(frozen=True)
class StopBroadcasting(ExternalHardwareVideoMessage):
    """Message regarding stream not being actively listened to by anyone"""
    pass


# Messages incoming and outgoing to and from control server
COMMON_INCOMING_VIDEO_MESSAGE = Union[
    CameraSubscription,
    StopBroadcasting]
COMMON_OUTGOING_VIDEO_MESSAGE = Union[CameraChunk, PingMessage, CameraUnavailable]


def log_video_message(logger: LOGGER, message: Any):
    if isinstance(message, NoisyMessage):
        logger.debug(f"Video message: {message}")
    else:
        logger.info(f"Video message: {message}")
