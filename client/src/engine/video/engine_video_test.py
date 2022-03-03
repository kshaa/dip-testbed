import asyncio
import unittest
from uuid import UUID
from result import Err, Ok
from src.domain.death import Death
from src.domain.dip_client_error import GenericClientError
from src.domain.hardware_shared_event import LifecycleStarted, LifecycleEnded
from src.domain.hardware_shared_message import InternalEndLifecycle, InternalStartLifecycle, PingMessage
from src.domain.hardware_video_event import ReceivedChunk, StartingVideoStream, StartedStream
from src.domain.hardware_video_message import log_video_message, CameraSubscription, StreamSpawnSuccess, CameraChunk
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.engine.engine_state import ManagedQueue, EngineBase
from src.engine.video.engine_video import EngineVideo
from src.engine.video.engine_video_state import EngineVideoState
from src.engine.video.engine_video_stream import EngineVideoStream
from src.service.managed_url import ManagedURL
from src.service.managed_video_stream import ExistingStreamConfig, ManagedVideoStream
from src.util import log
from unittest import IsolatedAsyncioTestCase


class TestCommonEngine(IsolatedAsyncioTestCase):

    async def test_engine_scenario(self):
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

        OUT_LOGGER = log.timed_named_logger("outgoing_event")
        async def log_outgoing_until_death():
            while not death.gracing:
                death_or_outgoing = await death.or_awaitable(out_queue.get())
                if isinstance(death_or_outgoing, Err):
                    return
                log_video_message(OUT_LOGGER, death_or_outgoing.value)
        asyncio.create_task(log_outgoing_until_death())

        # Engine upload
        # engine_lifecycle = EngineLifecycle()
        # engine_upload = EngineUpload(backend)
        # engine_upload.upload = MagicMock(return_value=async_identity(None))
        # engine_ping = EnginePing()
        #
        # # Engine serial monitor
        # engine_serial_monitor = EngineSerialMonitor()
        # read_serial_memory = []
        # from_agent_bytes = b"from_agent"
        # to_agent_bytes = b"to_agent"
        # async def read_serial():
        #     read_serial_memory.append(())
        #     return Ok(from_agent_bytes)
        # serial_config = ManagedSerialConfig(
        #     receive_size=4096,
        #     baudrate=115200,
        #     timeout=1.3
        # )
        # mock_serial = ManagedSerial(serial_config)
        # mock_serial.read = read_serial
        # mock_serial.write = MagicMock(return_value=async_identity(Ok(None)))
        # connect_serial_memory = []
        # async def connect_serial(device_path: ExistingFilePath, config: ManagedSerialConfig):
        #     connect_serial_memory.append((device_path, config))
        #     return Ok(mock_serial)
        # engine_serial_monitor.connect = connect_serial

        # Engine state
        heartbeat_seconds: PositiveInteger = PositiveInteger(1)
        hardware_id: ManagedUUID = ManagedUUID(UUID("55245e30-8d81-11ec-95da-f71d056c3822"))
        base = EngineBase(death, in_queue, out_queue, event_queue)
        stream_url = ManagedURL.build("http://localhost:8081/webcam.ogg").value
        stream_config = ExistingStreamConfig(stream_url)
        state = EngineVideoState(
            base, hardware_id, heartbeat_seconds, stream_config, None, Death())

        # Engine lifecycle
        engine_lifecycle = EngineLifecycle()

        # Engine video stream
        def fake_stream(config):
            return ManagedVideoStream(config, None, None, None)
        async def spawn_stream(config):
            return Ok(fake_stream(config))
        video_chunk = b"video_chunk"
        async def read_chunk(stream):
            await asyncio.sleep(0.5)
            return Ok(video_chunk)
        engine_video_stream = EngineVideoStream()
        engine_video_stream.spawn_stream = spawn_stream
        engine_video_stream.read_chunk = read_chunk

        # Engine ping
        engine_ping = EnginePing()

        # Start engine
        engine = EngineVideo(state, engine_lifecycle, engine_ping, engine_video_stream)
        engine_task = asyncio.create_task(engine.run())

        # Trigger streaming
        subscription_message = CameraSubscription()
        await asyncio.sleep(0.05)
        await in_queue.put(subscription_message)
        await asyncio.sleep(0.5)

        # Kill engine
        await asyncio.sleep(0.5)
        death_reason = GenericClientError("Test finished")
        await engine.kill(death_reason)
        await engine_task
        await asyncio.sleep(0.1)

        # Check events, effects
        self.assertEqual(in_queue_memory, [
            InternalStartLifecycle(),
            CameraSubscription(),
            StreamSpawnSuccess(fake_stream(stream_config)),
            CameraChunk(video_chunk),
            InternalEndLifecycle(death_reason),
            CameraChunk(video_chunk)
        ])
        self.assertEqual(event_queue_memory, [
            LifecycleStarted(state),
            StartingVideoStream(stream_config),
            StartedStream(fake_stream(stream_config)),
            ReceivedChunk(video_chunk),
            LifecycleEnded(death_reason),
            ReceivedChunk(video_chunk)
        ])
        self.assertEqual(out_queue_memory, [
            CameraChunk(video_chunk),
            PingMessage()
        ])


if __name__ == '__main__':
    unittest.main()
