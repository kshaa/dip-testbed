"""Module containing messages sent between this client and the control server"""

from typing import TypeVar, Generic, Union
from uuid import UUID
from dataclasses import dataclass

T = TypeVar('T')


@dataclass(frozen=True, eq=False)
class UploadMessage:
    """Message to upload a given binary firmware to the microcontroller"""
    software_id: UUID

    def __eq__(self, other) -> bool:
        return str(self.software_id) == str(other.software_id)


@dataclass(frozen=True, eq=False)
class FailedUploadMessage:
    """Message regarding failure to upload a given binary firmware to the microcontroller"""
    error_message: str

    def __eq__(self, other) -> bool:
        return self.error_message == other.error_message


@dataclass(frozen=True, eq=False)
class CreateUserMessage:
    """Message to request user creation"""
    username: str
    password: str

    def __eq__(self, other) -> bool:
        return self.username == other.username and \
               self.password == other.password


@dataclass(frozen=True, eq=False)
class SuccessMessage(Generic[T]):
    """Message containing success content"""
    value: T


@dataclass(frozen=True, eq=False)
class FailureMessage(Generic[T]):
    """Message containing failure content"""
    value: T


CommonIncomingMessage = Union[UploadMessage]
CommonOutgoingMessage = Union[FailedUploadMessage]
