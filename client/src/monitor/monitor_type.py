#!/usr/bin/env python
"""Available virtual monitoring interfaces"""
from dataclasses import dataclass
from enum import Enum, unique
from typing import Optional
from result import Result, Err, Ok
from src.domain.dip_client_error import DIPClientError
from src.domain.dip_runnable import DIPRunnable
from src.domain.positive_integer import PositiveInteger
from src.engine.monitor.minos.minos_suite import MinOSSuite
from src.monitor.monitor_serial import MonitorSerialHelper
from src.monitor.monitor_serial_button_led_bytes import MonitorSerialButtonLedBytes
from src.monitor.monitor_serial_hex_bytes import MonitorSerialHexbytes
from src.monitor.monitor_serial_min_os import MonitorSerialMinOS
from src.protocol import s11n_hybrid
from src.service.backend_config import UserPassAuthConfig
from src.service.managed_url import ManagedURL
from src.service.ws import WebSocket


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
    minos = 2
    minosrequest = 3

    @staticmethod
    def build(value: str) -> Result['MonitorType', MonitorTypeBuildError]:
        monitor_type_matches = [t for t in MonitorType if t.name == value]
        monitor_type = next(iter(monitor_type_matches), None)
        if monitor_type is None:
            return Err(MonitorTypeBuildError(value))
        return Ok(monitor_type)

    @staticmethod
    def socket(url: ManagedURL):
        decoder = s11n_hybrid.MONITOR_LISTENER_INCOMING_MESSAGE_DECODER
        encoder = s11n_hybrid.MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER
        return WebSocket(url, decoder, encoder)

    def resolve(
        self,
        heartbeat_seconds: PositiveInteger,
        socket_url: ManagedURL,
        auth: UserPassAuthConfig,
        minos_suite: Optional[MinOSSuite]
    ) -> Result[DIPRunnable, MonitorResolutionError]:
        # Monitor implementation resolution
        monitor: Optional[DIPRunnable] = None
        if self is MonitorType.hexbytes:
            socket = MonitorType.socket(socket_url)
            monitor = MonitorSerialHexbytes(MonitorSerialHelper(), socket, auth)
        elif self is MonitorType.buttonleds:
            socket = MonitorType.socket(socket_url)
            monitor = MonitorSerialButtonLedBytes(MonitorSerialHelper(), socket, auth)
        elif self is MonitorType.minos:
            monitor = MonitorSerialMinOS(heartbeat_seconds, auth, socket_url, None)
        elif self is MonitorType.minosrequest and minos_suite is not None:
            monitor = MonitorSerialMinOS(heartbeat_seconds, auth, socket_url, minos_suite)
        return Ok(monitor)
