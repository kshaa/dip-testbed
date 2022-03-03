from dataclasses import dataclass
from typing import Optional
from src.domain.death import Death
from src.domain.existing_file_path import ExistingFilePath
from src.engine.board.engine_common_state import EngineCommonState
from src.engine.engine_state import EngineBase
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.service.backend import BackendServiceInterface
from src.service.managed_serial import ManagedSerial


@dataclass
class EngineAnvylBoardState:
    device_name: str
    device_path: ExistingFilePath
    scan_chain_index: int


@dataclass
class EngineAnvylState(EngineCommonState):
    base: EngineBase

    hardware_id: ManagedUUID
    backend: BackendServiceInterface
    heartbeat_seconds: PositiveInteger
    board_state: EngineAnvylBoardState

    active_serial: Optional[ManagedSerial] = None
    serial_death: Death = None
