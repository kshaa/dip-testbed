#!/usr/bin/env python
"""Safe non-negative integer."""
import dataclasses
from dataclasses import dataclass
from typing import Optional
from result import Result, Ok, Err
from src.domain.dip_client_error import DIPClientError


@dataclass
class PositiveIntegerBuildError(DIPClientError):
    source_value: int
    type: Optional[str] = None

    def text(self):
        clarification = f" for '{self.type}'" if self.type is None else ""
        return f"Integer '{self.source_value}' {clarification}must be positive"

    def of_type(self, type: str) -> 'PositiveIntegerBuildError':
        return dataclasses.replace(self, type=type)


@dataclass(frozen=True)
class PositiveInteger:
    value: int

    @staticmethod
    def build(value: int) -> Result['PositiveInteger', str]:
        if value <= 0:
            return Err(PositiveIntegerBuildError(value))
        return Ok(PositiveInteger(value))
