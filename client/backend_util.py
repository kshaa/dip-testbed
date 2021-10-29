"""Module for functionality related to backend"""

import sys
import asyncio
from typing import Optional, List, TypeVar, Callable, Dict, Any
from dataclasses import dataclass
import termios
import tty
import signal
from urllib.parse import ParseResult
from pprint import pformat
import base64
from uuid import UUID
from result import Result, Ok, Err
from websockets.exceptions import ConnectionClosedError
from requests import Response
import requests
import protocol
import s11n
from url import url_with_path_str, download_file, download_temp_file, response_log_text
import log
from backend_domain import User, Hardware, Software
from codec import CodecParseException
from protocol import SuccessMessage, FailureMessage
from ws import WebSocket
from death import Death

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

    @staticmethod
    def response_to_result(
        response: Response,
        success_decode: Callable[[str], Result[SUCCESS_CONTENT, CodecParseException]],
        empty_success: bool = False
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
        user_create_response = requests.post(
            user_create_url, payload_serialized, headers=self.json_headers)
        LOGGER.debug(response_log_text(user_create_response))

        # Handle result
        result = self.response_to_result(
            user_create_response,
            s11n.success_message_decoder(s11n.user_decode))
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
        result = self.response_to_result(
            hardware_list_response,
            s11n.success_message_decoder(s11n.list_decoder(s11n.hardware_decode))
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
        payload_serialized = s11n.CREATE_HARDWARE_MESSAGE_ENCODER.transform(payload)
        request_headers = dict(self.json_headers, **self.auth_headers(username, password))
        hardware_create_response = requests.post(
            hardware_create_url,
            payload_serialized,
            headers=request_headers)
        LOGGER.debug(response_log_text(hardware_create_response))

        # Handle result
        result = self.response_to_result(
            hardware_create_response,
            s11n.success_message_decoder(s11n.hardware_decode))
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
            return Err("Hardware softwareu upload URL build failed: %s")
        hardware_software_upload_url = hardware_software_upload_url_result.value

        # Send request
        hardware_create_response = requests.post(hardware_software_upload_url)
        LOGGER.debug(response_log_text(hardware_create_response))

        # Handle result
        result = self.response_to_result(
            hardware_create_response,
            s11n.success_message_decoder(s11n.hardware_decode),
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
        result = self.response_to_result(
            software_list_response,
            s11n.success_message_decoder(s11n.list_decoder(s11n.software_decode))
        )
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
            s11n.success_message_decoder(s11n.software_decode))
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

    async def hardware_serial_monitor(self, hardware_id: UUID):
        # Build URL
        monitor_url_result = url_with_path_str(
            self.control_server,
            f"{self.api_prefix}/hardware/{hardware_id}/monitor/serial")
        if isinstance(monitor_url_result, Err):
            return Err("Hardware serial monitor URL build failed: %s")
        monitor_url = monitor_url_result.value

        # Connect to hardware listener in backend control
        decoder = s11n.MONITOR_LISTENER_INCOMING_MESSAGE_DECODER
        encoder = s11n.MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER
        websocket = WebSocket(monitor_url, decoder, encoder)
        LOGGER.debug("Connecting connect to control server: %s", monitor_url)
        error = await websocket.connect()
        if error is not None:
            return Err(f"Couldn't connect to control server: {error}")

        # Async IO loop
        asyncio_loop = asyncio.get_event_loop()

        # Silence stdin
        def silence_stdin() -> Any:
            stdin = sys.stdin.fileno()
            tattr = termios.tcgetattr(stdin)
            tty.setcbreak(stdin, termios.TCSANOW)
            sys.stdout.write("\x1b[6n")
            sys.stdout.flush()
            return tattr
        tattr = silence_stdin()
        def unsilence_stdin(tattr: Any):
            stdin = sys.stdin.fileno()
            termios.tcsetattr(stdin, termios.TCSANOW, tattr)

        # Transmit stdin to agent
        async def keep_transmitting_to_agent():
            stdin_reader = asyncio.StreamReader()
            stdin_protocol = asyncio.StreamReaderProtocol(stdin_reader)
            await asyncio_loop.connect_read_pipe(lambda: stdin_protocol, sys.stdin)
            while True:
                read_bytes = await stdin_reader.read(1)
                message = protocol.SerialMonitorMessageToAgent.from_bytes(read_bytes)
                await websocket.tx(message)
        asyncio_loop = asyncio.get_event_loop()
        stdin_capture_task = asyncio_loop.create_task(keep_transmitting_to_agent())

        # Define final handler
        death = Death()
        def handle_finish():
            death.grace()
            stdin_capture_task.cancel()
            asyncio_loop.create_task(websocket.disconnect())
            unsilence_stdin(tattr)

        # Handle signal interrupts
        for signame in ('SIGINT', 'SIGTERM'):
            asyncio_loop.add_signal_handler(getattr(signal, signame), handle_finish)

        # Run monitoring loop
        while True:
            incoming_message_result = await websocket.rx()

            # Handle message failures
            if death.graceful:
                return Ok()
            elif isinstance(incoming_message_result, Err) \
                    and isinstance(incoming_message_result.value, ConnectionClosedError):
                handle_finish()
                return Err("Control server connection closed")
            if isinstance(incoming_message_result, Err) \
                    and isinstance(incoming_message_result.value, CodecParseException):
                handle_finish()
                return Err("Unknown command received, ignoring")
            elif isinstance(incoming_message_result, Err):
                handle_finish()
                return Err(f"Failed to receive message: {pformat(incoming_message_result.value, indent=4)}")

            # Handle successful message
            incoming_message = incoming_message_result.value
            if isinstance(incoming_message, protocol.MonitorUnavailable):
                handle_finish()
                return Err(f"Monitor not available anymore: {incoming_message.reason}")
            elif isinstance(incoming_message, protocol.SerialMonitorMessageToClient):
                incoming_bytes = incoming_message.to_bytes()
                sys.stdout.buffer.write(incoming_bytes)
                sys.stdout.buffer.flush()
