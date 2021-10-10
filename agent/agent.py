#!/usr/bin/env python
"""Supervising agent, listening to server commands, passing to agent-specific engine"""

from typing import TypeVar
from pprint import pformat
from dataclasses import dataclass
from urllib.parse import ParseResult
from websockets.exceptions import ConnectionClosedError
from result import Err
from agent_util import unparse_url
from ws import WebSocket
import log
from codec import CodecParseException, Encoder, Decoder
from engine import Engine

LOGGER = log.timed_named_logger("agent")

@dataclass(frozen=True, eq=False)
class AgentConfig:
    """Common i.e. microcontroller-non-specific agent configuration options"""
    control_server: ParseResult
    static_server: ParseResult


PI = TypeVar('PI')
PO = TypeVar('PO')


async def agent(
        config: AgentConfig,
        encoder: Encoder[PO],
        decoder: Decoder[PI],
        engine: Engine[PI, PO]) -> int:
    """Supervising agent, which connects to a websocket, listens
     to commands from server, passes them to an agent-specific engine"""
    control_sever_str_result = unparse_url(config.control_server)
    if isinstance(control_sever_str_result, Err):
        LOGGER.error("Couldn't encode control server URL: %s", control_sever_str_result.value)
        return 0
    control_sever_str = control_sever_str_result.value
    websocket = WebSocket(control_sever_str, decoder, encoder)
    LOGGER.debug("Connecting connect to control server: %s", config.control_server)
    error = await websocket.connect()
    if error is not None:
        LOGGER.error("Couldn't connect to control server: %s", error)
        return 0

    LOGGER.info("Connected to control server, listening for commands")
    while True:
        incoming_result = await websocket.rx()
        if isinstance(incoming_result, Err) \
                and isinstance(incoming_result.value, ConnectionClosedError):
            LOGGER.error("Control server connection closed")
            return 1
        if isinstance(incoming_result, Err) \
                and isinstance(incoming_result.value, CodecParseException):
            LOGGER.error("Unknown command received, ignoring")
        elif isinstance(incoming_result, Err):
            LOGGER.error("Failed to receive message: %s", pformat(incoming_result.value, indent=4))
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
                    await websocket.disconnect()
                    return 1
                else:
                    LOGGER.info(
                        "Message transmitted: %s",
                        pformat(outgoing_message, indent=4))