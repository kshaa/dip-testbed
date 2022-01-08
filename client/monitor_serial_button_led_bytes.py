"""Module for functionality related to serial socket monitoring as button/led byte stream"""

import asyncio
from typing import Any, Callable, Optional
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
from monitor_serial_button_led_bytes_app import AppState, define_app
from bitstring import BitArray

LOGGER = log.timed_named_logger("monitor_button_led_bytes")


class MonitorSerialButtonLedBytes(MonitorSerial):
    """Serial socket monitor which interprets the byte stream as a buttons & LEDs"""

    @staticmethod
    def handle_finish(
        socketlike: Socketlike[Any, MonitorListenerIncomingMessage, MonitorListenerOutgoingMessage],
        death: Death
    ):
        death.grace()
        asyncio_loop = asyncio.get_event_loop()
        asyncio_loop.create_task(socketlike.disconnect())

    @staticmethod
    def render_incoming_message(app_state: AppState, incoming_message: SerialMonitorMessageToClient):
        for byte_int in incoming_message.to_bytes():
            bit_array_instance = BitArray(hex=hex(byte_int))
            bits = bit_array_instance.bin.zfill(8)
            for i, c in enumerate(bits):
                app_state.indexed_led_change(i, c == '1')

    @staticmethod
    def render_message_data_or_finish(
        app_state: AppState,
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
            MonitorSerialButtonLedBytes.render_incoming_message(app_state, incoming_message)
            return None
        else:
            handle_finish()
            return Err(f"Unknown message received: {incoming_message.reason}")

    async def run(
        self,
        socketlike: Socketlike[Any, MonitorListenerIncomingMessage, MonitorListenerOutgoingMessage],
    ):
        """Receive serial monitor websocket messages & implement user interfacing"""

        # Create UI app state
        state = AppState()

        # Register button click handler
        def send_on_button_click(button_index: int):
            LOGGER.debug(f"Button clicked: {button_index}")
            button_bytes = bytes([button_index])
            message = SerialMonitorMessageToAgent.from_bytes(button_bytes)
            asyncio_loop = asyncio.get_event_loop()
            asyncio_loop.create_task(socketlike.tx(message))

        state.set_on_indexed_button_click(send_on_button_click)

        # Define end-of-monitor handler
        handle_finish = partial(MonitorSerialButtonLedBytes.handle_finish, socketlike, state.death)

        # Handle signal interrupts
        for signame in ('SIGINT', 'SIGTERM'):
            asyncio_loop = asyncio.get_event_loop()
            asyncio_loop.add_signal_handler(getattr(signal, signame), handle_finish)

        # Start app
        (_ButtonLEDApp, run_button_led_app) = define_app()
        run_button_led_app(state)

        # Run monitoring loop
        while True:
            incoming_message_result = await socketlike.rx()
            result = self.render_message_data_or_finish(state, state.death, handle_finish, incoming_message_result)
            if result is not None:
                return result


# Export class as 'monitor' for explicit importing
monitor = MonitorSerialButtonLedBytes
