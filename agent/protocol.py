"""Module containing messages sent between this agent and the control server"""
from uuid import UUID
from dataclasses import dataclass
from typing import Union


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
        return str(self.error_message) == str(other.error_message)


CommonIncomingMessage = Union[UploadMessage]
CommonOutgoingMessage = Union[FailedUploadMessage]
