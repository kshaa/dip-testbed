#!/usr/bin/env python

from typing import TypeVar, Generic

PI = TypeVar('PI')
PO = TypeVar('PO')


class Engine(Generic[PI, PO]):
    def __init__(self):
        pass

    def process(self, message: PI):
        pass
