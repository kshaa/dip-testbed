#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""

from typing import TypeVar, Generic, Callable, Tuple
import os
from result import Result, Err, Ok
from pprint import pformat
import log
from agent_util import AgentConfig
from protocol import UploadMessage, UploadResultMessage

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
    ) -> Result[UploadResultMessage, Exception]:
        """Logic for NRF52 for UploadMessage"""
        # Download software
        LOGGER.info("Downloading firmware")
        file_result = self.config.agent.backend.download_temp_software(message.software_id)
        if isinstance(file_result, Err):
            message = f"Failed software download: {file_result.value}"
            LOGGER.error(message)
            return Ok(UploadResultMessage(message))
        file = file_result.value
        LOGGER.info("Downloaded software: %s", file)

        # Upload software
        upload_result = upload_file(file)
        try:
            LOGGER.debug("Removing temporary software: %s", file)
            os.remove(file)
        except Exception as e:
            LOGGER.error("Failed to remove temporary software '%s': %s", file, e)
        outcome = upload_result.value
        status_code = outcome[0]
        stdout = outcome[1].decode("utf-8")
        stderr = outcome[2].decode("utf-8")
        outcome_message = f"#### Status code: {status_code}\n" \
                          f"#### Stdout:\n{stdout}\n" \
                          f"#### Stderr:\n{stderr}"
        if isinstance(upload_result, Err):
            LOGGER.error("%s", pformat(outcome_message, indent=4))
            return Ok(UploadResultMessage(outcome_message))
        else:
            LOGGER.info("%s", pformat(outcome_message, indent=4))
            return Ok(UploadResultMessage(None))
