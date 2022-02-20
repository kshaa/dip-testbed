"""Engine lifecycle functionality."""
from dataclasses import dataclass
from typing import List
from result import Result, Ok
from src.engine.engine_events import COMMON_ENGINE_EVENT, LifecycleStarted, LifecycleEnded
from src.engine.engine_state import EngineState
from src.domain.dip_client_error import DIPClientError
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, InternalStartLifecycle, InternalEndLifecycle


@dataclass
class EngineLifecycle:
    @staticmethod
    def handle_message(
        previous_state: EngineState,
        message: COMMON_INCOMING_MESSAGE
    ) -> Result[List[COMMON_ENGINE_EVENT], DIPClientError]:
        if isinstance(message, InternalStartLifecycle):
            return Ok([LifecycleStarted(previous_state)])
        elif isinstance(message, InternalEndLifecycle):
            return Ok([LifecycleEnded(message.reason)])
        else:
            return Ok([])

    async def effect_project(self, previous_state: EngineState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, LifecycleEnded):
            previous_state.base.death.grace(event.reason)
