"""Module for backend management service definitions"""
import os
import urllib.request
from typing import List, TypeVar, Dict, Optional
from dataclasses import dataclass
import base64
from uuid import UUID
from result import Result, Ok, Err
from requests import Response
import requests
from src.domain.backend_management_message import CreateUserMessage, CreateHardwareMessage, SuccessMessage, \
    FailureMessage
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.protocol.codec import CodecParseException
from src.protocol.codec_json import DecoderJSON, EncoderJSON
from src.service.backend_config import BackendConfig
from src.service.managed_url import ManagedURL
from src.util import log
from src.domain.backend_entity import User, Hardware, Software
from src.protocol import s11n_json

LOGGER = log.timed_named_logger("backend")
FETCH_CONTENT = TypeVar('FETCH_CONTENT')
SEND_CONTENT = TypeVar('SEND_CONTENT')


@dataclass
class BackendManagementError(DIPClientError):
    title: str
    reason: Optional[str] = None
    exception: Optional[Exception] = None
    error: Optional[DIPClientError] = None

    def text(self):
        clarification = f", reason: {self.error.text()}" if self.error is not None \
            else f", reason: {str(self.reason)}" if self.reason is not None \
            else f", reason: {str(self.exception)}" if self.exception is not None \
            else ""
        return f"Backend management error '{self.title}'{clarification}"


@dataclass
class BackendServiceInterface:
    """Generic interface for backend management service"""
    config: BackendConfig

    # URLs
    def static_url(self, path: str) -> Result[ManagedURL, BackendManagementError]:
        pass

    def control_url(self, path: str) -> Result[ManagedURL, BackendManagementError]:
        pass

    def hardware_control_url(self, hardware_id: ManagedUUID) -> Result[ManagedURL, BackendManagementError]:
        pass

    def hardware_video_source_url(self, hardware_id: ManagedUUID) -> Result[ManagedURL, BackendManagementError]:
        pass

    def hardware_serial_monitor_url(self, hardware_id: ManagedUUID) -> Result[ManagedURL, BackendManagementError]:
        pass

    # User
    def auth_check(self) -> Optional[DIPClientError]:
        pass

    def user_list(self) -> Result[List[User], BackendManagementError]:
        pass

    def user_create(self, username: str, password: str) -> Result[List[User], BackendManagementError]:
        pass

    # Hardware
    def hardware_list(self) -> Result[List[Hardware], BackendManagementError]:
        pass

    def hardware_create(
        self,
        hardware_name: str
    ) -> Result[Hardware, BackendManagementError]:
        pass

    def hardware_software_upload(self, hardware_id: UUID, software_id: UUID) -> Result[None, BackendManagementError]:
        pass

    # Software
    def software_list(self) -> Result[List[Software], BackendManagementError]:
        pass

    def software_upload(
        self,
        file_path: str,
        software_name: str
    ) -> Result[Software, BackendManagementError]:
        pass

    def software_download(
        self,
        software_id: ManagedUUID,
        file_path: Optional[str] = None
    ) -> Result[ExistingFilePath, BackendManagementError]:
        pass


@dataclass
class BackendService(BackendServiceInterface):
    """Backend service implementation"""

    json_headers = {
        "Content-type": "application/json"
    }
    auth_error = GenericClientError("Authentication data required")

    def static_url(self, path: str) -> Result[ManagedURL, BackendManagementError]:
        if self.config.static_server is None: return Err(BackendManagementError("Missing static server URL"))
        url_result = self.config.static_server.with_absolute_path(path)
        if isinstance(url_result, Err):
            return Err(BackendManagementError("Static server URL build failed", exception=url_result.value))
        return Ok(url_result.value)

    def control_url(self, path: str) -> Result[ManagedURL, BackendManagementError]:
        if self.config.control_server is None: return Err(BackendManagementError("Missing control server URL"))
        url_result = self.config.control_server.with_absolute_path(path)
        if isinstance(url_result, Err):
            return Err(BackendManagementError("Control server URL build failed", exception=url_result.value))
        return Ok(url_result.value)

    def hardware_control_url(self, hardware_id: ManagedUUID) -> Result[ManagedURL, BackendManagementError]:
        """Build hardware control server URL"""
        return self.control_url(f"{self.config.api_prefix}/hardware/{hardware_id.value}/control")

    def hardware_video_source_url(self, hardware_id: ManagedUUID) -> Result[ManagedURL, BackendManagementError]:
        return self.control_url(f"{self.config.api_prefix}/hardware/video/source?hardware={hardware_id.value}")

    def hardware_video_sink_url(self, hardware_id: ManagedUUID) -> Result[ManagedURL, BackendManagementError]:
        url_result = self.static_url(f"{self.config.api_prefix}/hardware/video/sink/{hardware_id.value}.ogg")
        if isinstance(url_result, Err):
            return Err(BackendManagementError("Control server URL build failed", exception=url_result.value))
        return url_result.value.with_basic_auth(self.config.auth.username, self.config.auth.password) # Bad hack

    def hardware_serial_monitor_url(self, hardware_id: ManagedUUID) -> Result[ManagedURL, BackendManagementError]:
        """Build hardware serial monitor URL"""
        return self.control_url(f"{self.config.api_prefix}/hardware/{hardware_id.value}/monitor/serial")

    @staticmethod
    def response_to_result(
        response: Response,
        content_decoder: Optional[DecoderJSON[FETCH_CONTENT]],
    ) -> Result[FETCH_CONTENT, BackendManagementError]:
        """Attempt to parse request response as a JSON failure or success"""
        # Handle failure
        if not response.ok:
            # Parse failure response
            failure_result: Result[FailureMessage[str], CodecParseException] = \
                s11n_json.failure_message_decoder_json(s11n_json.STRING_DECODER_JSON).decode(response.text)
            if isinstance(failure_result, Err):
                return Err(BackendManagementError("HTTP error", reason=response.reason))
            return Err(BackendManagementError("Backend error response", reason=failure_result.value.value))

        # Handle empty success
        if content_decoder is None: return Ok(None)

        # Parse success response
        content_result: Result[SuccessMessage[FETCH_CONTENT], CodecParseException] = \
            s11n_json.success_message_decoder_json(content_decoder).decode(response.text)
        if isinstance(content_result, Err):
            return Err(BackendManagementError("Failed to parse successful response", exception=content_result.value))
        return Ok(content_result.value.value)

    def static_get_json_result(
        self,
        path: str,
        content_decoder: Optional[DecoderJSON[FETCH_CONTENT]],
        headers: Optional[Dict] = None
    ) -> Result[FETCH_CONTENT, BackendManagementError]:
        """Fetch a static content"""
        # Build URL
        url_result = self.static_url(path)
        if isinstance(url_result, Err): return Err(url_result.value)
        url_text_result = url_result.value.text()
        if isinstance(url_text_result, Err): return Err(url_text_result.value)

        # Send request and receive response
        if headers is None:
            headers = {}
        try:
            LOGGER.debug(f"HTTP GET JSON: {url_text_result.value}, headers: {headers}")
            response = requests.get(url_text_result.value, headers=headers)
            LOGGER.debug(ManagedURL.response_log_text(response))
            return BackendService.response_to_result(response, content_decoder)
        except Exception as e:
            return Err(BackendManagementError("Request failed", exception=e))

    def static_post_json_result(
        self,
        path: str,
        content_decoder: Optional[DecoderJSON[FETCH_CONTENT]] = None,
        payload: Optional[SEND_CONTENT] = None,
        payload_encoder: Optional[EncoderJSON] = None,
        headers: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Result[FETCH_CONTENT, BackendManagementError]:
        """Fetch a static content"""
        # Build URL
        url_result = self.static_url(path)
        if isinstance(url_result, Err): return Err(url_result.value)
        url_text_result = url_result.value.text()
        if isinstance(url_text_result, Err): return Err(url_text_result.value)

        # Send request and receive response
        if headers is None: headers = {}
        if files is None: files = {}
        try:
            if payload is None:
                LOGGER.debug(f"HTTP POST JSON: {url_text_result.value}, headers: {headers}, files:{ files }")
                response = requests.post(url_text_result.value, headers=headers, files=files)
            else:
                encoded_payload = payload_encoder.encode(payload) if payload_encoder is not None else payload
                LOGGER.debug(f"HTTP POST JSON: {url_text_result.value}, payload: {encoded_payload}, headers: {headers}, files:{files}")
                response = requests.post(url_text_result.value, encoded_payload, headers=headers, files=files)
            # Parse response
            LOGGER.debug(ManagedURL.response_log_text(response))
            return BackendService.response_to_result(response, content_decoder)
        except Exception as e:
            return Err(BackendManagementError("Request failed", exception=e))

    # User
    def auth_check(self) -> Optional[DIPClientError]:
        if self.config.auth is None: return BackendService.auth_error
        path = f"{self.config.api_prefix}/auth-check"
        auth_result = self.static_get_json_result(path, s11n_json.UNIT_DECODER_JSON, headers=self.config.auth.auth_headers())
        if isinstance(auth_result, Err):
            return auth_result.value
        return None

    def user_list(self) -> Result[List[User], BackendManagementError]:
        """Fetch a list of users"""
        path = f"{self.config.api_prefix}/user"
        decoder = s11n_json.list_decoder_json(s11n_json.USER_DECODER_JSON)
        return self.static_get_json_result(path, decoder, headers=self.config.auth.auth_headers())

    def user_create(self, username: str, password: str) -> Result[User, str]:
        """Create a new user"""
        path = f"{self.config.api_prefix}/user"
        encoder = s11n_json.CREATE_USER_MESSAGE_ENCODER_JSON
        decoder = s11n_json.USER_DECODER_JSON
        payload = CreateUserMessage(username, password)
        return self.static_post_json_result(path, decoder, payload, encoder, self.json_headers)

    # Hardware
    def hardware_list(self) -> Result[List[Hardware], BackendManagementError]:
        """Fetch a list of hardware"""
        path = f"{self.config.api_prefix}/hardware"
        decoder = s11n_json.list_decoder_json(s11n_json.HARDWARE_DECODER_JSON)
        return self.static_get_json_result(path, decoder, headers=self.config.auth.auth_headers())

    def hardware_create(
        self,
        hardware_name: str
    ) -> Result[Hardware, BackendManagementError]:
        """Create a new hardware"""
        path = f"{self.config.api_prefix}/hardware"
        encoder = s11n_json.CREATE_HARDWARE_MESSAGE_ENCODER_JSON
        decoder = s11n_json.HARDWARE_DECODER_JSON
        payload = CreateHardwareMessage(hardware_name)
        if self.config.auth is None: return BackendService.auth_error
        headers = dict(self.json_headers, **self.config.auth.auth_headers())
        return self.static_post_json_result(path, decoder, payload, encoder, headers)

    def hardware_software_upload(
        self,
        hardware_id: ManagedUUID,
        software_id: ManagedUUID
    ) -> Optional[BackendManagementError]:
        """Upload a given software to a given hardware"""
        path = f"{self.config.api_prefix}/hardware/{hardware_id.value}/upload/software/{software_id.value}"
        result = self.static_post_json_result(path, headers=self.config.auth.auth_headers())
        if isinstance(result, Err):
            return result.value
        return None

    # Software
    def software_list(self) -> Result[List[Software], str]:
        """Fetch a list of software"""
        path = f"{self.config.api_prefix}/software"
        decoder = s11n_json.list_decoder_json(s11n_json.SOFTWARE_DECODER_JSON)
        return self.static_get_json_result(path, decoder, headers=self.config.auth.auth_headers())

    def software_upload(
        self,
        file_path: ExistingFilePath,
        software_name: Optional[str]
    ) -> Result[Software, BackendManagementError]:
        """Upload a new software"""
        path = f"{self.config.api_prefix}/software"
        decoder = s11n_json.SOFTWARE_DECODER_JSON
        files = {'software': open(file_path.value, 'rb')}
        if software_name is None:
            software_name = os.path.basename(file_path.value)
        payload = {'name': software_name}
        if self.config.auth is None: return BackendService.auth_error
        return self.static_post_json_result(path, decoder, payload, None, self.config.auth.auth_headers(), files)

    def software_download(
        self,
        software_id: ManagedUUID,
        file_path: Optional[str] = None
    ) -> Result[ExistingFilePath, BackendManagementError]:
        """Download temporary software file and return its file path"""
        # Build URL
        url_result = self.static_url(f"{self.config.api_prefix}/software/{software_id.value}/download")
        if isinstance(url_result, Err): return Err(url_result.value)
        url_with_auth_result = url_result.value.with_basic_auth(self.config.auth.username, self.config.auth.password) # Bad hack
        if isinstance(url_with_auth_result, Err): return Err(url_with_auth_result.value)

        # Download file
        if file_path is None:
            file_result = url_with_auth_result.value.downloaded_file_in_temp()
        else:
            file_result = url_with_auth_result.value.downloaded_file_in_path(file_path)

        # Handle file download
        if isinstance(file_result, Err):
            return Err(BackendManagementError("Failed download", exception=file_result.value))
        return Ok(file_result.value)
