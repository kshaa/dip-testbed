import unittest
from src.domain.death import Death
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.engine.board.fake.engine_fake import EngineFakeBoardState, EngineFakeState, EngineFake, EngineFakeUpload, \
    EngineFakeSerialMonitor
from src.engine.board.engine_common_test import TestCommonEngine
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.engine.engine_state import ManagedQueue, EngineBase
from src.service.backend import BackendServiceInterface
from src.util.sh import src_relative_path
from unittest import IsolatedAsyncioTestCase


class TestFake(IsolatedAsyncioTestCase):
    async def test_engine(self):
        device_path = ExistingFilePath(src_relative_path("static/test/device"))
        board_state = EngineFakeBoardState(device_path)

        def build_engine_state(
            death: Death,
            in_queue: ManagedQueue,
            out_queue: ManagedQueue,
            event_queue: ManagedQueue,
            hardware_id: ManagedUUID,
            backend: BackendServiceInterface,
            heartbeat_seconds: PositiveInteger,
            board_state: EngineFakeBoardState
        ) -> EngineFakeState:
            return EngineFakeState(
                EngineBase(death, in_queue, out_queue, event_queue),
                hardware_id,
                backend,
                heartbeat_seconds,
                board_state
            )

        def build_engine(
            state: EngineFakeState,
            engine_lifecycle: EngineLifecycle,
            engine_upload: EngineFakeUpload,
            engine_ping: EnginePing,
            engine_serial_monitor: EngineFakeSerialMonitor
        ) -> EngineFake:
            return EngineFake(state, engine_lifecycle, engine_upload, engine_ping, engine_serial_monitor)

        await TestCommonEngine.engine_scenario(self, board_state, build_engine_state, build_engine)

if __name__ == '__main__':
    unittest.main()
