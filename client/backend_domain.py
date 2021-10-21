"""Module for functionality related to backend"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, eq=False)
class User:
    """Class containing user information"""
    id: UUID
    username: str
