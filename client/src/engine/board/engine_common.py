"""Generic board engine client functionality."""
from dataclasses import dataclass
from typing import List, TypeVar, Optional
from result import Result
from src.domain.dip_client_error import DIPClientError
from src.engine.engine import Engine
from src.engine.board.engine_common_state import EngineCommonState
from src.domain.hardware_control_event import COMMON_ENGINE_EVENT, log_event
from src.engine.engine_auth import EngineAuth
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, COMMON_OUTGOING_MESSAGE, log_hardware_message, \
    HardwareControlMessage, InternalStartLifecycle, InternalEndLifecycle
from src.engine.board.engine_serial_monitor import EngineSerialMonitor
from src.engine.board.engine_upload import EngineUpload
from src.util import log

HARDWARE_LOGGER = log.timed_named_logger("incoming_engine")
EVENT_LOGGER = log.timed_named_logger("event")
PI = TypeVar('PI', bound=COMMON_INCOMING_MESSAGE)
PO = TypeVar('PO', bound=COMMON_OUTGOING_MESSAGE)
S = TypeVar('S', bound=EngineCommonState)
E = TypeVar('E', bound=COMMON_ENGINE_EVENT)
X = TypeVar('X', bound=DIPClientError)


@dataclass
class EngineCommon(Engine[PI, PO, S, E, X]):
    engine_lifecycle: EngineLifecycle
    engine_upload: EngineUpload
    engine_ping: EnginePing
    engine_serial_monitor: EngineSerialMonitor
    engine_auth: EngineAuth

    async def start(self):
        await self.state.base.incoming_message_queue.put(InternalStartLifecycle())

    async def kill(self, reason: Optional[DIPClientError]):
        await self.state.base.incoming_message_queue.put(InternalEndLifecycle(reason))

    async def pre_process_message(self, previous_state: EngineCommonState, message: HardwareControlMessage):
        log_hardware_message(HARDWARE_LOGGER, message)

    async def pre_process_event(self, previous_state: EngineCommonState, event: COMMON_ENGINE_EVENT):
        log_event(EVENT_LOGGER, event)

    def message_project(
        self,
        previous_state: EngineCommonState,
        message: COMMON_INCOMING_MESSAGE
    ) -> Result[List[COMMON_ENGINE_EVENT], DIPClientError]:
        return self.multi_message_project([
            self.engine_lifecycle.handle_message,
            self.engine_upload.handle_message,
            self.engine_serial_monitor.handle_message,
            self.engine_auth.handle_message
        ], previous_state, message)

    def state_project(self, previous_state: EngineCommonState, event: COMMON_ENGINE_EVENT) -> S:
        monitored_state = self.engine_serial_monitor.state_project(previous_state, event)
        return monitored_state

    async def effect_project(self, previous_state: EngineCommonState, event: COMMON_ENGINE_EVENT):
        projections = [
            self.engine_lifecycle.effect_project,
            self.engine_upload.effect_project,
            self.engine_ping.effect_project,
            self.engine_serial_monitor.effect_project,
            self.engine_auth.effect_project
        ]
        return await Engine.multi_effect_project(projections, previous_state, event)

