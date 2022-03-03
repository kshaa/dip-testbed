#!/usr/bin/env python
"""Engine which reacts to server commands and supervises microcontroller"""
import asyncio
import dataclasses
from dataclasses import dataclass
from typing import List, Optional
from result import Result, Ok, Err
from src.domain.death import Death
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.hardware_shared_event import LifecycleEnded
from src.domain.hardware_video_message import COMMON_INCOMING_VIDEO_MESSAGE, CameraSubscription, StreamSpawnFailure, \
    StreamSpawnSuccess, FinishedEndingStream, StopBroadcasting, CameraUnavailable, CameraChunk
from src.engine.engine_state import EngineBase
from src.domain.hardware_video_event import COMMON_ENGINE_EVENT, StartedStream, StartingVideoStream, EndedStream, \
    EndingStream, ReceivedChunk
from src.service.managed_video_stream import VideoStreamConfig, ManagedVideoStream


class EngineVideoStreamState:
    base: EngineBase
    initial_stream_config: VideoStreamConfig
    stream: Optional[ManagedVideoStream]
    stream_death: Death


@dataclass
class EngineVideoStream:

    @staticmethod
    def handle_message(
        previous_state: EngineVideoStreamState,
        message: COMMON_INCOMING_VIDEO_MESSAGE
    ) -> Result[List[COMMON_ENGINE_EVENT], DIPClientError]:
        if isinstance(message, CameraSubscription):
            return Ok([StartingVideoStream(previous_state.initial_stream_config)])
        elif isinstance(message, StreamSpawnSuccess):
            return Ok([StartedStream(message.stream, Death())])
        elif isinstance(message, CameraChunk):
            return Ok([ReceivedChunk(message.chunk)])
        elif isinstance(message, StreamSpawnFailure):
            return Ok([EndingStream(GenericClientError("Failed to initialize stream"))])
        elif isinstance(message, StopBroadcasting):
            return Ok([EndingStream(GenericClientError("No one is listening"))])
        elif isinstance(message, FinishedEndingStream):
            return Ok([EndedStream()])
        return Ok([])

    @staticmethod
    def state_project(previous_state: EngineVideoStreamState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, StartedStream):
            return dataclasses.replace(previous_state, stream=event.stream, stream_death=event.death)
        elif isinstance(event, EndedStream):
            return dataclasses.replace(previous_state, stream=None)
        return previous_state

    @staticmethod
    async def read_chunk(stream: ManagedVideoStream) -> Result[bytes, DIPClientError]:
        return await stream.read_chunk()

    async def stream_until_death(
        self,
        previous_state: EngineVideoStreamState,
        stream: ManagedVideoStream,
        stream_death: Death
    ):
        in_queue = previous_state.base.incoming_message_queue
        engine_death = previous_state.base.death
        while not engine_death.gracing and not stream_death.gracing:
            # Free up event loop for incoming messages
            await asyncio.sleep(0.01)

            # Read stream chunks
            death_or_death_or_result = await engine_death.or_awaitable(
                stream_death.or_awaitable(self.read_chunk(stream)))

            # Handle potential death (and stop receiving)
            if isinstance(death_or_death_or_result, Err) or isinstance(death_or_death_or_result.value, Err):
                return
            chunk_result = death_or_death_or_result.value.value

            # Handle video stream chunk read failure (and stop receiving)
            if isinstance(chunk_result, Err):
                await in_queue.put(CameraUnavailable(chunk_result.value))
                return

            # Handle non-empty serial read (and continue)
            received_bytes = chunk_result.value
            if received_bytes is not None and len(received_bytes) > 0:
                await in_queue.put(CameraChunk(received_bytes))

    async def spawn_stream(self, config: VideoStreamConfig) -> Result[ManagedVideoStream, DIPClientError]:
        return await ManagedVideoStream.spawn_stream(config)

    async def effect_project(self, previous_state: EngineVideoStreamState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, StartingVideoStream):
            # Kill old stream
            if previous_state.stream_death is not None:
                previous_state.stream_death.grace(GenericClientError("New subscriber, new stream"))
            if previous_state.stream is not None:
                await previous_state.stream.end()
            # Start new stream
            stream_result = await self.spawn_stream(event.config)
            if isinstance(stream_result, Err):
                await previous_state.base.outgoing_message_queue.put(CameraUnavailable(stream_result.value))
                await previous_state.base.incoming_message_queue.put(StreamSpawnFailure(stream_result.value))
            else:
                await previous_state.base.incoming_message_queue.put(StreamSpawnSuccess(stream_result.value))
        elif isinstance(event, EndingStream):
            if previous_state.stream is not None:
                await previous_state.stream.end()
            await previous_state.base.incoming_message_queue.put(FinishedEndingStream())
        elif isinstance(event, LifecycleEnded):
            if previous_state.stream is not None:
                await previous_state.stream.end()
            previous_state.stream_death.grace()
        elif isinstance(event, StartedStream):
            await self.stream_until_death(previous_state, event.stream, event.death)
        elif isinstance(event, ReceivedChunk):
            await previous_state.base.outgoing_message_queue.put(CameraChunk(event.chunk))
