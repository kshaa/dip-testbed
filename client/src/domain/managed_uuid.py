#!/usr/bin/env python
"""Safe UUID wrapper."""
import dataclasses
from dataclasses import dataclass
from typing import Optional
from uuid import UUID
from result import Result, Err, Ok
from src.domain.dip_client_error import DIPClientError


@dataclass
class ManagedUUIDBuildError(DIPClientError):
    source_value: str
    exception: Exception
    type: Optional[str] = None

    def text(self):
        clarification = f" for '{self.type}'" if self.type is None else ""
        return f"Invalid UUID value '{self.source_value}'{clarification}, reason: {str(self.exception)}"

    def of_type(self, type: str) -> 'ManagedUUIDBuildError':
        return dataclasses.replace(self, type=type)


@dataclass
class ManagedUUID:
    value: UUID

    @staticmethod
    def build(value: str) -> Result['ManagedUUID', ManagedUUIDBuildError]:
        try:
            return Ok(ManagedUUID(UUID(value)))
        except Exception as e:
            return Err(ManagedUUIDBuildError(value, e))

