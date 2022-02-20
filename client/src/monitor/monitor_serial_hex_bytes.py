"""Module for functionality related to serial socket monitor as hex byte stream"""

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

from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.monitor_message import MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE, \
    SerialMonitorMessageToAgent, SerialMonitorMessageToClient, MonitorUnavailable
from src.monitor.monitor_serial import MonitorSerial
from src.protocol.codec import CodecParseException
from src.service.ws import SocketInterface
from src.domain.death import Death
from functools import partial


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
        socketlike: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE]
    ):
        """Send keyboard data from stdin straight to serial monitor socket"""
        asyncio_loop = asyncio.get_event_loop()
        stdin_reader = asyncio.StreamReader()
        stdin_protocol = asyncio.StreamReaderProtocol(stdin_reader)
        await asyncio_loop.connect_read_pipe(lambda: stdin_protocol, sys.stdin)
        while True:
            read_bytes = await stdin_reader.read(1)
            message = SerialMonitorMessageToAgent(read_bytes)
            await socketlike.tx(message)

    @staticmethod
    def handle_finish(
        socket: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE],
        death: Death,
        stdin_capture_task: Task,
        tattr: list,
    ):
        asyncio_loop = asyncio.get_event_loop()
        death.grace()
        stdin_capture_task.cancel()
        asyncio_loop.create_task(socket.disconnect())
        MonitorSerialHexbytes.unsilence_stdin(tattr)

    @staticmethod
    def render_incoming_message(incoming_message: SerialMonitorMessageToClient):
        for byte_int in incoming_message.content_bytes:
            render = f"[{hex(byte_int)}:{chr(byte_int)}] "
            sys.stdout.buffer.write(str.encode(render))
            sys.stdout.buffer.flush()

    @staticmethod
    def render_message_data_or_finish(
        death: Death,
        handle_finish: Callable,
        incoming_message_result: Result[MONITOR_LISTENER_INCOMING_MESSAGE, Exception]
    ) -> Optional[DIPClientError]:
        """Handle incoming serial message"""

        # Handle message failures
        if death.gracing:
            return None
        elif isinstance(incoming_message_result, Err) \
                and isinstance(incoming_message_result.value, ConnectionClosedError):
            handle_finish()
            return GenericClientError("Control server connection closed")
        if isinstance(incoming_message_result, Err) \
                and isinstance(incoming_message_result.value, CodecParseException):
            handle_finish()
            return GenericClientError("Unknown command received, ignoring")
        elif isinstance(incoming_message_result, Err):
            handle_finish()
            return GenericClientError(f"Failed to receive message: {pformat(incoming_message_result.value, indent=4)}")

        # Handle successful message
        incoming_message = incoming_message_result.value
        if isinstance(incoming_message, MonitorUnavailable):
            handle_finish()
            return GenericClientError(f"Monitor not available: {incoming_message.reason}")
        elif isinstance(incoming_message, SerialMonitorMessageToClient):
            MonitorSerialHexbytes.render_incoming_message(incoming_message)
            return None
        else:
            handle_finish()
            return GenericClientError(f"Unknown message received: {incoming_message.reason}")

    async def run(self) -> Optional[DIPClientError]:
        """Receive serial monitor websocket messages & implement user interfacing"""

        # Start socket
        connect_error = await self.socket.connect()
        if connect_error is not None:
            return GenericClientError(f"Failed connecting to control server, reason: {connect_error}")

        # Silence stdin
        tattr = MonitorSerialHexbytes.silence_stdin()

        # Redirect stdin to serial monitor socket
        asyncio_loop = asyncio.get_event_loop()
        stdin_capture_task = asyncio_loop.create_task(
            self.keep_transmitting_to_agent(self.socket))

        # Define end-of-monitor handler
        death = Death()
        handle_finish = partial(
            MonitorSerialHexbytes.handle_finish,
            self.socket,
            death,
            stdin_capture_task,
            tattr)

        # Handle signal interrupts
        for signame in ('SIGINT', 'SIGTERM'):
            asyncio_loop.add_signal_handler(getattr(signal, signame), handle_finish)

        # Run monitor loop
        while not death.gracing:
            # Wait for new message
            death_or_incoming_message = await death.or_awaitable(self.socket.rx())

            # Handle potential death
            if isinstance(death_or_incoming_message, Err):
                return

            incoming_message_result = death_or_incoming_message.value
            result = self.render_message_data_or_finish(death, handle_finish, incoming_message_result)
            if result is not None:
                return result


# Export class as 'monitor' for explicit importing
monitor = MonitorSerialHexbytes
