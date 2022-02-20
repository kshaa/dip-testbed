import asyncio
import unittest
from collections import Callable
from dataclasses import dataclass
from unittest.mock import MagicMock
from uuid import UUID
from result import Ok, Err
from src.domain.death import Death
from src.domain.dip_client_error import GenericClientError
from src.domain.existing_file_path import ExistingFilePath
from src.domain.hardware_control_message import UploadMessage, InternalStartLifecycle, InternalEndLifecycle, \
    InternalSucceededSoftwareDownload, InternalSucceededSoftwareUpload, UploadResultMessage, \
    InternalUploadBoardSoftware, PingMessage, SerialMonitorRequest, log_hardware_message, SerialMonitorRequestStop, \
    InternalSerialMonitorStarting, InternalStartedSerialMonitor, InternalReceivedSerialBytes, SerialMonitorResult
from src.domain.managed_uuid import ManagedUUID
from src.domain.monitor_message import SerialMonitorMessageToAgent, SerialMonitorMessageToClient, MonitorUnavailable
from src.domain.positive_integer import PositiveInteger
from src.engine.engine_common import EngineCommon
from src.engine.engine_common_state import EngineCommonState
from src.engine.engine_events import DownloadingBoardSoftware, LifecycleStarted, BoardSoftwareDownloadSuccess, \
    UploadingBoardSoftware, BoardUploadSuccess, LifecycleEnded, BoardState, SerialMonitorAboutToStart, \
    StartSerialMonitor, SerialMonitorAlreadyConfigured, SendingBoardBytes, ReceivedSerialBytes, StoppingSerialMonitor, \
    SerialMonitorStartSuccess
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.engine.engine_serial_monitor import EngineSerialMonitor, SerialBoard
from src.engine.engine_state import ManagedQueue, EngineState
from src.engine.engine_upload import EngineUpload
from src.service.backend import BackendServiceInterface
from src.service.backend_config import BackendConfig
from src.service.managed_serial import ManagedSerial
from src.service.managed_serial_config import ManagedSerialConfig
from src.util import log
from src.util.future import async_identity
from src.util.sh import src_relative_path
from unittest import IsolatedAsyncioTestCase


@dataclass
class TestBackend(BackendServiceInterface):
    pass


class TestCommonEngine:
    """This test is poor, because it's full of hardcoded timeouts, but it should be asynchronous"""

    @staticmethod
    async def engine_scenario(
        test: IsolatedAsyncioTestCase,
        board_state: SerialBoard,
        build_engine_state: Callable[
            [
                Death,
                ManagedQueue,
                ManagedQueue,
                ManagedQueue,
                ManagedUUID,
                BackendServiceInterface,
                PositiveInteger,
                SerialBoard
            ],
            EngineCommonState
        ],
        build_engine: Callable[
            [
                EngineState,
                EngineLifecycle,
                EngineUpload,
                EnginePing,
                EngineSerialMonitor
            ],
            EngineCommon
        ]
    ):
        # Engine base
        death = Death()
        in_queue_memory = []
        def in_queue_before_put(value):
            in_queue_memory.append(value)
        in_queue = ManagedQueue.build(in_queue_before_put)
        out_queue_memory = []
        def out_queue_before_put(value):
            out_queue_memory.append(value)
        out_queue = ManagedQueue.build(out_queue_before_put)
        event_queue_memory = []
        def event_queue_before_put(value):
            event_queue_memory.append(value)
        event_queue = ManagedQueue.build(event_queue_before_put)

        OUT_LOGGER = log.timed_named_logger("outgoing_hardware")
        async def log_outgoing_until_death():
            while not death.gracing:
                death_or_outgoing = await death.or_awaitable(out_queue.get())
                if isinstance(death_or_outgoing, Err):
                    return
                log_hardware_message(OUT_LOGGER, death_or_outgoing.value)
        asyncio.create_task(log_outgoing_until_death())

        # Backend
        backend_config: BackendConfig = BackendConfig(None, None)
        backend = TestBackend(backend_config)
        backend.software_download = lambda software_id: Ok(software_path)
        software_path = ExistingFilePath(src_relative_path("static/test/software.bin"))

        # Engine upload
        engine_lifecycle = EngineLifecycle()
        engine_upload = EngineUpload(backend)
        engine_upload.upload = MagicMock(return_value=async_identity(None))
        engine_ping = EnginePing()

        # Engine serial monitor
        engine_serial_monitor = EngineSerialMonitor()
        read_serial_memory = []
        from_agent_bytes = b"from_agent"
        to_agent_bytes = b"to_agent"
        async def read_serial():
            read_serial_memory.append(())
            return Ok(from_agent_bytes)
        serial_config = ManagedSerialConfig(
            receive_size=4096,
            baudrate=115200,
            timeout=1.3
        )
        mock_serial = ManagedSerial(serial_config)
        mock_serial.read = read_serial
        mock_serial.write = MagicMock(return_value=async_identity(Ok(None)))
        connect_serial_memory = []
        async def connect_serial(device_path: ExistingFilePath, config: ManagedSerialConfig):
            connect_serial_memory.append((device_path, config))
            return Ok(mock_serial)
        engine_serial_monitor.connect = connect_serial

        # Engine state
        heartbeat_seconds: PositiveInteger = PositiveInteger(1)
        hardware_id: ManagedUUID = ManagedUUID(UUID("55245e30-8d81-11ec-95da-f71d056c3822"))
        state = build_engine_state(
            death, in_queue, out_queue, event_queue, hardware_id, backend, heartbeat_seconds, board_state)

        # Start engine
        engine = build_engine(state, engine_lifecycle, engine_upload, engine_ping, engine_serial_monitor)
        engine_task = asyncio.create_task(engine.run())

        # Trigger upload
        upload_message = UploadMessage(UUID("094a89b4-8d84-11ec-95ea-73630d1316d7"))
        await asyncio.sleep(0.05)
        await in_queue.put(upload_message)

        # Trigger serial monitor, then re-request, then in-send bytes, then stop
        serial_request_message = SerialMonitorRequest(serial_config)
        await asyncio.sleep(0.05)
        await in_queue.put(serial_request_message)
        await asyncio.sleep(1.2)
        await in_queue.put(serial_request_message)
        await asyncio.sleep(0.05)
        to_agent_message = SerialMonitorMessageToAgent(to_agent_bytes)
        await in_queue.put(to_agent_message)
        await asyncio.sleep(0.05)
        serial_stop_message = SerialMonitorRequestStop()
        await in_queue.put(serial_stop_message)
        await asyncio.sleep(0.5)

        # Kill engine
        death_reason = GenericClientError("Test finished")
        await engine.kill(death_reason)
        await engine_task
        await asyncio.sleep(1)

        # Check events, effects
        test.assertTrue(len(read_serial_memory), 1)
        mock_serial.write.assert_called_with(to_agent_bytes)
        engine_upload.upload.assert_called_with(board_state, software_path)
        test.assertEqual(in_queue_memory, [
            InternalStartLifecycle(),
            upload_message,
            InternalSucceededSoftwareDownload(software_path),
            InternalUploadBoardSoftware(software_path),
            InternalSucceededSoftwareUpload(),
            serial_request_message,
            InternalSerialMonitorStarting(serial_config),
            InternalStartedSerialMonitor(mock_serial),
            serial_request_message,
            to_agent_message,
            serial_stop_message,
            InternalReceivedSerialBytes(from_agent_bytes),
            InternalEndLifecycle(death_reason)
        ])
        test.assertEqual(event_queue_memory, [
            LifecycleStarted(state),
            DownloadingBoardSoftware(upload_message.software_id),
            BoardSoftwareDownloadSuccess(software_path),
            UploadingBoardSoftware(software_path, board_state),
            BoardUploadSuccess(),
            SerialMonitorAboutToStart(serial_config),
            StartSerialMonitor(serial_config, board_state.device_path),
            SerialMonitorStartSuccess(mock_serial),
            SerialMonitorAlreadyConfigured(),
            SendingBoardBytes(to_agent_bytes),
            StoppingSerialMonitor(),
            ReceivedSerialBytes(from_agent_bytes),
            LifecycleEnded(death_reason)
        ])
        out_queue_memory_expectation = [
            UploadResultMessage(None),
            SerialMonitorResult(None),
            PingMessage(),
            SerialMonitorResult(None),
            MonitorUnavailable(reason='Hardware control stopped monitor'),
            SerialMonitorMessageToClient(from_agent_bytes)
        ]
        if out_queue_memory[-1] == PingMessage():
            # What a horrible hack
            out_queue_memory_expectation.append(PingMessage())
        test.assertEqual(out_queue_memory, out_queue_memory_expectation)


if __name__ == '__main__':
    unittest.main()
