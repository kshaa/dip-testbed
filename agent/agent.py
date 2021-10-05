#!/usr/bin/env python

from websockets.exceptions import ConnectionClosedError
from ws import WebSocket
from protocol import *
from pprint import pprint, pformat
from engine import Engine


async def agent() -> int:
    engine: Engine[str, str] = Engine()
    websocket = WebSocket("ws://localhost:12345", identityDecoder, identityEncoder)
    error = await websocket.connect()
    if error.isDefined:
        print(f"Agent error: Couldn't connect to control server: {error.value}")
        return 0

    while True:
        incoming_result = await websocket.rx()
        if incoming_result.isLeft and isinstance(incoming_result.left, ConnectionClosedError):
            print(f"Agent error: Control server connection closed: {incoming_result.left}")
            return 1
        elif incoming_result.isLeft:
            pprint(incoming_result.left)
            print(f"Agent error: {incoming_result.left}")
            return 1
        else:
            message = incoming_result.right
            print(f"Message received: {pformat(message, indent=4)}")
            engine.process(message)
