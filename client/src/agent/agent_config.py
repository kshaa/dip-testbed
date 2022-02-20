"""Module for common functionality between agents"""

from dataclasses import dataclass
from typing import TypeVar, Generic
from src.engine.engine import Engine
from src.service.ws import SocketInterface

PI = TypeVar('PI')
PO = TypeVar('PO')
S = TypeVar('S')
E = TypeVar('E')
X = TypeVar('X')


# Generic client config
@dataclass(frozen=True)
class AgentConfig(Generic[PI, PO]):
    """Common i.e. microcontroller-non-specific agent configuration options"""
    engine: Engine[PI, PO, S, E, X]
    socket: SocketInterface[PI, PO]
