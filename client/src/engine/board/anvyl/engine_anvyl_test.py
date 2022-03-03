import unittest
from src.domain.death import Death
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.engine.board.anvyl.engine_anvyl import EngineAnvyl
from src.engine.board.anvyl.engine_anvyl_state import EngineAnvylState, EngineAnvylBoardState
from src.engine.board.anvyl.engine_anvyl_upload import EngineAnvylUpload, FIRMWARE_UPLOAD_PATH
from src.engine.board.engine_common_test import TestCommonEngine
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.engine.board.engine_serial_monitor import EngineSerialMonitor
from src.engine.engine_state import ManagedQueue, EngineState, EngineBase
from src.service.backend import BackendServiceInterface
from src.util.sh import src_relative_path
from unittest import IsolatedAsyncioTestCase


class TestAnvyl(IsolatedAsyncioTestCase):
    """Anvyl client test suite"""

    def test_firmware_upload_args(self):
        """Test whether upload arguments are constructed properly"""
        reality = EngineAnvylUpload.firmware_upload_args("/home/me/code/anvyl/run.hex", "Anvyl", 0)
        upload_script_path = src_relative_path(FIRMWARE_UPLOAD_PATH)
        expectations = [
            'bash',
            '-c',
            f'{upload_script_path} -d "Anvyl" -s "0" -f "/home/me/code/anvyl/run.hex"']
        self.assertEqual(reality, expectations)

    async def test_engine(self):
        device_path = ExistingFilePath(src_relative_path("static/test/device"))
        board_state = EngineAnvylBoardState("Anvyl", device_path, 0)

        def build_engine_state(
            death: Death,
            in_queue: ManagedQueue,
            out_queue: ManagedQueue,
            event_queue: ManagedQueue,
            hardware_id: ManagedUUID,
            backend: BackendServiceInterface,
            heartbeat_seconds: PositiveInteger,
            board_state: EngineAnvylBoardState
        ) -> EngineAnvylState:
            return EngineAnvylState(
                EngineBase(death, in_queue, out_queue, event_queue),
                hardware_id,
                backend,
                heartbeat_seconds,
                board_state
            )

        def build_engine(
            state: EngineState,
            engine_lifecycle: EngineLifecycle,
            engine_upload: EngineAnvylUpload,
            engine_ping: EnginePing,
            engine_serial_monitor: EngineSerialMonitor
        ) -> EngineAnvyl:
            return EngineAnvyl(state, engine_lifecycle, engine_upload, engine_ping, engine_serial_monitor)

        await TestCommonEngine.engine_scenario(self, board_state, build_engine_state, build_engine)


if __name__ == '__main__':
    unittest.main()
