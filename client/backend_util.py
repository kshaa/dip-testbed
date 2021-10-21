"""Module for functionality related to backend"""

from typing import Optional, List, TypeVar, Callable
from dataclasses import dataclass
from urllib.parse import ParseResult
from uuid import UUID
from result import Result, Ok, Err
from requests import Response
import requests
import protocol
import s11n
from url import url_with_path_str, download_temp_file, response_log_text
import log
from backend_domain import User
from codec import CodecParseException
from protocol import SuccessMessage, FailureMessage

LOGGER = log.timed_named_logger("backend_util")


# Generic client config
@dataclass(frozen=True, eq=False)
class BackendConfig:
    """Backend related config"""
    api_version = "v1"
    api_prefix = f"/api/{api_version}"
    control_server: Optional[ParseResult]
    static_server: Optional[ParseResult]

    # Generic responses
    SUCCESS_CONTENT = TypeVar('SUCCESS_CONTENT')

    @staticmethod
    def response_to_result(
            response: Response,
            success_decode: Callable[[str], Result[SUCCESS_CONTENT, CodecParseException]]
    ) -> Result[FailureMessage, SuccessMessage]:
        """Attempt to parse request response as a JSON failure or success"""
        # Handle failure
        if not response.ok:
            failure_decode = s11n.failure_message_decoder(s11n.string_decode)
            failure_result = failure_decode(response.text)
            if isinstance(failure_result, Err):
                return Err(FailureMessage(f"HTTP error reason: {response.reason}"))
            else:
                return Err(failure_result.value)

        # Handle success
        success_result = success_decode(response.text)
        if isinstance(success_result, Err):
            return Err(f"Failed to parse successful response: {success_result.value}")
        else:
            return Ok(success_result.value)

    # Users
    def user_list(self) -> Result[List[User], str]:
        """Fetch a list of users"""
        # Build URL
        user_list_url_result = url_with_path_str(self.static_server, f"{self.api_prefix}/user")
        if isinstance(user_list_url_result, Err):
            return Err("User list URL build failed: %s")
        user_list_url = user_list_url_result.value

        # Send request
        user_list_response = requests.get(user_list_url)
        LOGGER.debug(response_log_text(user_list_response))
        if not user_list_response.ok:
            return Err(f"Request failure: {user_list_response.reason}")

        # Handle failure
        result = self.response_to_result(
            user_list_response,
            s11n.success_message_decoder(s11n.list_decoder(s11n.user_decode))
        )
        if isinstance(result, Err):
            return Err(result.value.value)
        else:
            return Ok(result.value.value)

    def user_create(self, username: str, password: str) -> Result[List[User], str]:
        """Create a new user"""
        # Build URL
        user_create_url_result = url_with_path_str(self.static_server, f"{self.api_prefix}/user")
        if isinstance(user_create_url_result, Err):
            return Err("User creation URL build failed: %s")
        user_create_url = user_create_url_result.value

        # Send request
        payload = protocol.CreateUserMessage(username, password)
        payload_serialized = s11n.CREATE_USER_MESSAGE_ENCODER.transform(payload)
        user_create_response = requests.post(user_create_url, payload_serialized, headers={
            "Content-type": "application/json"
        })
        LOGGER.debug(response_log_text(user_create_response))

        # Handle failure
        result = self.response_to_result(
            user_create_response,
            s11n.success_message_decoder(s11n.user_decode))
        if isinstance(result, Err):
            return Err(result.value.value)
        else:
            return Ok(result.value.value)

    # Hardware
    def hardware_control_url(self, hardware_id: str) -> Result[str, str]:
        """Build hardware control server URL"""
        if self.control_server is None:
            return Err("User list URL build failed: Control server is not defined")
        hardware_control_sever_result = url_with_path_str(
            self.control_server,
            f"{self.api_prefix}/hardware/{hardware_id}/control")
        if isinstance(hardware_control_sever_result, Err):
            return Err(f"Hardware control URL build failed: {hardware_control_sever_result.value}")
        return Ok(hardware_control_sever_result.value)

    # Software
    def software_download_url(self, software_id: UUID) -> Result[str, str]:
        """Build software download URL"""
        if self.static_server is None:
            return Err("User list URL build failed: Static server is not defined")
        software_url_result = url_with_path_str(
            self.static_server,
            f"{self.api_prefix}/software/{software_id}/download")
        if isinstance(software_url_result, Err):
            return Err(f"Software URL build failed: {software_url_result.value}")
        return Ok(software_url_result.value)

    def download_temp_software(self, software_id: UUID) -> Result[str, str]:
        """Download temporary software file and return its file path"""
        url_result = self.software_download_url(software_id)
        if isinstance(url_result, Err):
            return Err(f"Couldn't construct URL: {url_result.value}")
        file_result = download_temp_file(url_result.value)
        if isinstance(file_result, Err):
            return Err(f"Failed download: {file_result.value}")
        return Ok(file_result.value)
