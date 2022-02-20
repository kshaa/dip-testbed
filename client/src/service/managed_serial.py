"""Module for handling serial connections"""
from dataclasses import dataclass
from pprint import pformat
from typing import Optional

from result import Result, Ok, Err
from serial import Serial

from src.domain.dip_client_error import GenericClientError, DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.service.managed_serial_config import ManagedSerialConfig
from src.util import log

LOGGER = log.timed_named_logger("serial")


@dataclass
class ManagedSerial:
    """Shim for middle-managing a serial connection"""
    config: ManagedSerialConfig
    connection: Optional[Serial] = None

    @staticmethod
    def build(
        path: ExistingFilePath,
        config: ManagedSerialConfig
    ) -> Result['ManagedSerial', DIPClientError]:
        """Connect to a serial device"""
        try:
            # Define serial interface
            serial = Serial(
                path.value,
                baudrate=config.baudrate
            )
            serial.timeout = config.timeout

            # Log success
            LOGGER.info(
                "Configured serial device '%s' w/ config %s",
                path.value,
                pformat(config, indent=4))

            # Return device
            return Ok(ManagedSerial(config, serial))
        except Exception as e:
            return GenericClientError(f"Failed to start monitor: {str(e)}")

    async def read(self) -> Result[bytes, DIPClientError]:
        if self.connection is None:
            return Err(GenericClientError("Serial connection closed"))
        try:
            received_bytes = self.connection.read(self.config.receive_size)
            return Ok(received_bytes)
        except Exception as e:
            self.connection = None
            return Err(GenericClientError(f"Serial connection closed: {str(e)}"))

    async def write(self, content: bytes) -> Result[type(None), DIPClientError]:
        if self.connection is None:
            return Err(GenericClientError("Serial connection closed"))
        try:
            self.connection.write(content)
            return Ok()
        except Exception as e:
            self.connection = None
            return Err(GenericClientError(f"Serial connection closed: {str(e)}"))

    async def close(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None