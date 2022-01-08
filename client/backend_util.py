"""Module for functionality related to backend"""

from typing import Optional, List, TypeVar, Dict
from dataclasses import dataclass
from urllib.parse import ParseResult
import base64
from uuid import UUID
from result import Result, Ok, Err
from requests import Response
import requests
import protocol
import s11n_util
import s11n_json
import s11n_hybrid
from s11n_json import EncoderJSON, DecoderJSON
from url import url_with_path_str, download_file, download_temp_file, response_log_text
import log
from backend_domain import User, Hardware, Software
from protocol import SuccessMessage, FailureMessage
from ws import WebSocket
from monitor_serial import MonitorSerial

LOGGER = log.timed_named_logger("backend_util")


# Generic client config
@dataclass(frozen=True, eq=False)
class BackendConfig:
    """Backend related config"""
    api_version = "v1"
    api_prefix = f"/api/{api_version}"
    control_server: Optional[ParseResult]
    static_server: Optional[ParseResult]

    # Request headers
    json_headers = {
        "Content-type": "application/json"
    }

    @staticmethod
    def auth_headers(username: str, password: str) -> Dict:
        """Create authentication header"""
        token = base64.b64encode(f"{username}:{password}".encode()).decode("utf-8")
        return {
            "Authentication": f"Basic {token}"
        }

    # Generic responses
    SUCCESS_CONTENT = TypeVar('SUCCESS_CONTENT')
    FAILURE_CONTENT = TypeVar('FAILURE_CONTENT')

    @staticmethod
    def response_to_result(
        response: Response,
        success_decoder: DecoderJSON[SUCCESS_CONTENT],
        empty_success: bool = False
    ) -> Result[SUCCESS_CONTENT, FailureMessage[str]]:
        """Attempt to parse request response as a JSON failure or success"""
        # Handle failure
        if not response.ok:
            failure_decoder = s11n_json.STRING_DECODER_JSON
            failure_result = failure_decoder.raw_decode(response.text)
            if isinstance(failure_result, Err):
                return Err(FailureMessage(f"HTTP error reason: {response.reason}"))
            else:
                return Err(FailureMessage(failure_result.value))

        # Handle success
        success_result = success_decoder.raw_decode(response.text)
        if isinstance(success_result, Err):
            if empty_success:
                return Ok(None)
            else:
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

        # Handle result
        # type: ignore
        users_decoder: DecoderJSON[List[User]] = s11n_util.list_decoder(s11n_json.USER_DECODER_JSON)
        result: Result[SuccessMessage[List[User]], FailureMessage[str]] = self.response_to_result(
            user_list_response,
            s11n_json.success_message_decoder_json(users_decoder))
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
        payload_serialized = s11n_json.CREATE_USER_MESSAGE_ENCODER_JSON.encode(payload)
        user_create_response = requests.post(
            user_create_url,
            EncoderJSON.serializable_as_raw(payload_serialized),
            headers=self.json_headers)
        LOGGER.debug(response_log_text(user_create_response))

        # Handle result
        result = self.response_to_result(
            user_create_response,
            s11n_json.success_message_decoder_json(
                s11n_json.USER_DECODER_JSON))
        if isinstance(result, Err):
            return Err(result.value.value)
        else:
            return Ok(result.value.value)

    # Hardware
    def hardware_list(self) -> Result[List[Hardware], str]:
        """Fetch a list of hardware"""
        # Build URL
        hardware_list_url_result = url_with_path_str(self.static_server, f"{self.api_prefix}/hardware")
        if isinstance(hardware_list_url_result, Err):
            return Err("Hardware list URL build failed: %s")
        hardware_list_url = hardware_list_url_result.value

        # Send request
        hardware_list_response = requests.get(hardware_list_url)
        LOGGER.debug(response_log_text(hardware_list_response))
        if not hardware_list_response.ok:
            return Err(f"Request failure: {hardware_list_response.reason}")

        # Handle result
        # type: ignore
        hardwares_decoder: DecoderJSON[List[Hardware]] = \
            s11n_util.list_decoder(s11n_json.HARDWARE_DECODER_JSON)
        result = self.response_to_result(
            hardware_list_response,
            s11n_json.success_message_decoder_json(hardwares_decoder)
        )
        if isinstance(result, Err):
            return Err(result.value.value)
        else:
            return Ok(result.value.value)

    def hardware_create(self, username: str, password: str, hardware_name: str) -> Result[Hardware, str]:
        """Create a new hardware"""
        # Build URL
        hardware_create_url_result = url_with_path_str(self.static_server, f"{self.api_prefix}/hardware")
        if isinstance(hardware_create_url_result, Err):
            return Err("Hardware creation URL build failed: %s")
        hardware_create_url = hardware_create_url_result.value

        # Send request
        payload = protocol.CreateHardwareMessage(hardware_name)
        payload_serialized = s11n_json.CREATE_HARDWARE_MESSAGE_ENCODER_JSON.encode(payload)
        request_headers = dict(self.json_headers, **self.auth_headers(username, password))
        hardware_create_response = requests.post(
            hardware_create_url,
            EncoderJSON.serializable_as_raw(payload_serialized),
            headers=request_headers)
        LOGGER.debug(response_log_text(hardware_create_response))

        # Handle result
        result = self.response_to_result(
            hardware_create_response,
            s11n_json.success_message_decoder_json(
                s11n_json.HARDWARE_DECODER_JSON))
        if isinstance(result, Err):
            return Err(result.value.value)
        else:
            return Ok(result.value.value)

    def hardware_control_url(self, hardware_id: UUID) -> Result[str, str]:
        """Build hardware control server URL"""
        if self.control_server is None:
            return Err("User list URL build failed: Control server is not defined")
        hardware_control_sever_result = url_with_path_str(
            self.control_server,
            f"{self.api_prefix}/hardware/{hardware_id}/control")
        if isinstance(hardware_control_sever_result, Err):
            return Err(f"Hardware control URL build failed: {hardware_control_sever_result.value}")
        return Ok(hardware_control_sever_result.value)

    def hardware_software_upload(
        self,
        hardware_id: UUID,
        software_id: UUID
    ) -> Result[None, str]:
        """Upload a given software to a given hardware"""
        # Build URL
        hardware_software_upload_url_result = url_with_path_str(
            self.static_server,
            f"{self.api_prefix}/hardware/{hardware_id}/upload/software/{software_id}")
        if isinstance(hardware_software_upload_url_result, Err):
            return Err("Hardware software upload URL build failed: %s")
        hardware_software_upload_url = hardware_software_upload_url_result.value

        # Send request
        hardware_create_response = requests.post(hardware_software_upload_url)
        LOGGER.debug(response_log_text(hardware_create_response))

        # Handle result
        result = self.response_to_result(
            hardware_create_response,
            s11n_json.success_message_decoder_json(
                s11n_json.HARDWARE_DECODER_JSON),
            empty_success=True)
        if isinstance(result, Err):
            return Err(result.value.value)
        else:
            return Ok(None)

    # Software
    def software_list(self) -> Result[List[Software], str]:
        """Fetch a list of software"""
        # Build URL
        software_list_url_result = url_with_path_str(self.static_server, f"{self.api_prefix}/software")
        if isinstance(software_list_url_result, Err):
            return Err("Software list URL build failed: %s")
        software_list_url = software_list_url_result.value

        # Send request
        software_list_response = requests.get(software_list_url)
        LOGGER.debug(response_log_text(software_list_response))
        if not software_list_response.ok:
            return Err(f"Request failure: {software_list_response.reason}")

        # Handle result
        # type: ignore
        softwares_decoder: DecoderJSON[List[Software]] = s11n_util.list_decoder(s11n_json.SOFTWARE_DECODER_JSON)
        result = self.response_to_result(
            software_list_response,
            s11n_json.success_message_decoder_json(softwares_decoder))
        if isinstance(result, Err):
            return Err(result.value.value)
        else:
            return Ok(result.value.value)

    def software_upload(
        self,
        username: str,
        password: str,
        software_name: str,
        file_path: str
    ) -> Result[Software, str]:
        """Upload a new software"""
        # Build URL
        software_upload_url_result = url_with_path_str(self.static_server, f"{self.api_prefix}/software")
        if isinstance(software_upload_url_result, Err):
            return Err("Software upload URL build failed: %s")
        software_upload_url = software_upload_url_result.value

        # Send request
        headers = self.auth_headers(username, password)
        files = {'software': open(file_path, 'rb')}
        values = {'name': software_name}
        software_upload_response = \
            requests.post(software_upload_url, files=files, data=values, headers=headers)
        LOGGER.debug(response_log_text(software_upload_response))

        # Handle result
        result = self.response_to_result(
            software_upload_response,
            s11n_json.success_message_decoder_json(s11n_json.SOFTWARE_DECODER_JSON))
        if isinstance(result, Err):
            return Err(result.value.value)
        else:
            return Ok(result.value.value)

    def software_download(self, software_id: UUID, file_path: str) -> Result[str, str]:
        """Download temporary software file and return its file path"""
        # Build URL
        software_upload_url_result = url_with_path_str(
            self.static_server,
            f"{self.api_prefix}/software/{software_id}/download")
        if isinstance(software_upload_url_result, Err):
            return Err("Software upload URL build failed: %s")
        software_upload_url = software_upload_url_result.value

        # Send request
        file_result = download_file(software_upload_url, file_path)
        if isinstance(file_result, Err):
            return Err(f"Failed download: {file_result.value}")
        return Ok(file_result.value)

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

    async def hardware_serial_monitor(self, hardware_id: UUID, monitor_serial: MonitorSerial):
        # Build URL
        monitor_url_result = url_with_path_str(
            self.control_server,
            f"{self.api_prefix}/hardware/{hardware_id}/monitor/serial")
        if isinstance(monitor_url_result, Err):
            return Err("Hardware serial monitor URL build failed: %s")
        monitor_url = monitor_url_result.value

        # Connect to hardware listener in backend control
        decoder = s11n_hybrid.MONITOR_LISTENER_INCOMING_MESSAGE_DECODER
        encoder = s11n_hybrid.MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER
        websocket = WebSocket(monitor_url, decoder, encoder)
        LOGGER.debug("Connecting connect to control server: %s", monitor_url)
        error = await websocket.connect()
        if error is not None:
            return Err(f"Couldn't connect to control server: {error}")

        # Start monitor handler
        await monitor_serial.run(websocket)
