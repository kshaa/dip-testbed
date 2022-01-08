"""Module for functionality related to serial socket monitoring"""

import sys
import asyncio
from asyncio import Task
from typing import Any, Callable, Optional
import termios
import tty
import signal
from pprint import pformat
from result import Ok, Err, Result
from websockets.exceptions import ConnectionClosedError
from protocol import \
    SerialMonitorMessageToAgent, \
    MonitorListenerIncomingMessage, \
    MonitorListenerOutgoingMessage, \
    MonitorUnavailable, \
    SerialMonitorMessageToClient
import log
from codec import CodecParseException
from ws import Socketlike
from death import Death
from monitor_serial import MonitorSerial
from functools import partial

LOGGER = log.timed_named_logger("monitor_serial")

# Mocks for DIP client classes for python type hinting
# N.B This whole section can be removed if you don't care about type checking
#   and if you're just editing in Notepad and doing it trial-and-error style

# class Socketlike(Generic[SERIALIZABLE, PI, PO]):
#     """Interface for interactions w/ sockets"""
#     async def connect(self) -> Optional[Exception]:
#         pass
#
#     async def disconnect(self) -> Optional[Exception]:
#         pass
#
#     async def rx(self) -> Result[PI, Exception]:
#         pass
#
#     async def tx(self, data: PO) -> Optional[Exception]:
#         pass
#
# @dataclass(frozen=True, eq=False)
# class MonitorUnavailable:
#     """Message regarding hardware monitor unavailability"""
#     reason: str
#
# @dataclass(frozen=True, eq=False)
# class SerialMonitorMessageToClient:
#     """Message from hardware serial monitor to client"""
#     base64Bytes: str
#
#     @staticmethod
#     def from_bytes(content: bytes):
#         """Construct message from bytes"""
#         return SerialMonitorMessageToClient(base64.b64encode(content).decode("utf-8"))
#
#     def to_bytes(self) -> bytes:
#         """Construct bytes from message"""
#         return base64.b64decode(self.base64Bytes)
#
# class MonitorSerial:
#     """"""
#     async def run(
#         self,
#         socketike: Socketlike[Any, protocol.MonitorListenerIncomingMessage, protocol.MonitorListenerOutgoingMessage]
#     ):
#         """Receive serial monitor websocket messages & implement user interfacing"""
#         pass


# Actual monitor implementation
class MonitorSerialHexbytes(MonitorSerial):
    """Serial socket monitor, which sends keyboard keys as bytes & prints incoming data as hex bytes"""

    @staticmethod
    def silence_stdin() -> list:
        """Stop stdin from immediately being printed back out to stdout"""
        stdin = sys.stdin.fileno()
        tattr = termios.tcgetattr(stdin)
        tty.setcbreak(stdin, termios.TCSANOW)
        sys.stdout.write("\x1b[6n")
        sys.stdout.flush()
        return tattr

    @staticmethod
    def unsilence_stdin(tattr: list):
        """Allow stdin to be immediately printed back out to stdout"""
        stdin = sys.stdin.fileno()
        termios.tcsetattr(stdin, termios.TCSANOW, tattr)

    @staticmethod
    async def keep_transmitting_to_agent(
        socketlike: Socketlike[Any, MonitorListenerIncomingMessage, MonitorListenerOutgoingMessage]
    ):
        """Send keyboard data from stdin straight to serial monitor socket"""
        asyncio_loop = asyncio.get_event_loop()
        stdin_reader = asyncio.StreamReader()
        stdin_protocol = asyncio.StreamReaderProtocol(stdin_reader)
        await asyncio_loop.connect_read_pipe(lambda: stdin_protocol, sys.stdin)
        while True:
            read_bytes = await stdin_reader.read(1)
            message = SerialMonitorMessageToAgent.from_bytes(read_bytes)
            await socketlike.tx(message)

    @staticmethod
    def handle_finish(
        socketlike: Socketlike[Any, MonitorListenerIncomingMessage, MonitorListenerOutgoingMessage],
        death: Death,
        stdin_capture_task: Task,
        tattr: list,
    ):
        asyncio_loop = asyncio.get_event_loop()
        death.grace()
        stdin_capture_task.cancel()
        asyncio_loop.create_task(socketlike.disconnect())
        MonitorSerialHexbytes.unsilence_stdin(tattr)

    @staticmethod
    def render_incoming_message(incoming_message: SerialMonitorMessageToClient):
        for byte_int in incoming_message.to_bytes():
            render = f"[{hex(byte_int)}:{chr(byte_int)}] "
            sys.stdout.buffer.write(str.encode(render))
            sys.stdout.buffer.flush()

    @staticmethod
    def render_message_data_or_finish(
        death: Death,
        handle_finish: Callable,
        incoming_message_result: Result[MonitorListenerIncomingMessage, Exception]
    ) -> Optional[Result[type(True), str]]:
        """Handle incoming serial message"""

        # Handle message failures
        if death.gracing:
            return Ok()
        elif isinstance(incoming_message_result, Err) \
                and isinstance(incoming_message_result.value, ConnectionClosedError):
            handle_finish()
            return Err("Control server connection closed")
        if isinstance(incoming_message_result, Err) \
                and isinstance(incoming_message_result.value, CodecParseException):
            handle_finish()
            return Err("Unknown command received, ignoring")
        elif isinstance(incoming_message_result, Err):
            handle_finish()
            return Err(f"Failed to receive message: {pformat(incoming_message_result.value, indent=4)}")

        # Handle successful message
        incoming_message = incoming_message_result.value
        if isinstance(incoming_message, MonitorUnavailable):
            handle_finish()
            return Err(f"Monitor not available anymore: {incoming_message.reason}")
        elif isinstance(incoming_message, SerialMonitorMessageToClient):
            MonitorSerialHexbytes.render_incoming_message(incoming_message)
            return None
        else:
            handle_finish()
            return Err(f"Unknown message received: {incoming_message.reason}")

    async def run(
        self,
        socketlike: Socketlike[Any, MonitorListenerIncomingMessage, MonitorListenerOutgoingMessage],
    ):
        """Receive serial monitor websocket messages & implement user interfacing"""

        # Silence stdin
        tattr = MonitorSerialHexbytes.silence_stdin()

        # Redirect stdin to serial monitor socket
        asyncio_loop = asyncio.get_event_loop()
        stdin_capture_task = asyncio_loop.create_task(
            MonitorSerialHexbytes.keep_transmitting_to_agent(socketlike))

        # Define end-of-monitor handler
        death = Death()
        handle_finish = partial(
            MonitorSerialHexbytes.handle_finish,
            socketlike,
            death,
            stdin_capture_task,
            tattr)

        # Handle signal interrupts
        for signame in ('SIGINT', 'SIGTERM'):
            asyncio_loop.add_signal_handler(getattr(signal, signame), handle_finish)

        # Run monitoring loop
        while True:
            incoming_message_result = await socketlike.rx()
            result = MonitorSerialHexbytes.render_message_data_or_finish(death, handle_finish, incoming_message_result)
            if result is not None:
                return result


# Export class as 'monitor' for explicit importing
monitor = MonitorSerialHexbytes
