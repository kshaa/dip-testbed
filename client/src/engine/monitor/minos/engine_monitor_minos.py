from dataclasses import dataclass
from os import environ
from typing import List, Optional
from result import Result
from src.domain.dip_client_error import DIPClientError
from src.domain.hardware_video_message import COMMON_INCOMING_VIDEO_MESSAGE, COMMON_OUTGOING_VIDEO_MESSAGE, \
    HardwareVideoMessage, InternalStartLifecycle, InternalEndLifecycle
from src.domain.monitor_message import log_monitor_message
from src.engine.engine import Engine
from src.engine.engine_auth import EngineAuth
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.domain.hardware_video_event import COMMON_ENGINE_EVENT, log_event
from src.engine.monitor.minos.engine_monitor_minos_app import EngineMonitorMinOSApp
from src.engine.monitor.minos.engine_monitor_minos_state import EngineMonitorMinOSState
from src.util import log

MESSAGE_LOGGER = log.timed_named_logger("incoming_engine")
EVENT_LOGGER = log.timed_named_logger("event")


@dataclass
class EngineMonitorMinOS(Engine[
    COMMON_INCOMING_VIDEO_MESSAGE,
    COMMON_OUTGOING_VIDEO_MESSAGE,
    EngineMonitorMinOSState,
    COMMON_ENGINE_EVENT,
    DIPClientError
]):
    engine_lifecycle: EngineLifecycle
    engine_ping: EnginePing
    engine_minos_app: EngineMonitorMinOSApp
    engine_auth: EngineAuth

    async def start(self):
        await self.state.base.incoming_message_queue.put(InternalStartLifecycle())

    async def kill(self, reason: Optional[DIPClientError]):
        await self.state.base.incoming_message_queue.put(InternalEndLifecycle(reason))

    async def pre_process_message(self, previous_state: EngineMonitorMinOSState, message: HardwareVideoMessage):
        if environ.get('DEBUG_NO_TUI') == "1":
            log_monitor_message(MESSAGE_LOGGER, message)

    async def pre_process_event(self, previous_state: EngineMonitorMinOSState, event: COMMON_ENGINE_EVENT):
        if environ.get('DEBUG_NO_TUI') == "1":
            log_event(EVENT_LOGGER, event)

    def message_project(
        self,
        previous_state: EngineMonitorMinOSState,
        message: COMMON_INCOMING_VIDEO_MESSAGE
    ) -> Result[List[COMMON_ENGINE_EVENT], DIPClientError]:
        return self.multi_message_project([
            self.engine_lifecycle.handle_message,
            self.engine_minos_app.handle_message,
            self.engine_auth.handle_message,
        ], previous_state, message)

    def state_project(
        self,
        previous_state: EngineMonitorMinOSState,
        event: COMMON_ENGINE_EVENT
    ) -> EngineMonitorMinOSState:
        stream_state = self.engine_minos_app.state_project(previous_state, event)
        return stream_state

    async def effect_project(self, previous_state: EngineMonitorMinOSState, event: COMMON_ENGINE_EVENT):
        projections = [
            self.engine_lifecycle.effect_project,
            self.engine_minos_app.effect_project,
            self.engine_ping.effect_project,
            self.engine_auth.effect_project,
        ]
        return await Engine.multi_effect_project(projections, previous_state, event)

