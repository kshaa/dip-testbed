"""Video Stream engine functionality."""
from dataclasses import dataclass
from typing import List, Optional
from result import Result
from src.domain.dip_client_error import DIPClientError
from src.domain.hardware_video_message import COMMON_INCOMING_VIDEO_MESSAGE, COMMON_OUTGOING_VIDEO_MESSAGE, \
    HardwareVideoMessage, log_video_message, InternalStartLifecycle, InternalEndLifecycle
from src.engine.engine import Engine
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.domain.hardware_video_event import COMMON_ENGINE_EVENT, log_event
from src.engine.video.engine_video_state import EngineVideoState
from src.engine.video.engine_video_stream import EngineVideoStream
from src.util import log

HARDWARE_LOGGER = log.timed_named_logger("incoming_engine")
EVENT_LOGGER = log.timed_named_logger("event")


@dataclass
class EngineVideo(Engine[
    COMMON_INCOMING_VIDEO_MESSAGE,
    COMMON_OUTGOING_VIDEO_MESSAGE,
    EngineVideoState,
    COMMON_ENGINE_EVENT,
    DIPClientError
]):
    engine_lifecycle: EngineLifecycle
    engine_ping: EnginePing
    engine_video_stream: EngineVideoStream

    async def start(self):
        await self.state.base.incoming_message_queue.put(InternalStartLifecycle())

    async def kill(self, reason: Optional[DIPClientError]):
        await self.state.base.incoming_message_queue.put(InternalEndLifecycle(reason))

    async def pre_process_message(self, previous_state: EngineVideoState, message: HardwareVideoMessage):
        log_video_message(HARDWARE_LOGGER, message)

    async def pre_process_event(self, previous_state: EngineVideoState, event: COMMON_ENGINE_EVENT):
        log_event(EVENT_LOGGER, event)

    def message_project(
        self,
        previous_state: EngineVideoState,
        message: COMMON_INCOMING_VIDEO_MESSAGE
    ) -> Result[List[COMMON_ENGINE_EVENT], DIPClientError]:
        return self.multi_message_project([
            self.engine_lifecycle.handle_message,
            self.engine_video_stream.handle_message,
        ], previous_state, message)

    def state_project(self, previous_state: EngineVideoState, event: COMMON_ENGINE_EVENT) -> EngineVideoState:
        stream_state = self.engine_video_stream.state_project(previous_state, event)
        return stream_state

    async def effect_project(self, previous_state: EngineVideoState, event: COMMON_ENGINE_EVENT):
        projections = [
            self.engine_lifecycle.effect_project,
            self.engine_video_stream.effect_project,
            self.engine_ping.effect_project,
        ]
        return await Engine.multi_effect_project(projections, previous_state, event)

