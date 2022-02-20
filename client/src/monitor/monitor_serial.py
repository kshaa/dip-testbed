"""Module for functionality related to serial socket monitor"""
from dataclasses import dataclass
from typing import Any, Optional
from src.domain.dip_client_error import DIPClientError
from src.domain.dip_runnable import DIPRunnable
from src.domain.monitor_message import SerialMonitorMessageToClient, SerialMonitorMessageToAgent, \
    MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE, MonitorUnavailable
from src.service.ws import SocketInterface
from src.protocol.codec import CodecParseException


class MonitorSerialHelperInterface:
    """Helper for managing monitor messages"""

    @staticmethod
    def isMonitorUnavailable(message: Any) -> bool:
        """Check if message is of type 'MonitorUnavailable'"""
        pass

    @staticmethod
    def isSerialMonitorMessageToClient(message: Any) -> bool:
        """Check if message is of type 'SerialMonitorMessageToClient'"""
        pass

    @staticmethod
    def isCodecParseException(instance: Any) -> bool:
        """Check if class instance is of type 'CodecParseException'"""
        pass

    @staticmethod
    def createSerialMonitorMessageToAgent(payload: bytes) -> Any:
        """Create createSerialMonitorMessageToAgent from bytes"""
        pass


class MonitorSerialHelper(MonitorSerialHelperInterface):
    """Helper for managing monitor messages"""

    @staticmethod
    def isMonitorUnavailable(message: Any) -> bool:
        """Check if message is of type 'MonitorUnavailable'"""
        return isinstance(message, MonitorUnavailable)

    @staticmethod
    def isSerialMonitorMessageToClient(message: Any) -> bool:
        """Check if message is of type 'SerialMonitorMessageToClient'"""
        return isinstance(message, SerialMonitorMessageToClient)

    @staticmethod
    def isCodecParseException(instance: Any) -> bool:
        """Check if class instance is of type 'CodecParseException'"""
        return isinstance(instance, CodecParseException)

    @staticmethod
    def createSerialMonitorMessageToAgent(payload: bytes) -> Any:
        """Create createSerialMonitorMessageToAgent from bytes"""
        return SerialMonitorMessageToAgent(payload)


@dataclass
class MonitorSerial(DIPRunnable):
    """Interface for serial socket monitors"""
    helper: MonitorSerialHelperInterface
    socket: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE]

    async def run(self) -> Optional[DIPClientError]:
        """Receive serial monitor websocket messages & implement user interfacing"""
        pass
