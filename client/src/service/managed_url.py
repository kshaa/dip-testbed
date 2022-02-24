#!/usr/bin/env python
"""Module for managing URLs"""
import dataclasses
from dataclasses import dataclass
import tempfile
import urllib.request
import urllib.parse
from typing import Optional
from urllib.parse import ParseResult
from result import Result, Ok, Err
from requests import Response
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath


@dataclass
class ManagedURLBuildError(DIPClientError):
    source_value: str
    exception: Exception
    type: Optional[str] = None

    def text(self):
        clarification = f" for '{self.type}'" if self.type is None else ""
        return f"Invalid URL value '{self.source_value}'{clarification}, reason: {str(self.exception)}"

    def of_type(self, type: str) -> 'ManagedURLBuildError':
        return dataclasses.replace(self, type=type)

@dataclass
class ManagedURL:
    value: ParseResult

    def __str__(self):
        return f"ManagedURL({self.text()})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        """Overrides the default implementation"""
        if isinstance(other, ManagedURL):
            return self.text() == other.text()
        return False

    @staticmethod
    def build(value: str) -> Result['ManagedURL', 'ManagedURLBuildError']:
        try:
            return Ok(ManagedURL(urllib.parse.urlparse(value)))
        except Exception as e:
            return Err(ManagedURLBuildError(value, e))

    def text(self) -> Result[str, Exception]:
        """Encode URL into a string"""
        try:
            return Ok(self.value.geturl())
        except Exception as e:
            return Err(e)

    def with_absolute_path(self, absolute_path: str) -> Result['ManagedURL', Exception]:
        """Append an additional string path to a parsed URL"""
        try:
            copy = dataclasses.replace(self)
            result = copy.value._replace(path=absolute_path)
            return Ok(ManagedURL(result))
        except Exception as e:
            return Err(e)

    def downloaded_file_in_path(self, path: str) -> Result[ExistingFilePath, str]:
        """Download file and return file path"""
        try:
            url_result = self.text()
            if isinstance(url_result, Err):
                return url_result
            url_text: str = url_result.value
            urllib.request.urlretrieve(url_text, path)
            return Ok(ExistingFilePath(path))
        except Exception as e:
            return Err(e)

    def downloaded_file_in_temp(self) -> Result[ExistingFilePath, str]:
        """Download file and return file path"""
        tmp = tempfile.NamedTemporaryFile(delete=False)
        return self.downloaded_file_in_path(tmp.name)

    @staticmethod
    def response_log_text(response: Response) -> str:
        """Serialize response content to text"""
        return f"Status code: {response.status_code}, " \
               f"reason: {response.reason}, " \
               f"headers: {response.headers}, " \
               f"text result: {response.text}"
