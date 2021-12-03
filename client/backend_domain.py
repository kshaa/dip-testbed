"""Module for functionality related to backend"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, eq=False)
class User:
    """Class containing user information"""
    id: UUID
    username: str


@dataclass(frozen=True, eq=False)
class Hardware:
    """Class containing hardware information"""
    id: UUID
    name: str
    owner_id: UUID


@dataclass(frozen=True, eq=False)
class Software:
    """Class containing software information"""
    id: UUID
    name: str
    owner_id: UUID
