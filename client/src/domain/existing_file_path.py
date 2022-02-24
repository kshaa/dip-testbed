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
    exception: Optional[Exception] = None

    def text(self):
        type_info = f" for '{self.type}'" if self.type is None else ""
        reason_info = f", reason: {str(self.exception)}" if self.exception is not None else ""
        return f"File path '{self.source_value}'{type_info} does not exist{reason_info}"

    def of_type(self, type: str) -> 'ManagedExistingFilePathBuildError':
        return dataclasses.replace(self, type=type)


@dataclass(frozen=True)
class ExistingFilePath:
    value: str

    @staticmethod
    def exists(value: str) -> bool:
        result = ExistingFilePath.build(value)
        return isinstance(result, Ok)

    @staticmethod
    def build(value: str) -> Result['ExistingFilePath', ManagedExistingFilePathBuildError]:
        if not os.path.exists(value):
            return Err(ManagedExistingFilePathBuildError(value))
        return Ok(ExistingFilePath(value))

    @staticmethod
    def new(value: str) -> Result['ExistingFilePath', ManagedExistingFilePathBuildError]:
        try:
            # Create directory path to file
            config_dir = os.path.dirname(value)
            if not ExistingFilePath.exists(config_dir):
                os.makedirs(config_dir)
            # Create and return empty file
            open(value, 'w').close()
            return Ok(ExistingFilePath(value))
        except Exception as e:
            return Err(ManagedExistingFilePathBuildError(value))
