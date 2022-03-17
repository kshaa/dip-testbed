"""Module for functionality related to serial socket monitor as button/led byte stream"""

import asyncio
from typing import Callable, Optional
import signal
from pprint import pformat
from result import Err, Result
from websockets.exceptions import ConnectionClosedError
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.fancy_byte import FancyByte
from src.domain.monitor_message import MONITOR_LISTENER_INCOMING_MESSAGE, SerialMonitorMessageToClient, \
    MonitorUnavailable, SerialMonitorMessageToAgent, MONITOR_LISTENER_OUTGOING_MESSAGE
from src.monitor.monitor_serial import MonitorSerial
from src.monitor.monitor_serial_button_led_bytes_app import AppState
from src.monitor.monitor_serial_button_led_bytes_app import ButtonLEDApp
from src.util import log
from src.protocol.codec import CodecParseException
from src.service.ws import SocketInterface
from src.domain.death import Death
from functools import partial

LOGGER = log.timed_named_logger("monitor_button_led_bytes")


class MonitorSerialButtonLedBytes(MonitorSerial):
    """Serial socket monitor which interprets the byte stream as a buttons & LEDs"""

    @staticmethod
    def handle_finish(
        socketlike: SocketInterface[MONITOR_LISTENER_INCOMING_MESSAGE, MONITOR_LISTENER_OUTGOING_MESSAGE],
        death: Death
    ):
        death.grace()
        asyncio_loop = asyncio.get_event_loop()
        asyncio_loop.create_task(socketlike.disconnect())

    @staticmethod
    def render_incoming_message(app_state: AppState, incoming_message: SerialMonitorMessageToClient):
        for byte in incoming_message.content_bytes:
            fancy_byte_result = FancyByte.fromInt(byte)
            if isinstance(fancy_byte_result, Err): return
            fancy_byte = fancy_byte_result.value
            bits = fancy_byte.to_binary_bits()
            for index, is_on in enumerate(bits):
                app_state.indexed_led_change(fancy_byte, index, is_on)

    @staticmethod
    def render_message_data_or_finish(
        app_state: AppState,
        death: Death,
        handle_finish: Callable,
        incoming_message_result: Result[MONITOR_LISTENER_INCOMING_MESSAGE, Exception]
    ) -> Optional[DIPClientError]:
        """Handle incoming serial message"""

        # Handle message failures
        if death.gracing:
            handle_finish()
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
            return GenericClientError(f"Monitor not available anymore: {incoming_message.reason}")
        elif isinstance(incoming_message, SerialMonitorMessageToClient):
            MonitorSerialButtonLedBytes.render_incoming_message(app_state, incoming_message)
            return None
        else:
            handle_finish()
            return GenericClientError(f"Unknown message received: {incoming_message.reason}")

    async def run(self) -> Optional[DIPClientError]:
        """Receive serial monitor websocket messages & implement user interfacing"""

        # Create UI app state
        state = AppState()

        # Handle signal interrupts
        for signame in ('SIGINT', 'SIGTERM'):
            asyncio_loop = asyncio.get_event_loop()
            asyncio_loop.add_signal_handler(getattr(signal, signame), partial(state.death.grace))

        # Start socket
        connect_error = await self.socket.connect()
        if connect_error is not None:
            return GenericClientError(f"Failed connecting to control server, reason: {connect_error}")

        # Send auth request and wait for response
        await self.helper.sendAuth(self.socket, self.auth)
        auth_error = await self.helper.expectAuthResult(state.death, self.socket)
        if auth_error is not None:
            return auth_error

        # Register button click handler
        def send_on_button_click(button_index: int):
            LOGGER.debug(f"Button clicked: {button_index}")
            button_bytes = bytes([button_index])
            message = SerialMonitorMessageToAgent(button_bytes)
            asyncio_loop = asyncio.get_event_loop()
            asyncio_loop.create_task(self.socket.tx(message))

        state.set_on_indexed_button_click(send_on_button_click)

        # Define end-of-monitor handler
        handle_finish = partial(MonitorSerialButtonLedBytes.handle_finish, self.socket, state.death)

        # Handle signal interrupts
        for signame in ('SIGINT', 'SIGTERM'):
            asyncio_loop = asyncio.get_event_loop()
            asyncio_loop.add_signal_handler(getattr(signal, signame), handle_finish)

        # Start app
        loop = asyncio.get_event_loop()
        loop.create_task(ButtonLEDApp.run_with_state(state))

        # Run monitor loop
        while not state.death.gracing:
            # Wait for new message
            death_or_incoming_message = await state.death.or_awaitable(self.socket.rx())

            # Handle potential death
            if isinstance(death_or_incoming_message, Err):
                return

            incoming_message_result = death_or_incoming_message.value
            result = self.render_message_data_or_finish(state, state.death, handle_finish, incoming_message_result)
            if result is not None:
                return result
