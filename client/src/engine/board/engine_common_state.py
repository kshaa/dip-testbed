#!/usr/bin/env python

from typing import Optional
from src.agent.agent_error import AgentExecutionError
from src.domain.death import Death
from src.engine.engine_auth import EngineAuth
from src.engine.engine_ping import EnginePingState
from src.engine.board.engine_serial_monitor import EngineSerialMonitorState, SerialBoard
from src.engine.engine_state import EngineState, ManagedQueue
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.service.backend import BackendServiceInterface
from src.service.backend_config import UserPassAuthConfig
from src.service.managed_serial import ManagedSerial


class EngineCommonState(EngineState, EnginePingState, EngineSerialMonitorState, EngineAuth):
    death: Death[AgentExecutionError]
    incoming_message_queue: ManagedQueue
    outgoing_message_queue: ManagedQueue
    event_queue: ManagedQueue

    hardware_id: ManagedUUID
    backend: BackendServiceInterface
    heartbeat_seconds: PositiveInteger
    board_state: SerialBoard

    active_serial: Optional[ManagedSerial]
    serial_death: Death

    auth: UserPassAuthConfig

