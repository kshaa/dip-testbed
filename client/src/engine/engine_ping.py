#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""
import asyncio
from asyncio import Task
from dataclasses import dataclass
from typing import TypeVar, Generic, List, Optional, Any
from result import Result, Err

from src.agent.agent_error import AgentExecutionError
from src.domain.death import Death
from src.domain.dip_client_error import DIPClientError
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, PingMessage
from src.domain.positive_integer import PositiveInteger
from src.engine.engine_events import NoisyEvent, FailureEvent, COMMON_ENGINE_EVENT, LifecycleStarted
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

    async def effect_project(self, previous_state: EnginePingState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, LifecycleStarted):
            await self.ping_until_death(
                previous_state.base.death,
                previous_state.heartbeat_seconds,
                previous_state.base.outgoing_message_queue)
