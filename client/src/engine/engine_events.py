"""Module containing events consumed by engines"""
from logging import Logger
from typing import TypeVar, Union, Optional
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.engine.engine_state import EngineState
from src.service.managed_serial import ManagedSerial
from src.service.managed_serial_config import ManagedSerialConfig

PI = TypeVar('PI')
PO = TypeVar('PO')


class NoisyEvent:
    """Marker trait to mark an event as noisy, used for logging"""


class FailureEvent:
    """Marker trait to mark an event as a failure, used for logging"""


@dataclass(frozen=True)
class LifecycleStarted:
    """First message emitted into engines"""
    state: EngineState


@dataclass(frozen=True)
class LifecycleEnded:
    """Last message emitted into engines"""
    reason: Optional[DIPClientError] = None


@dataclass(frozen=True)
class DownloadingBoardSoftware:
    software_id: ManagedUUID


@dataclass(frozen=True)
class BoardSoftwareDownloadFailure(FailureEvent):
    reason: DIPClientError


@dataclass(frozen=True)
class BoardState:
    pass


@dataclass(frozen=True)
class UploadingBoardSoftware:
    file_path: ExistingFilePath
    board_state: BoardState


@dataclass(frozen=True)
class BoardSoftwareDownloadSuccess:
    file_path: ExistingFilePath


@dataclass(frozen=True)
class BoardSoftwareRemovalSuccess:
    pass


@dataclass(frozen=True)
class BoardUploadSuccess:
    pass


@dataclass(frozen=True)
class BoardUploadFailure:
    reason: DIPClientError


@dataclass(frozen=True)
class BoardSoftwareRemovalFailure(FailureEvent):
    reason: str


@dataclass(frozen=True)
class BoardSoftwareUploadFailure(FailureEvent):
    reason: str


@dataclass(frozen=True)
class BoardSoftwareUploadSuccess:
    pass


@dataclass(frozen=True)
class SerialMonitorAboutToStart:
    config: ManagedSerialConfig


@dataclass(frozen=True)
class SerialMonitorAlreadyConfigured:
    pass


@dataclass(frozen=True)
class StartSerialMonitor:
    config: ManagedSerialConfig
    device_path: ExistingFilePath


@dataclass
class SerialMonitorStartSuccess:
    serial: ManagedSerial


@dataclass
class SerialMonitorStartFailure:
    reason: DIPClientError


@dataclass
class ReceivedSerialBytes(NoisyEvent):
    received_bytes: bytes


@dataclass
class SendingBoardBytes(NoisyEvent):
    content_bytes: bytes


@dataclass
class StoppingSerialMonitor:
    reason: Optional[DIPClientError] = None


@dataclass
class StoppedSerialMonitor:
    pass


@dataclass
class MonitorDied:
    pass


COMMON_ENGINE_EVENT = Union[
    LifecycleStarted,
    LifecycleEnded,
    DownloadingBoardSoftware,
    BoardSoftwareDownloadFailure,
    BoardSoftwareDownloadSuccess,
    BoardSoftwareRemovalSuccess,
    BoardSoftwareRemovalFailure,
    BoardSoftwareUploadFailure,
    BoardSoftwareUploadSuccess
]


def log_event(logger: Logger, event: COMMON_ENGINE_EVENT):
    # Log event
    if isinstance(event, NoisyEvent):
        logger.debug(f"Engine event: {event}")
    elif isinstance(event, FailureEvent):
        logger.error(f"Engine event: {event}")
    else:
        logger.info(f"Engine event: {event}")
