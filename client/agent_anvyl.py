#!/usr/bin/env python
"""Anvyl FPGA client functionality."""

from typing import Sequence, Tuple, Any
from result import Result, Err
from engine import Engine, EngineConfig
from protocol import CommonIncomingMessage, UploadMessage
from sh import root_relative_path, outcome_sh
from agent_util import AgentConfig
import log

LOGGER = log.timed_named_logger("anvyl")
FIRMWARE_UPLOAD_PATH = 'static/digilent_anvyl/upload.sh'


def firmware_upload_args(
    firmware_path: str,
    device_name: str,
    scan_chain_index: int
) -> Sequence[str]:
    """Create command line arguments to initiate firmware upload"""
    upload_script_path = root_relative_path(FIRMWARE_UPLOAD_PATH)
    return [
        "bash",
        "-c",
        f"{upload_script_path} "
        f"-d \"{device_name}\" "
        f"-s \"{scan_chain_index}\" "
        f"-f \"{firmware_path}\""
    ]


class EngineAnvylConfig(EngineConfig):
    """Anvyl engine configuration options"""
    device_name: str
    scan_chain_index: int

    def __init__(self, agent: AgentConfig, device_name: str, scan_chain_index: int):
        super().__init__(agent)
        self.device_name = device_name
        self.scan_chain_index = scan_chain_index


class EngineAnvyl(Engine[CommonIncomingMessage, Any]):
    """Engine for Anvyl microcontroller"""
    config: EngineAnvylConfig

    def firmware_upload(
        self,
        file: str
    ) -> Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]:
        """Upload firmware and return shell script outcome"""
        return outcome_sh(firmware_upload_args(
            file, self.config.device_name, self.config.scan_chain_index))

    def process(self, message: CommonIncomingMessage) -> Result[Any, Exception]:
        """Consume server-sent message and react accordingly"""
        message_type = type(message)
        if message_type == UploadMessage:
            return self.process_upload_message_sh(message, firmware_upload_args)
        return Err(NotImplementedError())
