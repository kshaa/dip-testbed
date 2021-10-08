#!/usr/bin/env python
"""Supervising agent, listening to server commands, passing to agent-specific engine"""

from pprint import pprint, pformat
from websockets.exceptions import ConnectionClosedError
from ws import WebSocket
import log
from codec import identityDecoder, identityEncoder
from engine import Engine

LOGGER = log.timed_named_logger("agent")


async def agent() -> int:
    """Supervising agent, which connects to a websocket, listens
     to commands from server, passes them to an agent-specific engine"""
    engine: Engine[str, str] = Engine()
    control_server = "ws://localhost:12345"
    websocket = WebSocket(control_server, identityDecoder, identityEncoder)
    LOGGER.debug("Connecting connect to control server: %s", control_server)
    error = await websocket.connect()
    if error.isDefined:
        LOGGER.error("Couldn't connect to control server: %s", error.value)
        return 0

    LOGGER.info("Connected to control server, listening for commands")

    while True:
        incoming_result = await websocket.rx()
        if incoming_result.isLeft and isinstance(incoming_result.left, ConnectionClosedError):
            LOGGER.error("Agent error: Control server connection closed: %s", incoming_result.left)
            return 1
        elif incoming_result.isLeft:
            pprint(incoming_result.left)
            LOGGER.error("Agent error: %s", incoming_result.left)
            return 1
        else:
            message = incoming_result.right
            LOGGER.info("Message received: %s", pformat(message, indent=4))
            engine.process(message)
