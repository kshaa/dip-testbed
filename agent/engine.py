#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""

from typing import TypeVar, Generic

PI = TypeVar('PI')
PO = TypeVar('PO')


class Engine(Generic[PI, PO]):
    """Implementation of microcontroller-specific agent logic"""

    def __init__(self):
        pass

    def process(self, message: PI):
        """Consume server-sent message and react accordingly"""
