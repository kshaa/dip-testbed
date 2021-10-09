#!/usr/bin/env python
"""NRF52 micro-controller agent functionality."""

from typing import Iterable, Tuple, Any
import subprocess
from subprocess import CalledProcessError
from result import Result, Err, Ok
from engine import Engine
from protocol import CommonIncomingMessage, UploadMessage
from sh import root_relative_path

FIRMWARE_UPLOAD_PATH = 'static/adafruit_nrf52/upload.sh'


def firmware_upload_args(firmware_path: str, device_path: str, baud_rate: int) -> Iterable[str]:
    """Create command line arguments to initiate firmware upload"""
    upload_script_path = root_relative_path(FIRMWARE_UPLOAD_PATH)
    return [
        "bash",
        "-c",
        f"{upload_script_path} -d {device_path} -b {baud_rate} -f {firmware_path}"
    ]


def firmware_upload(
        firmware_path: str,
        device_path: str,
        baud_rate: int
) -> Result[bytes, Tuple[int, bytes]]:
    """Run firmware upload command and return error code & stderr or stdout"""
    runner_args = firmware_upload_args(firmware_path, device_path, baud_rate)
    try:
        return Ok(subprocess.check_output(runner_args))  # type: ignore
    except CalledProcessError as e:
        return Err((e.returncode, e.output))
    except Exception as e:
        return Err((1, str.encode(f"{e}")))


class EngineNRF52Config:
    """NRF52 engine configuration options"""
    baudrate: int

    def __init__(self, baudrate: int):
        self.baudrate = baudrate


class EngineNRF52(Engine[CommonIncomingMessage, Any]):
    """Engine for NRF52 microcontroller"""
    config: EngineNRF52Config

    def __init__(self, config: EngineNRF52Config):
        super().__init__()
        self.config = config

    def process(self, message: CommonIncomingMessage) -> Result[Any, Exception]:
        """Consume server-sent message and react accordingly"""
        message_type = type(message)
        if message_type == UploadMessage:
            return Err(Exception("tada"))

        return Err(NotImplementedError())
