"""Module containing messages sent between this agent and the control server"""
from uuid import UUID
from dataclasses import dataclass

@dataclass(frozen=True, eq=False)
class UploadMessage:
    """Message to upload a given binary firmware to the microcontroller"""
    firmware_id: UUID

    def __eq__(self, other) -> bool:
        return str(self.firmware_id) == str(other.firmware_id)
