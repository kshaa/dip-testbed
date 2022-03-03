#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""
import asyncio
import dataclasses
from dataclasses import dataclass
from typing import TypeVar, List, Optional
from result import Result, Err, Ok
from src.domain.death import Death
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.existing_file_path import ExistingFilePath
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, SerialMonitorRequest, \
    InternalStartedSerialMonitor, InternalSerialMonitorStartFailure, SerialMonitorResult, InternalReceivedSerialBytes, \
    SerialMonitorRequestStop, InternalSerialMonitorStopped, InternalSerialMonitorStarting, InternalSerialMonitorDied
from src.domain.monitor_message import SerialMonitorMessageToAgent, SerialMonitorMessageToClient, MonitorUnavailable
from src.domain.hardware_control_event import COMMON_ENGINE_EVENT, StartSerialMonitor, SerialMonitorStartSuccess, \
    SerialMonitorStartFailure, ReceivedSerialBytes, SendingBoardBytes, StoppingSerialMonitor, StoppedSerialMonitor, \
    SerialMonitorAboutToStart, SerialMonitorAlreadyConfigured, MonitorDied, LifecycleEnded, UploadingBoardSoftware
from src.engine.engine_state import EngineState, EngineBase
from src.service.managed_serial import ManagedSerial
from src.service.managed_serial_config import ManagedSerialConfig
from src.util import log


LOGGER = log.timed_named_logger("agent")
PI = TypeVar('PI')
PO = TypeVar('PO')
S = TypeVar('S', bound=EngineState)
E = TypeVar('E')


class SerialBoard:
    device_path: ExistingFilePath


class EngineSerialMonitorState:
    base: EngineBase
    board_state: SerialBoard
    active_serial: Optional[ManagedSerial]
    serial_death: Death


@dataclass
class EngineSerialMonitor:
    """Software upload related effects projected by engine"""

    async def connect(
        self,
        device_path: ExistingFilePath,
        config: ManagedSerialConfig
    ) -> Result[ManagedSerial, DIPClientError]:
        return ManagedSerial.build(device_path, config)

    async def read(
        self,
        active_serial: ManagedSerial
    ) -> Result[bytes, DIPClientError]:
        return await active_serial.read()

    async def write(
        self,
        previous_state: EngineSerialMonitorState,
        value: bytes
    ) -> Result[type(None), DIPClientError]:
        if previous_state.active_serial is None:
            return Err(GenericClientError("Serial monitor is disconnected"))
        return await previous_state.active_serial.write(value)

    async def ping_until_death(
        self,
        previous_state: EngineSerialMonitorState,
        active_serial: ManagedSerial
    ):
        in_queue = previous_state.base.incoming_message_queue
        engine_death = previous_state.base.death
        serial_death = previous_state.serial_death
        while not engine_death.gracing and not serial_death.gracing:
            # Wait for new messages
            death_or_death_or_timeout = await engine_death.or_awaitable(
                serial_death.or_awaitable(asyncio.sleep(active_serial.config.timeout)))

            # Handle potential death (and stop receiving)
            if isinstance(death_or_death_or_timeout, Err) or isinstance(death_or_death_or_timeout.value, Err):
                return

            # Handle serial read failure (and stop receiving)
            received_bytes_result = await self.read(active_serial)
            if isinstance(received_bytes_result, Err):
                await in_queue.put(StoppingSerialMonitor(received_bytes_result.value))
                return

            # Handle non-empty serial read (and continue)
            received_bytes = received_bytes_result.value
            if received_bytes is not None and len(received_bytes) > 0:
                await in_queue.put(InternalReceivedSerialBytes(received_bytes_result.value))

    @staticmethod
    def handle_message(
        previous_state: EngineSerialMonitorState,
        message: COMMON_INCOMING_MESSAGE
    ) -> Result[List[COMMON_ENGINE_EVENT], DIPClientError]:
        if isinstance(message, SerialMonitorRequest):
            monitor_active = previous_state.active_serial != None
            monitor_config_changed = monitor_active and \
                                     message.config is not None and\
                                     previous_state.active_serial.config != message.config
            if not monitor_active or monitor_config_changed:
                config = message.config if message.config is not None else ManagedSerialConfig.empty()
                return Ok([SerialMonitorAboutToStart(config)])
            else:
                return Ok([SerialMonitorAlreadyConfigured()])
        elif isinstance(message, InternalSerialMonitorStarting):
            return Ok([StartSerialMonitor(message.config, previous_state.board_state.device_path)])
        elif isinstance(message, InternalStartedSerialMonitor):
            return Ok([SerialMonitorStartSuccess(message.serial)])
        elif isinstance(message, InternalSerialMonitorStartFailure):
            return Ok([SerialMonitorStartFailure(message.reason)])
        elif isinstance(message, InternalReceivedSerialBytes):
            return Ok([ReceivedSerialBytes(message.received_bytes)])
        elif isinstance(message, SerialMonitorMessageToAgent):
            return Ok([SendingBoardBytes(message.content_bytes)])
        elif isinstance(message, SerialMonitorRequestStop):
            return Ok([StoppingSerialMonitor()])
        elif isinstance(message, InternalSerialMonitorStopped):
            return Ok([StoppedSerialMonitor()])
        elif isinstance(message, InternalSerialMonitorDied):
            return Ok([MonitorDied()])
        return Ok([])

    @staticmethod
    def state_project(previous_state: EngineSerialMonitorState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, SerialMonitorAboutToStart):
            return dataclasses.replace(previous_state, active_serial=None, serial_death=Death())
        elif isinstance(event, SerialMonitorStartSuccess):
            return dataclasses.replace(previous_state, active_serial=event.serial)
        elif isinstance(event, SerialMonitorStartFailure):
            return dataclasses.replace(previous_state, active_serial=None, serial_death=Death())
        elif isinstance(event, StoppedSerialMonitor):
            return dataclasses.replace(previous_state, active_serial=None, serial_death=Death())
        return previous_state

    async def effect_project(self, previous_state: EngineSerialMonitorState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, SerialMonitorAlreadyConfigured):
            await previous_state.base.outgoing_message_queue.put(SerialMonitorResult(None))
        elif isinstance(event, SerialMonitorAboutToStart):
            await previous_state.base.incoming_message_queue.put(InternalSerialMonitorStarting(event.config))
        elif isinstance(event, StartSerialMonitor):
            result = await self.connect(event.device_path, event.config)
            if isinstance(result, Err):
                await previous_state.base.incoming_message_queue.put(InternalSerialMonitorStartFailure(result.value))
            await previous_state.base.incoming_message_queue.put(InternalStartedSerialMonitor(result.value))
        elif isinstance(event, SerialMonitorStartFailure):
            await previous_state.base.outgoing_message_queue.put(SerialMonitorResult(event.reason.text()))
        elif isinstance(event, SerialMonitorStartSuccess):
            await previous_state.base.outgoing_message_queue.put(SerialMonitorResult(None))
            await self.ping_until_death(previous_state, event.serial)
        elif isinstance(event, ReceivedSerialBytes):
            await previous_state.base.outgoing_message_queue.put(SerialMonitorMessageToClient(event.received_bytes))
        elif isinstance(event, SendingBoardBytes):
            write_result = await self.write(previous_state, event.content_bytes)
            if isinstance(write_result, Err):
                if previous_state.serial_death is not None:
                    previous_state.serial_death.grace()
                await previous_state.base.incoming_message_queue.put(InternalSerialMonitorDied())
        elif isinstance(event, StoppingSerialMonitor):
            if previous_state.active_serial is not None:
                await previous_state.active_serial.close()
            if previous_state.serial_death is not None:
                previous_state.serial_death.grace()
            message = f"Hardware control stopped monitor"
            if event.reason is not None:
                message = f"{message}, reason: {event.reason.text()}"
            await previous_state.base.outgoing_message_queue.put(MonitorUnavailable(message))
            await previous_state.base.incoming_message_queue.put(InternalSerialMonitorStopped())
        elif isinstance(event, MonitorDied):
            await previous_state.base.outgoing_message_queue.put(MonitorUnavailable("Serial device disconnected"))
            await previous_state.base.incoming_message_queue.put(InternalSerialMonitorStopped())
        elif isinstance(event, LifecycleEnded):
            message = f"Agent engine stopped"
            if event.reason is not None:
                message = f"{message}, reason: {event.reason.text()}"
            await previous_state.base.outgoing_message_queue.put(MonitorUnavailable(message))
        elif isinstance(event, UploadingBoardSoftware):
            await previous_state.base.outgoing_message_queue.put(MonitorUnavailable(
                "Serial connection broken by new board software upload"))