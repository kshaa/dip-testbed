#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""
import asyncio
from dataclasses import dataclass
from typing import TypeVar, Generic, List, Optional, Callable, Awaitable
from result import Result, Err, Ok
from src.agent.agent_error import AgentExecutionError
from src.domain.dip_client_error import DIPClientError
from src.domain.hardware_control_message import InternalStartLifecycle, InternalEndLifecycle
from src.engine.engine_state import EngineState
from src.util import log


LOGGER = log.timed_named_logger("engine")
PI = TypeVar('PI')
PO = TypeVar('PO')
S = TypeVar('S', bound=EngineState)
E = TypeVar('E')
X = TypeVar('X')


@dataclass
class Engine(Generic[PI, PO, S, E, X]):
    """Engine that receives events, modifies state and executes side-effects"""
    state: S

    async def run(self) -> Result[type(None), Optional[AgentExecutionError]]:
        await self.state.base.incoming_message_queue.put(InternalStartLifecycle())
        await self.loop()
        return self.state.base.death.reason

    async def kill(self, reason: Optional[DIPClientError]):
        await self.state.base.incoming_message_queue.put(InternalEndLifecycle(reason))

    async def loop_messages(self):
        while not self.state.base.death.gracing:
            # Wait for new message
            death_or_incoming_message = await self.state.base.death.or_awaitable(
                self.state.base.incoming_message_queue.get())

            # Handle potential death
            if isinstance(death_or_incoming_message, Err):
                return

            # Handle incoming message
            incoming_message: PI = death_or_incoming_message.value
            await self.process_message(self.state, incoming_message)

    async def loop_events(self):
        while not self.state.base.death.gracing:
            # Wait for new message
            death_or_incoming_event = await self.state.base.death.or_awaitable(
                self.state.base.event_queue.get())

            # Handle potential death
            if isinstance(death_or_incoming_event, Err):
                return

            # Handle incoming event
            event: E = death_or_incoming_event.value
            await self.process_event(event)

    async def loop(self):
        """Keep listening to messages while alive and process them"""
        while not self.state.base.death.gracing:
            # Start message and event processing
            asyncio.create_task(self.loop_messages())
            asyncio.create_task(self.loop_events())

            # Wait for engine death
            await self.state.base.death.wait()

    async def process(self, message: PI):
        """Consume server-sent message and react accordingly"""
        # Convert message into an exception or new events
        result = self.process_message(self.state, message)

        # Handle exception
        if isinstance(result, Err):
            LOGGER.error(f"Message {message} resulted in an error: ${result.value}")
            await self.error_project(result.value)

        # Handle events (project into states and effects)
        events = result.value
        for event in events:
            await self.process_event(event)

    async def pre_process_message(self, previous_state: S, message: PI):
        pass

    async def process_message(self, previous_state: S, message: PI):
        # Pre-process message
        await self.pre_process_message(previous_state, message)

        # Transform into events or exception
        message_result = self.message_project(previous_state, message)

        # Handle exception
        if isinstance(message_result, Err):
            await self.process_error(message_result.value)

        # Send events into queue
        events = message_result.value
        for event in events:
            await self.state.base.event_queue.put(event)

    async def pre_process_event(self, previous_state: S, event: PI):
        pass

    async def process_event(self, event: E):
        # Pre-process event
        await self.pre_process_event(self.state, event)

        # Calculate and store new state
        previous_state = self.state
        new_state = self.state_project(previous_state, event)
        self.state = new_state

        # Execute side effects
        await self.effect_project(previous_state, event)

    def pre_process_error(self, exception: Exception):
        pass

    async def process_error(self, exception: Exception):
        pass

    @staticmethod
    def message_project(previous_state: S, message: PI) -> Result[List[E], Exception]:
        pass

    @staticmethod
    def state_project(previous_state: S, event: E) -> S:
        pass

    async def effect_project(self, previous_state: S, event: E):
        pass

    async def error_project(self, exception: Exception):
        pass

    @staticmethod
    def multi_message_project(
        handlers: List[Callable[[S, PI], Result[List[E], DIPClientError]]],
        previous_state: S,
        message: PI
    ) -> Result[List[E], DIPClientError]:
        events = []
        for handler in handlers:
            result = handler(previous_state, message)
            if isinstance(result, Err): return Err(result.value)
            if isinstance(result.value, list): events.extend(result.value)
        return Ok(events)

    @staticmethod
    async def multi_effect_project(
        handlers: List[Callable[[S, E], Awaitable[type(None)]]],
        previous_state: S,
        event: E
    ):
        for handler in handlers:
            asyncio.create_task(handler(previous_state, event))
