#!/usr/bin/env python
"""Safe existing filesystem path wrapper."""
import dataclasses
import os
from dataclasses import dataclass
from typing import Optional
from result import Result, Ok, Err
from src.domain.dip_client_error import DIPClientError


@dataclass
class ManagedExistingFilePathBuildError(DIPClientError):
    source_value: str
    type: Optional[str] = None

    def text(self):
        clarification = f" for '{self.type}'" if self.type is None else ""
        return f"File path '{self.source_value}'{clarification} does not exist."

    def of_type(self, type: str) -> 'ManagedExistingFilePathBuildError':
        return dataclasses.replace(self, type=type)


@dataclass(frozen=True)
class ExistingFilePath:
    value: str

    @staticmethod
    def build(value: str) -> Result['ExistingFilePath', ManagedExistingFilePathBuildError]:
        if not os.path.exists(value):
            return Err(ManagedExistingFilePathBuildError(value))
        return Ok(ExistingFilePath(value))
