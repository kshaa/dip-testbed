from typing import Optional
from src.domain.death import Death
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.engine.board.engine_common_state import EngineCommonState
from dataclasses import dataclass
from src.engine.engine_state import EngineBase
from src.service.backend import BackendServiceInterface
from src.service.backend_config import UserPassAuthConfig
from src.service.managed_serial import ManagedSerial


@dataclass
class EngineIcestickBoardState:
    device_name: str
    device_path: ExistingFilePath


@dataclass
class EngineIcestickState(EngineCommonState):
    base: EngineBase

    hardware_id: ManagedUUID
    backend: BackendServiceInterface
    heartbeat_seconds: PositiveInteger
    board_state: EngineIcestickBoardState

    auth: UserPassAuthConfig

    active_serial: Optional[ManagedSerial] = None
    serial_death: Death = None
