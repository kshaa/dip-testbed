"""Module for common functionality between agents"""

import urllib.parse
from urllib.parse import ParseResult
from result import Ok, Err, Result


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


def url_with_path(url: ParseResult, with_path: str) -> Result[ParseResult, Exception]:
    """Append an additional string path to a parsed URL"""
    try:
        return Ok(url._replace(path=with_path))
    except Exception as e:
        return Err(e)
