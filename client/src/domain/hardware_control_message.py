"""Module containing messages sent between this client and the control server"""

from typing import TypeVar, Generic, Union, Optional, Any
from uuid import UUID
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.domain.hardware_shared_message import InternalStartLifecycle, InternalEndLifecycle, PingMessage, AuthRequest, \
    AuthResult
from src.domain.managed_uuid import ManagedUUID
from src.domain.monitor_message import SerialMonitorMessageToAgent, SerialMonitorMessageToClient
from src.domain.noisy_message import NoisyMessage
from src.service.managed_serial import ManagedSerial
from src.service.managed_serial_config import ManagedSerialConfig
from src.util import log

LOGGER = log.timed_named_logger("hardware_message")
T = TypeVar('T')


@dataclass(frozen=True)
class HardwareControlMessage:
    """Marker trait for hardware control messages"""
    pass


@dataclass(frozen=True)
class InternalHardwareControlMessage(HardwareControlMessage):
    """Marker trait for internal hardware control messages"""
    pass


@dataclass(frozen=True)
class ExternalHardwareControlMessage(HardwareControlMessage):
    """Marker trait for external hardware control messages"""
    pass


@dataclass(frozen=True)
class UploadMessage(ExternalHardwareControlMessage):
    """Message to upload a given binary firmware to the microcontroller"""
    software_id: ManagedUUID


@dataclass(frozen=True)
class InternalSucceededSoftwareDownload(InternalHardwareControlMessage):
    file_path: ExistingFilePath


@dataclass(frozen=True)
class InternalFailedSoftwareDownload(InternalHardwareControlMessage):
    reason: DIPClientError


@dataclass(frozen=True)
class InternalUploadBoardSoftware(InternalHardwareControlMessage):
    file_path: ExistingFilePath


@dataclass(frozen=True)
class InternalSucceededSoftwareUpload(InternalHardwareControlMessage):
    pass


@dataclass(frozen=True)
class InternalFailedSoftwareUpload(InternalHardwareControlMessage):
    reason: DIPClientError


@dataclass(frozen=True)
class UploadResultMessage(ExternalHardwareControlMessage):
    """Message regarding result of a hardware software upload"""
    error: Optional[str]


@dataclass(frozen=True)
class SerialMonitorRequestStop(ExternalHardwareControlMessage):
    """Message to request serial monitor stopping"""
    pass


@dataclass(frozen=True)
class InternalSerialMonitorStopped(InternalHardwareControlMessage):
    pass


@dataclass(frozen=True)
class SerialMonitorRequest(ExternalHardwareControlMessage):
    """Message to request serial monitor for a given microcontroller"""
    config: Optional[ManagedSerialConfig]


@dataclass(frozen=True)
class InternalSerialMonitorStarting(InternalHardwareControlMessage):
    config: Optional[ManagedSerialConfig]


@dataclass(frozen=True)
class InternalSerialMonitorDied(InternalHardwareControlMessage):
    pass


@dataclass(frozen=True)
class InternalStartedSerialMonitor(InternalHardwareControlMessage):
    serial: ManagedSerial


@dataclass(frozen=True)
class InternalSerialMonitorStartFailure(InternalHardwareControlMessage):
    reason: DIPClientError


@dataclass(frozen=True)
class InternalReceivedSerialBytes(InternalHardwareControlMessage, NoisyMessage):
    received_bytes: bytes


@dataclass(frozen=True)
class SerialMonitorResult(ExternalHardwareControlMessage):
    """Message regarding result of a hardware serial monitor request"""
    error: Optional[str]


# Messages incoming and outgoing to and from control server
COMMON_INCOMING_MESSAGE = Union[
    AuthResult,
    InternalStartLifecycle,
    InternalEndLifecycle,
    UploadMessage,
    SerialMonitorRequest,
    SerialMonitorRequestStop,
    SerialMonitorMessageToAgent]
COMMON_OUTGOING_MESSAGE = Union[AuthRequest, UploadResultMessage, PingMessage, SerialMonitorResult, SerialMonitorMessageToClient]


def log_hardware_message(logger: LOGGER, message: Any):
    if isinstance(message, NoisyMessage):
        logger.debug(f"Hardware message: {message}")
    else:
        logger.info(f"Hardware message: {message}")
