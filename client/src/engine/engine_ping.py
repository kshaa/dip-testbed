#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""
import asyncio
from dataclasses import dataclass
from typing import TypeVar, Any
from result import Err
from src.domain.death import Death
from src.domain.hardware_shared_event import LifecycleStarted
from src.domain.hardware_shared_message import PingMessage
from src.domain.positive_integer import PositiveInteger
from src.engine.engine_state import EngineState, ManagedQueue, EngineBase
from src.util import log


LOGGER = log.timed_named_logger("agent")
PI = TypeVar('PI')
PO = TypeVar('PO')
S = TypeVar('S', bound=EngineState)
E = TypeVar('E')


class EnginePingState:
    base: EngineBase
    heartbeat_seconds: PositiveInteger


@dataclass
class EnginePing:
    @staticmethod
    async def ping_until_death(
        death: Death,
        heartbeat_seconds: PositiveInteger,
        out_queue: ManagedQueue
    ):
        while not death.gracing:
            # Wait for death or ping timeout
            death_or_ping_timeout = await death.or_awaitable(asyncio.sleep(heartbeat_seconds.value))
            # Handle potential death (and stop pinging)
            if isinstance(death_or_ping_timeout, Err):
                return
            # Ping and repeat
            await out_queue.put(PingMessage())

    async def effect_project(self, previous_state: EnginePingState, event: Any):
        if isinstance(event, LifecycleStarted):
            await self.ping_until_death(
                previous_state.base.death,
                previous_state.heartbeat_seconds,
                previous_state.base.outgoing_message_queue)
