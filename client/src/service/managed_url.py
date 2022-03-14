#!/usr/bin/env python
"""Module for managing URLs"""
import base64
import dataclasses
from dataclasses import dataclass
import tempfile
import urllib.request
import urllib.parse
from typing import Optional
from urllib.parse import ParseResult
from urllib.request import Request
from result import Result, Ok, Err
from requests import Response
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.util import log

LOGGER = log.timed_named_logger("url")


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

    def with_basic_auth(self, username: str, password: str) -> Result['ManagedURL', Exception]:
        """Append an additional string path to a parsed URL"""
        try:
            copy = dataclasses.replace(self)
            result = copy.value._replace(netloc=f"{username}:{password}@{copy.value.netloc}")
            return Ok(ManagedURL(result))
        except Exception as e:
            return Err(e)

    def downloaded_file_in_path(self, path: str) -> Result[ExistingFilePath, str]:
        """Download file and return file path"""
        try:
            # Don't even comment, I know this is bad, it makes me cry too
            basic_auth_index = self.value.netloc.find("@")
            has_basic_auth = basic_auth_index != -1
            if has_basic_auth:
                basic_auth = self.value.netloc[0:basic_auth_index]
                basic_auth_b64 = base64.b64encode(basic_auth.encode()).decode("utf-8")
                url_without_basic_auth = ManagedURL(self.value._replace(netloc=self.value.netloc[basic_auth_index + 1:]))

                req = Request(url_without_basic_auth.text().value)
                req.add_header("Authorization", f"Basic {basic_auth_b64}")
                with urllib.request.urlopen(req) as url:
                    contents = url.read()
                f = open(path, "wb")
                f.write(contents)
                f.close()
                return Ok(ExistingFilePath(path))
            else:
                url_result = self.text()
                if isinstance(url_result, Err):
                    return url_result
                url_text: str = url_result.value
                LOGGER.debug(f"HTTP download. URL: {url_text}, file: {path}")
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
