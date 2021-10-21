#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""

from typing import TypeVar, Generic, Callable, Tuple, Any
from result import Result, Err
import log
from agent_util import AgentConfig
from protocol import UploadMessage

LOGGER = log.timed_named_logger("engine")
PI = TypeVar('PI')
PO = TypeVar('PO')


class EngineConfig:
    """Generic engine configuration options"""
    agent: AgentConfig

    def __init__(self, agent: AgentConfig):
        self.agent = agent


class Engine(Generic[PI, PO]):
    """Implementation of generic microcontroller agent engine"""
    config: EngineConfig

    def __init__(self, config):
        self.config = config

    # W0613: ignore unused message, because this class is abstract
    # R0201: ignore no-self-use, because I want this method here regardless
    # pylint: disable=W0613,R0201
    def process(self, message: PI) -> Result[PO, Exception]:
        """Consume server-sent message and react accordingly"""
        return Err(NotImplementedError())

    def process_upload_message_sh(
        self,
        message: UploadMessage,
        upload_file: Callable[[str], Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]]
    ) -> Result[Any, Exception]:
        """Logic for NRF52 for UploadMessage"""
        # Download software
        LOGGER.info("Downloading firmware")
        file_result = self.config.agent.backend.download_temp_software(message.software_id)
        if isinstance(file_result, Err):
            LOGGER.error("Failed software download: %s", file_result.value)
            return Err(NotImplementedError("Correct server reply not implemented"))
        file = file_result.value
        LOGGER.info("Downloaded software: %s", file)

        # Upload software
        upload_result = upload_file(file)
        if isinstance(upload_result, Err):
            LOGGER.error("Failed upload: %s", upload_result.value)
            return Err(NotImplementedError("Correct server reply not implemented"))
        LOGGER.info("Upload successful: %s", upload_result.value)
        return Err(NotImplementedError("Correct server reply not implemented"))
