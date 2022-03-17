"""Module for functionality related to serial socket monitor"""
from dataclasses import dataclass
from typing import Any, Optional
from result import Err
from src.domain.death import Death
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.dip_runnable import DIPRunnable
from src.domain.hardware_shared_message import AuthRequest, AuthResult
from src.domain.monitor_message import SerialMonitorMessageToClient, SerialMonitorMessageToAgent, \
    MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE, MonitorUnavailable
from src.service.backend_config import UserPassAuthConfig
from src.service.ws import SocketInterface
from src.protocol.codec import CodecParseException
from src.util import log

LOGGER = log.timed_named_logger("serial_monitor")


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

    @staticmethod
    async def sendAuth(
        socket: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE],
        auth: UserPassAuthConfig
    ):
        """Send auth request into socket"""
        pass

    @staticmethod
    async def expectAuthResult(
        death: Death,
        socket: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE]
    ) -> Optional[DIPClientError]:
        """Wait for auth result response from socket"""
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

    @staticmethod
    async def sendAuth(
        socket: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE],
        auth: UserPassAuthConfig
    ):
        await socket.tx(AuthRequest(auth.username, auth.password))

    @staticmethod
    async def expectAuthResult(
        death: Death,
        socket: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE]
    ) -> Optional[DIPClientError]:
        # Wait for new messages
        try:
            death_or_message = await death.or_awaitable(socket.rx())
        except Exception as e:
            raise e

        # Handle potential death (and stop expecting auth)
        if isinstance(death_or_message, Err):
            LOGGER.debug(f"Serial monitor stopping auth expecation, reason: {death_or_message.value}")
            return GenericClientError("Serial monitor auth was killed by death")

        # Handle connection close (and stop receiving)
        incoming_result = death_or_message.value
        if isinstance(incoming_result, Err):
            return GenericClientError(
                f"Serial monitor auth failed to receive response, reason: {incoming_result.value}")

        # Handle valid message (and continue receiving)
        message = incoming_result.value
        if isinstance(message, AuthResult) and message.error is None:
            return None
        elif isinstance(message, AuthResult) and message.error is not None:
            return GenericClientError(f"Serial monitor auth failed: {message.error}")
        else:
            return GenericClientError(f"Serial monitor auth received non-auth response: {message}")


@dataclass
class MonitorSerial(DIPRunnable):
    """Interface for serial socket monitors"""
    helper: MonitorSerialHelperInterface
    socket: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE]
    auth: UserPassAuthConfig

    async def run(self) -> Optional[DIPClientError]:
        """Receive serial monitor websocket messages & implement user interfacing"""
        pass
