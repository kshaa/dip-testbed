import asyncio
from dataclasses import dataclass
from typing import Any, Callable, Optional
from src.agent.agent_error import AgentExecutionError
from src.domain.death import Death


@dataclass
class ManagedQueue:
    queue: asyncio.Queue
    before_put: Optional[Any]
    before_get: Optional[Any]

    def __str__(self):
        return f"ManagedQueue(...)"

    def __repr__(self):
        return self.__str__()

    @staticmethod
    def build(
        before_put: Optional[Callable[[Any], type(None)]] = None,
        before_get: Optional[Callable[[], type(None)]] = None
    ):
        return ManagedQueue(asyncio.Queue(), before_put, before_get)

    async def put(self, value):
        if self.before_put is not None:
            self.before_put(value)
        return await self.queue.put(value)

    async def get(self):
        if self.before_get is not None:
            self.before_get()
        return await self.queue.get()


@dataclass
class EngineBase:
    death: Death[AgentExecutionError]
    incoming_message_queue: ManagedQueue
    outgoing_message_queue: ManagedQueue
    event_queue: ManagedQueue

    @staticmethod
    async def build() -> 'EngineBase':
        return EngineBase(
            Death(),
            ManagedQueue.build(),
            ManagedQueue.build(),
            ManagedQueue.build())


@dataclass
class EngineState:
    base: Optional[EngineBase]
