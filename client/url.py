"""Module for common functionality for URLs"""

from typing import Optional
import tempfile
import urllib.request
import urllib.parse
from urllib.parse import ParseResult
from result import Result, Ok, Err
from requests import Response


# URL manipulations
def parse_url(value: str) -> Result[ParseResult, Exception]:
    """Parse string as a URL"""
    try:
        return Ok(urllib.parse.urlparse(value))
    except Exception as e:
        return Err(e)


def unparse_url(value: ParseResult) -> Result[str, Exception]:
    """Encode URL into a string"""
    try:
        return Ok(value.geturl())
    except Exception as e:
        return Err(e)


def url_with_path(url: Optional[ParseResult], with_path: str) -> Result[ParseResult, Exception]:
    """Append an additional string path to a parsed URL"""
    if url is None:
        return Err("Base URL is not defined")
    try:
        return Ok(url._replace(path=with_path))
    except Exception as e:
        return Err(e)


def url_with_path_str(url: Optional[ParseResult], with_path: str) -> Result[str, str]:
    """Append an additional string path to a URL and convert to string"""
    url_result = url_with_path(url, with_path)
    if isinstance(url_result, Err):
        return Err("URL appending failed: %s")
    url_str_result = unparse_url(url_result.value)
    if isinstance(url_str_result, Err):
        return Err("URL serialization failed: %s")
    return Ok(url_str_result.value)


# URL downloads
def download_temp_file(url: str) -> Result[str, str]:
    """Download temporary file and return file path"""
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        urllib.request.urlretrieve(url, tmp.name)
        return Ok(tmp.name)
    except Exception as e:
        return Err(f"Failed to download file: {e}")


# Request responses
def response_log_text(response: Response) -> str:
    """Serialize response content to text"""
    return f"Status code: {response.status_code}, " \
           f"reason: {response.reason}, " \
           f"headers: {response.headers}, " \
           f"text result: {response.text}"
