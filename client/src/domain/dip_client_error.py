"""Module for marking common DIP client errors"""
from dataclasses import dataclass
from typing import Any


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


# Sweet god, this is an insane hack, I know
# an error which actually is used for a success value....
#
# Lets see how this bites me back some day
@dataclass
class NotAnError(DIPClientError):
    success_value: Any

    def text(self) -> str:
        return self.success_value

