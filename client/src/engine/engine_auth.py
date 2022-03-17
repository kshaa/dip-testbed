"""Engine auth functionality."""
from dataclasses import dataclass
from typing import List, Any
from result import Result, Ok
from src.domain.hardware_shared_event import StartingAuth, AuthSucceeded, AuthFailed
from src.domain.hardware_shared_message import InternalStartLifecycle, AuthResult, AuthRequest, InternalEndLifecycle
from src.engine.engine_state import EngineState, EngineBase
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.service.backend_config import UserPassAuthConfig


class EngineAuthState:
    base: EngineBase
    auth: UserPassAuthConfig


@dataclass
class EngineAuth:
    @staticmethod
    def handle_message(
        previous_state: EngineAuthState,
        message: Any
    ) -> Result[List[Any], DIPClientError]:
        if isinstance(message, InternalStartLifecycle):
            return Ok([StartingAuth(previous_state.auth)])
        elif isinstance(message, AuthResult):
            if message.error is None:
                return Ok([AuthSucceeded()])
            else:
                return Ok([AuthFailed(message.error)])
        else:
            return Ok([])

    async def effect_project(self, previous_state: EngineState, event: Any):
        if isinstance(event, StartingAuth):
            await previous_state.base.outgoing_message_queue.put(
                AuthRequest(event.auth.username, event.auth.password))
        elif isinstance(event, AuthFailed):
            await previous_state.base.incoming_message_queue.put(
                InternalEndLifecycle(GenericClientError(f"Auth failed: {event.reason}")))
