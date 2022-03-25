from dataclasses import dataclass
from typing import List

from src.domain.fancy_byte import FancyByte
from src.domain.positive_integer import PositiveInteger
from src.engine.engine_auth import EngineAuthState
from src.engine.engine_ping import EnginePingState
from src.engine.engine_state import EngineBase, EngineState
from src.service.backend_config import UserPassAuthConfig


@dataclass
class EngineMonitorMinOSState(EngineState, EngineAuthState, EnginePingState):
    base: EngineBase
    auth: UserPassAuthConfig
    event_handlers: List
    heartbeat_seconds: PositiveInteger
    chunker_stream: bytes = b""
    is_text_mode: bool = False
    text_out: str = ""
    text_in: str = ""
    switches: FancyByte = FancyByte.fromInt(0).value
