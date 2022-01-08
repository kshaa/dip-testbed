"""Module for functionality related to serial socket monitoring"""

from typing import Any
from protocol import MonitorListenerIncomingMessage, MonitorListenerOutgoingMessage
from ws import Socketlike


class MonitorSerial:
    """Interface for serial socket monitors"""
    async def run(
        self,
        socketlike: Socketlike[Any, MonitorListenerIncomingMessage, MonitorListenerOutgoingMessage]
    ):
        """Receive serial monitor websocket messages & implement user interfacing"""
        pass
