"""Module containing messages sent between this client and the control server"""

from typing import TypeVar, Generic, Union, Optional
from uuid import UUID
import base64
from dataclasses import dataclass
from serial_util import SerialConfig

T = TypeVar('T')


@dataclass(frozen=True, eq=False)
class UploadMessage:
    """Message to upload a given binary firmware to the microcontroller"""
    software_id: UUID

    def __eq__(self, other) -> bool:
        return str(self.software_id) == str(other.software_id)


@dataclass(frozen=True, eq=False)
class UploadResultMessage:
    """Message regarding result of a hardware software upload"""
    error: Optional[str]

    def __eq__(self, other) -> bool:
        return self.error == other.error


@dataclass(frozen=True, eq=False)
class SerialMonitorRequestStop:
    """Message to request serial monitor stopping"""
    pass


@dataclass(frozen=True, eq=False)
class SerialMonitorRequest:
    """Message to request serial monitor for a given microcontroller"""
    config: Optional[SerialConfig]


@dataclass(frozen=True, eq=False)
class SerialMonitorResult:
    """Message regarding result of a hardware serial monitor request"""
    error: Optional[str]


@dataclass(frozen=True, eq=False)
class SerialMonitorMessageToAgent:
    """Message from client to hardware serial monitor"""
    base64Bytes: str

    @staticmethod
    def from_bytes(content: bytes):
        """Construct message from bytes"""
        return SerialMonitorMessageToAgent(base64.b64encode(content).decode("utf-8"))

    def to_bytes(self):
        """Construct bytes from message"""
        return base64.b64decode(self.base64Bytes)


@dataclass(frozen=True, eq=False)
class SerialMonitorMessageToClient:
    """Message from hardware serial monitor to client"""
    base64Bytes: str

    @staticmethod
    def from_bytes(content: bytes):
        """Construct message from bytes"""
        return SerialMonitorMessageToClient(base64.b64encode(content).decode("utf-8"))

    def to_bytes(self) -> bytes:
        """Construct bytes from message"""
        return base64.b64decode(self.base64Bytes)


@dataclass(frozen=True, eq=False)
class MonitorUnavailable:
    """Message regarding hardware monitor unavailability"""
    reason: str


@dataclass(frozen=True, eq=False)
class CreateUserMessage:
    """Message to request user creation"""
    username: str
    password: str

    def __eq__(self, other) -> bool:
        return self.username == other.username and \
               self.password == other.password


@dataclass(frozen=True, eq=False)
class CreateHardwareMessage:
    """Message to request hardware creation"""
    name: str

    def __eq__(self, other) -> bool:
        return self.name == other.name


@dataclass(frozen=True, eq=False)
class SuccessMessage(Generic[T]):
    """Message containing success content"""
    value: T


@dataclass(frozen=True, eq=False)
class FailureMessage(Generic[T]):
    """Message containing failure content"""
    value: T


@dataclass(frozen=True, eq=False)
class PingMessage(Generic[T]):
    """Message for sending heartbeats to server"""


CommonIncomingMessage = Union[
    UploadMessage,
    SerialMonitorRequest,
    SerialMonitorRequestStop,
    SerialMonitorMessageToAgent]
CommonOutgoingMessage = Union[UploadResultMessage, PingMessage, SerialMonitorResult, SerialMonitorMessageToClient]

MonitorListenerIncomingMessage = Union[MonitorUnavailable, SerialMonitorMessageToClient]
MonitorListenerOutgoingMessage = Union[SerialMonitorMessageToAgent]
