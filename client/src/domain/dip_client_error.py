"""Module for marking common DIP client errors"""
from dataclasses import dataclass


@dataclass
class DIPClientError:
    def text(self) -> str:
        """Marker class to mark this as a known DIP error"""
        pass


@dataclass
class GenericClientError(DIPClientError):
    value: str

    def text(self) -> str:
        return self.value

