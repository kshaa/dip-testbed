"""Module containing messages sent between this client and the management server"""

from typing import TypeVar, Generic
from dataclasses import dataclass

T = TypeVar('T')


@dataclass(frozen=True)
class SuccessMessage(Generic[T]):
    """Message containing success content"""
    value: T


@dataclass(frozen=True)
class FailureMessage(Generic[T]):
    """Message containing failure content"""
    value: T


@dataclass(frozen=True)
class CreateUserMessage:
    """Message to request user creation"""
    username: str
    password: str

    def __eq__(self, other) -> bool:
        return self.username == other.username and \
               self.password == other.password


@dataclass(frozen=True)
class CreateHardwareMessage:
    """Message to request hardware creation"""
    name: str

    def __eq__(self, other) -> bool:
        return self.name == other.name

