"""Module containing Python-to-rich serialization logic"""
from dataclasses import dataclass
from typing import TypeVar, Generic, Tuple, List
from rich.table import Table

from src.domain.backend_entity import Hardware, User, Software

A = TypeVar("A")

@dataclass
class RichEncoder(Generic[A]):
    """Marker class for rich encoders"""

    @staticmethod
    def toRow(value: A) -> Tuple:
        pass

    @staticmethod
    def toTable(values: List[A]) -> Table:
        pass


@dataclass
class RichHardwareEncoder(RichEncoder[Hardware]):
    @staticmethod
    def toRow(value: Hardware) -> Tuple[str, str, str]:
        return str(value.id.value), value.name, str(value.owner_id.value)

    @staticmethod
    def toTable(values: List[Hardware]) -> Table:
        table = Table("Id", "Name", "Owner id", title="Hardware list")
        for value in values:
            table.add_row(*RichHardwareEncoder.toRow(value))
        return table


@dataclass
class RichSoftwareEncoder(RichEncoder[Hardware]):
    @staticmethod
    def toRow(value: Software) -> Tuple[str, str, str]:
        return str(value.id.value), value.name, str(value.owner_id.value)

    @staticmethod
    def toTable(values: List[Software]) -> Table:
        table = Table("Id", "Name", "Owner id", title="Software list")
        for value in values:
            table.add_row(*RichSoftwareEncoder.toRow(value))
        return table


@dataclass
class RichUserEncoder(RichEncoder[Hardware]):
    @staticmethod
    def toRow(value: User) -> Tuple[str, str]:
        return str(value.id.value), value.username

    @staticmethod
    def toTable(values: List[User]) -> Table:
        table = Table("Id", "Username", title="User list")
        for value in values:
            table.add_row(*RichUserEncoder.toRow(value))
        return table
