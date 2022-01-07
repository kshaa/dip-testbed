#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""

from typing import TypeVar, Generic, Callable, Tuple, Any, Optional
import asyncio
import os
from result import Result, Err, Ok
from pprint import pformat
import log
from agent_util import AgentConfig
from protocol import \
    PingMessage, \
    UploadMessage, \
    UploadResultMessage, \
    CommonIncomingMessage, \
    CommonOutgoingMessage, \
    SerialMonitorRequest, \
    SerialMonitorResult, \
    SerialMonitorMessageToAgent, \
    SerialMonitorMessageToClient
from ws import WebSocket
from serial import Serial
from serial_util import SerialConfig, monitor_serial

LOGGER = log.timed_named_logger("engine")
SERIALIZABLE = TypeVar('SERIALIZABLE')
PI = TypeVar('PI')
PO = TypeVar('PO')


class EngineConfig:
    """Generic engine configuration options"""
    agent: AgentConfig

    def __init__(self, agent: AgentConfig):
        self.agent = agent


class Engine(Generic[SERIALIZABLE, PI, PO]):
    """Implementation of generic microcontroller agent engine"""
    # Generic state
    config: EngineConfig
    engine_on: bool = True
    socket: Optional[WebSocket[SERIALIZABLE, CommonIncomingMessage, CommonOutgoingMessage]] = None

    # Ping state
    ping_enabled: bool = True
    ping_task: Optional[Any] = None

    # Serial monitor state
    serial: Optional[Tuple[Serial, SerialConfig]] = None
    serial_receive_task: Optional[Any] = None

    # Constructor
    def __init__(self, config):
        self.config = config

    # Ping methods
    async def keep_pinging(
        self,
        socket: WebSocket[SERIALIZABLE, CommonIncomingMessage, CommonOutgoingMessage]
    ):
        """Keeps pinging server while engine is on"""
        while self.engine_on:
            await socket.tx(PingMessage())
            await asyncio.sleep(self.config.agent.heartbeat_seconds)

    def start_ping(self, socket: WebSocket):
        """Start sending regular heartbeat to server"""
        loop = asyncio.get_event_loop()
        self.ping_task = loop.create_task(self.keep_pinging(socket))

    def stop_ping(self):
        """Stop sending regular heartbeat to server"""
        if self.ping_task is not None:
            self.ping_task.cancel()
            self.ping_task = None

    # Monitoring methods
    async def monitor_to_server(self, sendable: Optional[bytes]):
        """Send monitoring data to server"""
        if self.socket is not None and sendable is not None:
            message = SerialMonitorMessageToClient.from_bytes(sendable)
            await self.socket.tx(message)

    async def keep_monitoring(self):
        """Keep receiving messages and enact on them"""
        while self.engine_on and self.serial is not None:
            (serial, serialConfig) = self.serial
            received_bytes = serial.read(serialConfig.receive_size)
            if received_bytes is not None and len(received_bytes) > 0:
                # Send to server immediately, don't wait for request to finish
                loop = asyncio.get_event_loop()
                loop.create_task(self.monitor_to_server(received_bytes))
            # Python is trash, sleep for a bit to allow other
            # async coroutines to execute
            await asyncio.sleep(serialConfig.timeout)

    def start_monitor(self, serial: Serial, serial_config: SerialConfig):
        """Start serial monitoring"""
        loop = asyncio.get_event_loop()
        self.serial = (serial, serial_config)
        self.serial_receive_task = loop.create_task(self.keep_monitoring())

    def stop_monitor(self):
        """Stop sending regular heartbeat to server"""
        if self.serial_receive_task is not None:
            self.serial_receive_task.cancel()
            self.serial_receive_task = None

        if self.serial is not None:
            (serial, _) = self.serial
            serial.close()
            self.serial = None

    # Socket lifecycle methods
    def on_start(self, socket: WebSocket):
        """Engine start hook"""
        self.engine_on = True
        self.socket = socket
        self.start_ping(socket)

    def on_end(self):
        """Engine end hook"""
        self.engine_on = False
        self.socket = None
        self.stop_ping()
        self.stop_monitor()

    # Message handler entrypoint
    # W0613: ignore unused message, because this class is abstract
    # R0201: ignore no-self-use, because I want this method here regardless
    # pylint: disable=W0613,R0201
    def process(self, message: PI) -> Optional[Result[PO, Exception]]:
        """Consume server-sent message and react accordingly"""
        return Err(NotImplementedError())

    # Generic shell script upload handler
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

    # Generic serial port monitor handler
    def process_serial_monitor(
        self,
        device: str,
        message: SerialMonitorRequest
    ) -> Result[CommonOutgoingMessage, Exception]:
        """Configure and start serial monitoring"""
        # Stop old monitor
        self.stop_monitor()

        # Define a strictly non-empty configuration
        if message.config is None:
            serial_config = SerialConfig.empty()
        else:
            serial_config = message.config

        # Avoid changes to monitoring if configuration doesn't change
        if self.serial is not None:
            (_, old_serial_config) = self.serial
            if old_serial_config == serial_config:
                LOGGER.debug("Skipping monitor request with unchanged config")
                return Ok(SerialMonitorResult(None))

        # Connect to serial device w/ the given configurations
        serial_result = monitor_serial(device, serial_config)
        if isinstance(serial_result, Err):
            outcome_message = f"Failed setting up monitor: {pformat(serial_result.value, indent=4)}"
            LOGGER.error("%s", outcome_message)
            return Ok(SerialMonitorResult(outcome_message))

        # Initiate monitoring
        self.start_monitor(serial_result.value, serial_config)

        return Ok(SerialMonitorResult(None))

    def process_serial_monitor_stop(self):
        """Stop serial monitoring"""
        self.stop_monitor()

    def process_serial_monitor_to_agent(
        self,
        message: SerialMonitorMessageToAgent
    ):
        if self.serial is not None:
            (serial, serialConfig) = self.serial
            serial.write(message.to_bytes())
        return None
