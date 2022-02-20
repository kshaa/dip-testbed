from typing import Optional
from result import Result, Ok
from src.domain.death import Death
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.engine.engine_common import EngineCommon
from src.engine.engine_common_state import EngineCommonState
from src.engine.engine_events import COMMON_ENGINE_EVENT
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, COMMON_OUTGOING_MESSAGE
from src.engine.engine_serial_monitor import EngineSerialMonitor
from src.engine.engine_state import EngineBase
from src.engine.engine_upload import EngineUpload
from src.service.backend import BackendServiceInterface
from src.service.managed_serial import ManagedSerial
from src.service.managed_serial_config import ManagedSerialConfig
from src.util.sh import src_relative_path


@dataclass
class EngineFakeBoardState:
    device_path: ExistingFilePath = ExistingFilePath(src_relative_path("static/test/device"))


@dataclass
class EngineFakeState(EngineCommonState):
    base: EngineBase

    hardware_id: ManagedUUID
    backend: BackendServiceInterface
    heartbeat_seconds: PositiveInteger
    board_state: EngineFakeBoardState

    active_serial: Optional[ManagedSerial] = None
    serial_death: Death = None


@dataclass
class EngineFakeUpload(EngineUpload):
    @staticmethod
    async def upload(
        state: EngineFakeBoardState,
        file: ExistingFilePath
    ) -> Optional[DIPClientError]:
        return None


@dataclass
class EngineFakeSerialMonitor(EngineSerialMonitor):
    time_since_read: float = 0

    async def connect(
        self,
        device_path: ExistingFilePath,
        config: ManagedSerialConfig
    ) -> Result[ManagedSerial, DIPClientError]:
        return Ok(ManagedSerial(config, None))

    async def read(self, active_serial: ManagedSerial) -> Result[bytes, DIPClientError]:
        if self.time_since_read > 1:
            self.time_since_read = 0
            return Ok(b"to_client")
        else:
            self.time_since_read += active_serial.config.timeout
            return Ok(b"")

    async def write(self, active_serial: ManagedSerial, value: bytes) -> Result[type(None), DIPClientError]:
        return Ok()


@dataclass
class EngineFake(EngineCommon[
    COMMON_INCOMING_MESSAGE,
    COMMON_OUTGOING_MESSAGE,
    EngineFakeState,
    COMMON_ENGINE_EVENT,
    DIPClientError
]):
    engine_serial_monitor: EngineFakeSerialMonitor
    engine_upload: EngineFakeUpload
