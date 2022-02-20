import unittest

from src.domain.death import Death
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.engine.board.nrf52.engine_nrf52 import EngineNRF52
from src.engine.board.nrf52.engine_nrf52_state import EngineNRF52BoardState, EngineNRF52State
from src.engine.board.nrf52.engine_nrf52_upload import EngineNRF52Upload, FIRMWARE_UPLOAD_PATH
from src.engine.engine_common_test import TestCommonEngine
from src.engine.engine_events import BoardState
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.engine.engine_serial_monitor import EngineSerialMonitor
from src.engine.engine_state import ManagedQueue, EngineBase
from src.engine.engine_upload import EngineUpload
from src.service.backend import BackendServiceInterface
from src.util.sh import src_relative_path
from unittest import IsolatedAsyncioTestCase


class TestNrf52(IsolatedAsyncioTestCase):
    """NRF52 client test suite"""

    def test_firmware_upload_args(self):
        """Test whether upload arguments are constructed properly"""
        reality = EngineNRF52Upload.firmware_upload_args("/home/me/code/nrf/run.hex", "/dev/tty0", 115200)
        upload_script_path = src_relative_path(FIRMWARE_UPLOAD_PATH)
        expectations = [
            'bash',
            '-c',
            f'{upload_script_path} -d "/dev/tty0" -b "115200" -f "/home/me/code/nrf/run.hex"']
        self.assertEqual(reality, expectations)

    async def test_engine(self):
        device_path = ExistingFilePath(src_relative_path("static/test/device"))
        board_state = EngineNRF52BoardState(device_path)

        def build_engine_state(
            death: Death,
            in_queue: ManagedQueue,
            out_queue: ManagedQueue,
            event_queue: ManagedQueue,
            hardware_id: ManagedUUID,
            backend: BackendServiceInterface,
            heartbeat_seconds: PositiveInteger,
            board_state: EngineNRF52BoardState
        ) -> EngineNRF52State:
            return EngineNRF52State(
                EngineBase(death, in_queue, out_queue, event_queue),
                hardware_id,
                backend,
                heartbeat_seconds,
                board_state
            )

        def build_engine(
            state: EngineNRF52State,
            engine_lifecycle: EngineLifecycle,
            engine_upload: EngineNRF52Upload,
            engine_ping: EnginePing,
            engine_serial_monitor: EngineSerialMonitor
        ) -> EngineNRF52:
            return EngineNRF52(state, engine_lifecycle, engine_upload, engine_ping, engine_serial_monitor)

        await TestCommonEngine.engine_scenario(self, board_state, build_engine_state, build_engine)

if __name__ == '__main__':
    unittest.main()
