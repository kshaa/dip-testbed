"""Synchronization primitive for coroutine-safe process finishing"""
import asyncio
from asyncio import Task, Future
from dataclasses import dataclass
from random import randint
from typing import TypeVar, Coroutine, Optional, Generic, Union
from result import Result, Ok, Err

T = TypeVar('T')


@dataclass
class Death(Generic[T]):
    """Coroutine-safe application death boolean"""
    gracing: bool = False
    reason: Optional[T] = None

    def grace(self, reason: Optional[T] = None):
        self.gracing = True
        self.reason = reason

    async def wait(self) -> 'Death':
        while not self.gracing:
            await asyncio.sleep(0.3)
        return self

    async def or_task(self, content_task: Task) -> Result[T, 'Death']:
        # Wait for any task to finish
        self_task = asyncio.create_task(self.wait())
        done_set, pending_set = await asyncio.wait(
            [self_task, content_task],
            loop=None,
            return_when=asyncio.FIRST_COMPLETED
        )

        # Cancel pending tasks
        if len(pending_set) != 0:
            pending_set.pop().cancel()

        # Return either this death or result
        done_task = done_set.pop()
        done = done_task.result()
        if len(pending_set) != 0 or isinstance(done, Death):
            return Err(self)
        else:
            return Ok(done)

    async def or_awaitable(self, awaitable: Union[Coroutine, Future]) -> Result[T, 'Death']:
        return await self.or_task(asyncio.create_task(awaitable))
