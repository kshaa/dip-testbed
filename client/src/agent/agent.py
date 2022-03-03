#!/usr/bin/env python
"""Supervising client, listening to server commands, passing to client-specific agent"""
import asyncio
import signal
from dataclasses import dataclass
from functools import partial
from typing import TypeVar, Optional, Generic
from result import Err
from websockets.exceptions import ConnectionClosedError
from src.agent.agent_config import AgentConfig
from src.agent.agent_error import AgentExecutionError
from src.domain.dip_client_error import GenericClientError
from src.domain.dip_runnable import DIPRunnable
from src.domain.hardware_control_message import log_hardware_message
from src.util import log
from src.protocol.codec import CodecParseException

LOGGER = log.timed_named_logger("agent")
OUTGOING_LOGGER = log.timed_named_logger("outgoing_engine")
PI = TypeVar('PI')
PO = TypeVar('PO')


@dataclass
class Agent(Generic[PI, PO], DIPRunnable):
    """Wrapper for engines to pipe websocket messages"""
    config: AgentConfig[PI, PO]

    async def run(self) -> Optional[AgentExecutionError]:
        """Supervising client, which connects to a websocket, listens
         to commands from server, passes them to an client-specific agent"""

        LOGGER.info("Running async engine agent")
        config = self.config

        # Connect to control
        error = await config.socket.connect()
        if error is not None:
            return AgentExecutionError("Failed connecting to control server", exception=error)

        # Handle lifecycle
        LOGGER.info("Connected to control server, listening for commands, running start hook")
        asyncio.create_task(self.socket_receive())
        asyncio.create_task(self.socket_transmit())
        asyncio.create_task(self.socket_end_on_death())

        # Handle kill signals
        def on_signal(signal: str, *args):
            asyncio.create_task(self.config.engine.kill(GenericClientError(f"Signal '{signal}' received")))
        signal.signal(signal.SIGINT, partial(on_signal, "SIGINT"))
        signal.signal(signal.SIGTERM, partial(on_signal, "SIGTERM"))

        # Run engine until it dies
        return await self.config.engine.run()

    async def socket_end_on_death(self):
        await self.config.engine.state.base.death.wait()
        LOGGER.debug("Closing control server connection")
        await self.config.socket.disconnect()

    async def socket_transmit(self):
        """Redirects agent queue messages into the socket"""
        while self.config.socket.connected() and not self.config.engine.state.base.death.gracing:
            # Wait for new message
            death_or_outgoing_message = await self.config.engine.state.base.death.or_awaitable(
                self.config.engine.state.base.outgoing_message_queue.get())

            # Handle potential death (and stop transmitting)
            if isinstance(death_or_outgoing_message, Err):
                LOGGER.debug(
                    f"Agent stopping transmit loop as death has occurred, reason: {death_or_outgoing_message.value}")
                return

            # Send message
            message = death_or_outgoing_message.value
            log_hardware_message(OUTGOING_LOGGER, message)
            transmission_exception = await self.config.socket.tx(message)

            # Handle transmission error (and stop transmitting)
            if transmission_exception is not None:
                deathly_error = AgentExecutionError("Failed to transmit message", exception=transmission_exception)
                await self.config.engine.kill(deathly_error)
                return

    async def socket_receive(self):
        """Redirects socket messages into the agent queue"""
        while self.config.socket.connected() and not self.config.engine.state.base.death.gracing:
            # Wait for new messages
            try:
                death_or_message = await self.config.engine.state.base.death.or_awaitable(self.config.socket.rx())
            except Exception as e:
                raise e

            # Handle potential death (and stop receiving)
            if isinstance(death_or_message, Err):
                LOGGER.debug(f"Agent stopping receive loop as death has occurred, reason: {death_or_message.value}")
                return

            # Handle connection close (and stop receiving)
            incoming_result = death_or_message.value
            if isinstance(incoming_result, Err) and isinstance(incoming_result.value, ConnectionClosedError):
                deathly_error = AgentExecutionError("Control server connection closed")
                await self.config.engine.kill(deathly_error)
                return

            # Handle unknown message (and continue receiving)
            if isinstance(incoming_result, Err) and isinstance(incoming_result.value, CodecParseException):
                LOGGER.error("Unknown command received, ignoring")
                continue

            # Handle catch-all transmission error (and stop receiving)
            if isinstance(incoming_result, Err):
                deathly_error = AgentExecutionError("Failed to receive message", exception=incoming_result.value)
                await self.config.engine.kill(deathly_error)
                return

            # Handle valid message (and continue receiving)
            message = incoming_result.value
            await self.config.engine.state.base.incoming_message_queue.put(message)
