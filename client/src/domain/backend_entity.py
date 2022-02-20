"""Module for holding entities used in backend management"""

from dataclasses import dataclass
from typing import Tuple, List, Dict, Any
from rich.table import Table
from src.domain.managed_uuid import ManagedUUID


@dataclass(frozen=True)
class BackendEntity:
    def toRow(self) -> Tuple:
        pass

    @staticmethod
    def toTable(values: List['BackendEntity']) -> Table:
        pass

    def toJSON(self) -> Any:
        pass


@dataclass(frozen=True)
class User(BackendEntity):
    """Class containing user information"""
    id: ManagedUUID
    username: str


@dataclass(frozen=True)
class Hardware(BackendEntity):
    """Class containing hardware information"""
    id: ManagedUUID
    name: str
    owner_id: ManagedUUID


@dataclass(frozen=True)
class Software(BackendEntity):
    """Class containing software information"""
    id: ManagedUUID
    name: str
    owner_id: ManagedUUID
