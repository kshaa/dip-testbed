#!/usr/bin/env python

from websockets.exceptions import ConnectionClosedError
from ws import WebSocket
from codec import *
from pprint import pprint, pformat
from engine import Engine
import log

logger = log.timed_named_logger("agent")


async def agent() -> int:
    engine: Engine[str, str] = Engine()
    control_server = "ws://localhost:12345"
    websocket = WebSocket(control_server, identityDecoder, identityEncoder)
    logger.debug(f"Connecting connect to control server: {control_server}")
    error = await websocket.connect()
    if error.isDefined:
        logger.error(f"Couldn't connect to control server: {error.value}")
        return 0

    logger.info(f"Connected to control server, listening for commands")

    while True:
        incoming_result = await websocket.rx()
        if incoming_result.isLeft and isinstance(incoming_result.left, ConnectionClosedError):
            logger.error(f"Agent error: Control server connection closed: {incoming_result.left}")
            return 1
        elif incoming_result.isLeft:
            pprint(incoming_result.left)
            logger.error(f"Agent error: {incoming_result.left}")
            return 1
        else:
            message = incoming_result.right
            logger.info(f"Message received: {pformat(message, indent=4)}")
            engine.process(message)
