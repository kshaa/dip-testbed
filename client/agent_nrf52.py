#!/usr/bin/env python
"""NRF52 micro-controller client functionality."""

from typing import Sequence, Tuple, Any
from result import Result, Err
from engine import Engine, EngineConfig
from protocol import CommonIncomingMessage, UploadMessage
from sh import root_relative_path, outcome_sh
from agent_util import AgentConfig
import log

LOGGER = log.timed_named_logger("nrf52")
FIRMWARE_UPLOAD_PATH = 'static/adafruit_nrf52/upload.sh'


def firmware_upload_args(
    firmware_path: str,
    device_path: str,
    baud_rate: int
) -> Sequence[str]:
    """Create command line arguments to initiate firmware upload"""
    upload_script_path = root_relative_path(FIRMWARE_UPLOAD_PATH)
    return [
        "bash",
        "-c",
        f"{upload_script_path} "
        f"-d \"{device_path}\" "
        f"-b \"{baud_rate}\" "
        f"-f \"{firmware_path}\""
    ]


class EngineNRF52Config(EngineConfig):
    """NRF52 engine configuration options"""
    device: str
    baudrate: int

    def __init__(self, agent: AgentConfig, device: str, baudrate: int):
        super().__init__(agent)
        self.device = device
        self.baudrate = baudrate


class EngineNRF52(Engine[CommonIncomingMessage, Any]):
    """Engine for NRF52 microcontroller"""
    config: EngineNRF52Config

    def firmware_upload(
        self,
        file: str
    ) -> Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]:
        """Upload firmware and return shell script outcome"""
        return outcome_sh(firmware_upload_args(
            file, self.config.device, self.config.baudrate))

    # Duplicate code, but not enough to refactor
    # pylint: disable=R0801
    def process(self, message: CommonIncomingMessage) -> Result[Any, Exception]:
        """Consume server-sent message and react accordingly"""
        message_type = type(message)
        if message_type == UploadMessage:
            return self.process_upload_message_sh(message, firmware_upload_args)
        return Err(NotImplementedError())
