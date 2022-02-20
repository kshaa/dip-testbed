from typing import TypeVar

A = TypeVar('A')

async def async_identity(value: A):
    return value