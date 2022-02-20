from typing import Optional
from src.domain.death import Death
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.engine.engine_common_state import EngineCommonState
from dataclasses import dataclass
from src.engine.engine_state import EngineBase
from src.service.backend import BackendServiceInterface
from src.service.managed_serial import ManagedSerial


@dataclass
class EngineNRF52BoardState:
    device_path: ExistingFilePath
    upload_baud_rate: PositiveInteger = PositiveInteger(115200)


@dataclass
class EngineNRF52State(EngineCommonState):
    base: EngineBase

    hardware_id: ManagedUUID
    backend: BackendServiceInterface
    heartbeat_seconds: PositiveInteger
    board_state: EngineNRF52BoardState

    active_serial: Optional[ManagedSerial] = None
    serial_death: Death = None
