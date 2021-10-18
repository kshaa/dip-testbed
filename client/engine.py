#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""

from typing import TypeVar, Generic
from result import Result, Err

PI = TypeVar('PI')
PO = TypeVar('PO')


class Engine(Generic[PI, PO]):
    """Implementation of microcontroller-specific client logic"""
    def __init__(self):
        pass

    # W0613: ignore unused message, because this class is abstract
    # R0201: ignore no-self-use, because I want this method here regardless
    # pylint: disable=W0613,R0201
    def process(self, message: PI) -> Result[PO, Exception]:
        """Consume server-sent message and react accordingly"""
        return Err(NotImplementedError())
