"""Module for functionality related to serial socket monitoring"""

import asyncio
from death import Death
from asyncio import Task
from typing import Any
from protocol import \
    MonitorListenerIncomingMessage, \
    MonitorListenerOutgoingMessage, \
    MonitorUnavailable, \
    SerialMonitorMessageToClient, \
    SerialMonitorMessageToAgent
from ws import Socketlike
from codec import CodecParseException


class MonitorSerialHelperLike:
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


class MonitorSerialHelper(MonitorSerialHelperLike):
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
        return SerialMonitorMessageToAgent.from_bytes(payload)


class MonitorSerial:
    """Interface for serial socket monitors"""

    helper: MonitorSerialHelperLike

    def __init__(self, helper):
        self.helper = helper

    async def run(
        self,
        socketlike: Socketlike[Any, MonitorListenerIncomingMessage, MonitorListenerOutgoingMessage]
    ):
        """Receive serial monitor websocket messages & implement user interfacing"""
        pass
