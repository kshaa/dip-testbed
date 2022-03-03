"""Engine lifecycle functionality."""
from dataclasses import dataclass
from typing import List, Any
from result import Result, Ok
from src.domain.hardware_shared_event import LifecycleStarted, LifecycleEnded
from src.domain.hardware_shared_message import InternalStartLifecycle, InternalEndLifecycle
from src.engine.engine_state import EngineState
from src.domain.dip_client_error import DIPClientError


@dataclass
class EngineLifecycle:
    @staticmethod
    def handle_message(
        previous_state: EngineState,
        message: Any
    ) -> Result[List[Any], DIPClientError]:
        if isinstance(message, InternalStartLifecycle):
            return Ok([LifecycleStarted(previous_state)])
        elif isinstance(message, InternalEndLifecycle):
            return Ok([LifecycleEnded(message.reason)])
        else:
            return Ok([])

    async def effect_project(self, previous_state: EngineState, event: Any):
        if isinstance(event, LifecycleEnded):
            previous_state.base.death.grace(event.reason)
