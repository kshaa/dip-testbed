#!/usr/bin/env python
"""Supervising client, listening to server commands, passing to client-specific engine"""

from typing import TypeVar
from pprint import pformat
from result import Err
from websockets.exceptions import ConnectionClosedError
from ws import WebSocket
import log
from codec import CodecParseException, Encoder, Decoder
from engine import Engine
from agent_util import AgentConfig

LOGGER = log.timed_named_logger("client")
PI = TypeVar('PI')
PO = TypeVar('PO')


async def agent(
        config: AgentConfig,
        encoder: Encoder[PO],
        decoder: Decoder[PI],
        engine: Engine[PI, PO]) -> int:
    """Supervising client, which connects to a websocket, listens
     to commands from server, passes them to an client-specific engine"""

    # Construct hardware control URL
    hardware_control_url_result = config.backend.hardware_control_url(config.hardware_id)
    if isinstance(hardware_control_url_result, Err):
        LOGGER.error(
            "Couldn't construct hardware-specific control server URL: %s",
            hardware_control_url_result.value)
        return 0
    hardware_control_url = hardware_control_url_result.value

    # Connect to control
    websocket = WebSocket(hardware_control_url, decoder, encoder)
    LOGGER.debug("Connecting connect to control server: %s", config.backend.control_server)
    error = await websocket.connect()
    if error is not None:
        LOGGER.error("Couldn't connect to control server: %s", error)
        return 0

    # Start communication/logic loop
    LOGGER.info(
        "Connected to control server, listening for commands, running start hook")
    engine.on_start(websocket)
    while True:
        incoming_result = await websocket.rx()
        if isinstance(incoming_result, Err) \
                and isinstance(incoming_result.value, ConnectionClosedError):
            LOGGER.error("Control server connection closed")
            engine.on_end()
            return 1
        if isinstance(incoming_result, Err) \
                and isinstance(incoming_result.value, CodecParseException):
            LOGGER.error("Unknown command received, ignoring")
        elif isinstance(incoming_result, Err):
            LOGGER.error("Failed to receive message: %s", pformat(incoming_result.value, indent=4))
            engine.on_end()
            await websocket.disconnect()
            return 1
        else:
            incoming_message = incoming_result.value
            LOGGER.info("Message received: %s", pformat(incoming_message, indent=4))
            LOGGER.debug("Message processing started")
            outgoing_result = engine.process(incoming_message)
            LOGGER.debug("Message processing stopped")
            if isinstance(outgoing_result, Err) \
                    and isinstance(outgoing_result.value, NotImplementedError):
                LOGGER.error("Command known, but processor not implemented, ignoring")
            elif isinstance(outgoing_result, Err):
                LOGGER.error(
                    "Failed to process message: %s",
                    pformat(outgoing_result.value, indent=4))
                engine.on_end()
                await websocket.disconnect()
                return 1
            else:
                outgoing_message = outgoing_result.value
                transmit_error = await websocket.tx(outgoing_message)
                if transmit_error is not None:
                    LOGGER.info(
                        "Failed to transmit message (%s): %s",
                        pformat(outgoing_message, indent=4),
                        pformat(transmit_error, indent=4))
                    engine.on_end()
                    await websocket.disconnect()
                    return 1
                else:
                    LOGGER.info(
                        "Message transmitted: %s",
                        pformat(outgoing_message, indent=4))
