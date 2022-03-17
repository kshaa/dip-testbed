#!/usr/bin/env python
"""Available virtual monitoring interfaces"""
from dataclasses import dataclass
from enum import Enum, unique
from typing import Optional
from result import Result, Err, Ok
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.monitor.monitor_serial import MonitorSerial, MonitorSerialHelper
from src.monitor.monitor_serial_button_led_bytes import MonitorSerialButtonLedBytes
from src.monitor.monitor_serial_hex_bytes import MonitorSerialHexbytes
from src.service.backend_config import UserPassAuthConfig
from src.service.ws import SocketInterface
from src.util import pymodules


@dataclass
class MonitorTypeBuildError(DIPClientError):
    source_value: str

    def text(self):
        return f"Invalid monitor type value '{self.source_value}'"


@dataclass
class MonitorResolutionError(DIPClientError):
    title: str
    reason: Optional[str] = None
    exception: Optional[Exception] = None
    error: Optional[DIPClientError] = None

    def text(self):
        clarification = f", reason: {self.error.text()}" if self.error is not None \
            else f", reason: {str(self.reason)}" if self.reason is not None \
            else f", reason: {str(self.exception)}" if self.exception is not None \
            else ""
        return f"Monitor resolution error '{self.title}'{clarification}"


@unique
class MonitorType(Enum):
    """Choices of available monitor implementations"""
    hexbytes = 0
    buttonleds = 1

    @staticmethod
    def build(value: str) -> Result['MonitorType', MonitorTypeBuildError]:
        monitor_type_matches = [t for t in MonitorType if t.name == value]
        monitor_type = next(iter(monitor_type_matches), None)
        if monitor_type is None:
            return Err(MonitorTypeBuildError(value))
        return Ok(monitor_type)

    def resolve(
        self,
        socket: SocketInterface,
        auth: UserPassAuthConfig
    ) -> Result[MonitorSerial, MonitorResolutionError]:
        # Monitor implementation resolution
        monitor: Optional[MonitorSerial] = None
        if self is MonitorType.hexbytes:
            monitor = MonitorSerialHexbytes(MonitorSerialHelper(), socket, auth)
        elif self is MonitorType.buttonleds:
            monitor = MonitorSerialButtonLedBytes(MonitorSerialHelper(), socket, auth)
        return Ok(monitor)
