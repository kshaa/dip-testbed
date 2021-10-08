"""Module containing messages sent between this agent and the control server"""
from uuid import UUID


class UploadMessage:
    """Message to upload a given binary firmware to the microcontroller"""
    firmware_id: UUID

    def __init__(self, firmware_id: UUID):
        self.firmware_id = firmware_id
