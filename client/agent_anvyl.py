#!/usr/bin/env python
"""Anvyl FPGA client functionality."""

from typing import Sequence, Tuple, Any
import subprocess
from subprocess import CalledProcessError
from result import Result, Err, Ok
from engine import Engine
from protocol import CommonIncomingMessage, UploadMessage
from sh import root_relative_path
from agent_util import AgentConfig, download_temp_software
import log

LOGGER = log.timed_named_logger("anvyl")
FIRMWARE_UPLOAD_PATH = 'static/digilent_anvyl/upload.sh'


def firmware_upload_args(firmware_path: str, device_name: str, scan_chain_index: int) -> Sequence[str]:
    """Create command line arguments to initiate firmware upload"""
    upload_script_path = root_relative_path(FIRMWARE_UPLOAD_PATH)
    return [
        "bash",
        "-c",
        f"{upload_script_path} -d \"{device_name}\" -s \"{scan_chain_index}\" -f \"{firmware_path}\""
    ]


def firmware_upload(
    firmware_path: str,
    device_name: str,
    scan_chain_index: int
) -> Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]:
    """Run firmware upload command and return error code & stderr or stdout"""
    runner_args = firmware_upload_args(firmware_path, device_name, scan_chain_index)
    try:
        LOGGER.debug("Running command: %s", runner_args)
        proc = subprocess.Popen(
            runner_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        LOGGER.debug("Command returncode: %s", proc.returncode)
        LOGGER.debug("Command stdout: %s", stdout)
        LOGGER.debug("Command stderr: %s", stderr)

        if proc.returncode == 0:
            return Ok((proc.returncode, stdout, stderr))
        else:
            return Err((proc.returncode, stdout, stderr))
    except CalledProcessError as e:
        return Err((e.returncode, "", e.output))
    except Exception as e:
        return Err((1, "", str.encode(f"{e}")))


class EngineAnvylConfig:
    """Anvyl engine configuration options"""
    common: AgentConfig
    device_name: str
    scan_chain_index: int

    def __init__(self, common: AgentConfig, device_name: str, scan_chain_index: int):
        self.common = common
        self.device_name = device_name
        self.scan_chain_index = scan_chain_index


class EngineAnvyl(Engine[CommonIncomingMessage, Any]):
    """Engine for Anvyl microcontroller"""
    config: EngineAnvylConfig

    def __init__(self, config: EngineAnvylConfig):
        super().__init__()
        self.config = config

    def process_upload_message(self, message: UploadMessage) -> Result[Any, Exception]:
        """Logic for Anvyl for UploadMessage"""
        # Download software
        LOGGER.info("Downloading firmware")
        file_result = download_temp_software(self.config.common, message.software_id)
        if isinstance(file_result, Err):
            LOGGER.error("Failed software download: %s", file_result.value)
            return Err(NotImplementedError("Correct server reply not implemented"))
        file = file_result.value
        LOGGER.info("Downloaded software: %s", file)

        # Upload software
        upload_result = firmware_upload(file, self.config.device_name, self.config.scan_chain_index)
        if isinstance(upload_result, Err):
            LOGGER.error("Failed upload: %s", upload_result.value)
            return Err(NotImplementedError("Correct server reply not implemented"))
        LOGGER.info("Upload successful: %s", upload_result.value)
        return Err(NotImplementedError("Correct server reply not implemented"))

    def process(self, message: CommonIncomingMessage) -> Result[Any, Exception]:
        """Consume server-sent message and react accordingly"""
        message_type = type(message)
        if message_type == UploadMessage:
            return self.process_upload_message(message)
        return Err(NotImplementedError())
