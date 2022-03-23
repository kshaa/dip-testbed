import asyncio
import dataclasses
import sys
from dataclasses import dataclass
from typing import List, Any
from result import Result, Ok, Err
from src.domain.dip_client_error import DIPClientError
from src.domain.hardware_shared_event import AuthSucceeded
from src.domain.hardware_video_event import COMMON_ENGINE_EVENT
from src.domain.minos_chunker import MinOSChunker
from src.domain.minos_chunks import IndexedButtonChunk
from src.domain.minos_monitor_event import MinOSMonitorEvent, StartingTUI, AddingTUISideEffect, IndexButtonClicked, \
    ReceivedChunkBytes, LeftoverChanged, BadChunkReceived, GoodChunkReceived
from src.domain.monitor_message import StartTUI, AddTUISideEffect, IndexButtonClick, SerialMonitorMessageToAgent, \
    SerialMonitorMessageToClient, ReceiveChunks
from src.engine.monitor.minos.engine_monitor_minos_state import EngineMonitorMinOSState
from src.engine.monitor.minos.minos_app import MinOSApp


@dataclass
class EngineMonitorMinOSApp:
    @staticmethod
    def handle_message(
        previous_state: EngineMonitorMinOSState,
        message: Any
    ) -> Result[List[MinOSMonitorEvent], DIPClientError]:
        if isinstance(message, StartTUI):
            return Ok([StartingTUI()])
        if isinstance(message, AddTUISideEffect):
            return Ok([AddingTUISideEffect(message.event_handler)])
        if isinstance(message, IndexButtonClick):
            return Ok([IndexButtonClicked(message.button_index)])
        if isinstance(message, SerialMonitorMessageToClient):
            return Ok([ReceivedChunkBytes(previous_state.chunker_stream, message.content_bytes)])
        if isinstance(message, ReceiveChunks):
            events = [LeftoverChanged(message.leftover)]
            for chunk in message.chunks:
                chunk_result = MinOSChunker.parse_chunk(chunk)
                if isinstance(chunk_result, Err):
                    events.append(BadChunkReceived(chunk, chunk_result.value))
                else:
                    events.append(GoodChunkReceived(chunk_result.value))
            return Ok(events)
        return Ok([])

    def state_project(
        self,
        previous_state: EngineMonitorMinOSState,
        event: Any
    ) -> EngineMonitorMinOSState:
        if isinstance(event, AddingTUISideEffect):
            return dataclasses.replace(previous_state, event_handlers=previous_state.event_handlers + [event.event_handler])
        if isinstance(event, LeftoverChanged):
            return dataclasses.replace(previous_state, chunker_stream=event.leftover)
        return previous_state

    async def effect_project(self, previous_state: EngineMonitorMinOSState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, AuthSucceeded):
            await previous_state.base.incoming_message_queue.put(StartTUI())
            pass
        elif isinstance(event, StartingTUI):
            loop = asyncio.get_event_loop()
            loop.create_task(MinOSApp.run_with_state(previous_state))
        elif isinstance(event, IndexButtonClicked):
            chunk = IndexedButtonChunk(event.button_index).to_chunk()
            encoded = MinOSChunker.encode(chunk)
            await previous_state.base.outgoing_message_queue.put(SerialMonitorMessageToAgent(encoded))
        elif isinstance(event, ReceivedChunkBytes):
            chunks, leftover = MinOSChunker.decode_stream(event.old_stream + event.incoming)
            await previous_state.base.incoming_message_queue.put(ReceiveChunks(chunks, leftover))

        # No matter what is the event, also pass it to subscribed event handlers (TUI app components)
        for event_handler in previous_state.event_handlers:
            event_handler(event)
