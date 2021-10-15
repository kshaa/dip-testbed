"""Module for common functionality between agents"""

import tempfile
import urllib.request
import urllib.parse
from dataclasses import dataclass
from urllib.parse import ParseResult
from uuid import UUID
from result import Result, Ok, Err


# Generic agent config
@dataclass(frozen=True, eq=False)
class AgentConfig:
    """Common i.e. microcontroller-non-specific agent configuration options"""
    hardware_id: UUID
    control_server: ParseResult
    static_server: ParseResult

    def hardware_control_url(self) -> Result[str, str]:
        """Build hardware control server URL"""
        hardware_control_sever_result = \
            url_with_path(self.control_server, f"/api/v1/hardware/{self.hardware_id}/control")
        if isinstance(hardware_control_sever_result, Err):
            return Err("URL appending failed: %s")
        hardware_control_sever_str_result = \
            unparse_url(hardware_control_sever_result.value)
        if isinstance(hardware_control_sever_str_result, Err):
            return Err("URL serialization failed: %s")
        return Ok(hardware_control_sever_str_result.value)

    def software_url(self, software_id: UUID) -> Result[str, str]:
        """Build software download URL"""
        software_url_result = \
            url_with_path(self.static_server, f"/api/v1/software/{software_id}/download")
        if isinstance(software_url_result, Err):
            return Err("URL appending failed: %s")
        software_server_str_result = \
            unparse_url(software_url_result.value)
        if isinstance(software_server_str_result, Err):
            return Err("URL serialization failed: %s")
        return Ok(software_server_str_result.value)


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


# URL downloads
def download_temp_file(url: str) -> Result[str, str]:
    """Download temporary file and return file path"""
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        urllib.request.urlretrieve(url, tmp.name)
        return Ok(tmp.name)
    except Exception as e:
        return Err(f"Failed to download file: {e}")


def download_temp_software(agent_config: AgentConfig, software_id: UUID) -> Result[str, str]:
    """Download temporary software file and return its file path"""
    url_result = agent_config.software_url(software_id)
    if isinstance(url_result, Err):
        return Err(f"Couldn't construct URL: {url_result.value}")
    file_result = download_temp_file(url_result.value)
    if isinstance(file_result, Err):
        return Err(f"Failed download: {file_result.value}")
    return Ok(file_result.value)
