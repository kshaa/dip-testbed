import asyncio
import dataclasses
from dataclasses import dataclass
from os import environ
from typing import List, Any
from result import Result, Ok, Err

from src.domain.death import Death
from src.domain.dip_client_error import DIPClientError, NotAnError
from src.domain.hardware_shared_event import AuthSucceeded
from src.domain.hardware_shared_message import InternalEndLifecycle
from src.domain.hardware_video_event import COMMON_ENGINE_EVENT
from src.domain.minos_chunker import MinOSChunker
from src.domain.minos_chunks import IndexedButtonChunk, SwitchChunk, TextChunk, ParsedChunk
from src.domain.minos_monitor_event import MinOSMonitorEvent, StartingTUI, AddingTUISideEffect, IndexButtonClicked, \
    ReceivedChunkBytes, LeftoverChanged, BadChunkReceived, GoodChunkReceived, ModeSwitched, TextToAgent, \
    TextChanged, SwitchesChanged, SendingParsedChunk, MinOSSuiteTimedOut
from src.domain.monitor_message import StartTUI, AddTUISideEffect, SerialMonitorMessageToAgent, \
    SerialMonitorMessageToClient, ReceiveChunks, ButtonPress, SendParsedChunk, MinOSSuiteTimeout
from src.engine.engine_state import ManagedQueue
from src.engine.monitor.minos.engine_monitor_minos_state import EngineMonitorMinOSState
from src.engine.monitor.minos.minos_app import MinOSApp, button_keys, switch_keys
from src.engine.monitor.minos.minos_suite import MinOSSuite, MinOSSuitePacket
import time
from src.protocol.s11n_json import COMMON_MINOS_SUITE_ENCODER_JSON
import datetime


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
        if isinstance(message, SerialMonitorMessageToClient):
            return Ok([ReceivedChunkBytes(previous_state.chunker_stream, message.content_bytes)])
        if isinstance(message, SendParsedChunk):
            return Ok([SendingParsedChunk(message.parsed_chunk)])
        if isinstance(message, ReceiveChunks):
            events = [LeftoverChanged(message.leftover)]
            for chunk in message.chunks:
                chunk_result = MinOSChunker.parse_chunk(chunk)
                if isinstance(chunk_result, Err):
                    events.append(BadChunkReceived(chunk, chunk_result.value))
                else:
                    events.append(GoodChunkReceived(chunk_result.value))
            return Ok(events)
        if isinstance(message, ButtonPress):
            if message.key == "ctrl+i": # i.e. TAB
                return Ok([ModeSwitched(not previous_state.is_text_mode)])
            if previous_state.is_text_mode and message.key == "ctrl+h": # i.e. backspace
                return Ok([TextChanged(previous_state.text_out[:-1])])
            if previous_state.is_text_mode and message.key == "enter":
                return Ok([TextToAgent(previous_state.text_out), TextChanged("")])
            if previous_state.is_text_mode and message.key != "enter" and len(previous_state.text_out) < 32:
                return Ok([TextChanged(previous_state.text_out + message.key)])
            if not previous_state.is_text_mode and message.key in switch_keys:
                switch_index = switch_keys.index(message.key)
                return Ok([SwitchesChanged(previous_state.switches.toggle_bit(switch_index).value)])
            if not previous_state.is_text_mode and message.key in button_keys:
                button_index = button_keys.index(message.key)
                return Ok([IndexButtonClicked(button_index)])
        if isinstance(message, MinOSSuiteTimeout):
            return Ok([MinOSSuiteTimedOut()])
        return Ok([])

    def state_project(
        self,
        previous_state: EngineMonitorMinOSState,
        event: Any
    ) -> EngineMonitorMinOSState:
        if isinstance(event, StartingTUI) and previous_state.source_suite is not None:
            src = previous_state.source_suite
            time_ms = time.time() * 1000
            start_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            result_suite = MinOSSuite([], src.treshold_time, src.treshold_chunks, time_ms, start_timestamp)
            return dataclasses.replace(previous_state, result_suite=result_suite)
        if isinstance(event, AddingTUISideEffect):
            return dataclasses.replace(previous_state, event_handlers=previous_state.event_handlers + [event.event_handler])
        if isinstance(event, LeftoverChanged):
            return dataclasses.replace(previous_state, chunker_stream=event.leftover)
        if isinstance(event, ModeSwitched):
            return dataclasses.replace(previous_state, is_text_mode=event.is_text_mode)
        if isinstance(event, TextChanged):
            return dataclasses.replace(previous_state, text_out=event.text)
        if isinstance(event, SwitchesChanged):
            return dataclasses.replace(previous_state, switches=event.fancy_byte)
        if isinstance(event, GoodChunkReceived) and previous_state.result_suite is not None:
            received_chunks = list(filter(lambda c: not c.outgoing, previous_state.result_suite.chunks))
            treshold = previous_state.result_suite.treshold_chunks
            if 0 <= treshold <= len(received_chunks):
                return previous_state
            src = previous_state.result_suite
            time_ms = time.time() * 1000
            delta_ms = time_ms - previous_state.result_suite.start_time
            sent_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            new_chunk = MinOSSuitePacket(
                event.parsed_chunk,
                delta_ms,
                sent_timestamp,
                False
            )
            new_suite = dataclasses.replace(previous_state.result_suite, chunks=src.chunks + [new_chunk])
            return dataclasses.replace(previous_state, result_suite=new_suite)
        if isinstance(event, SendingParsedChunk) and previous_state.result_suite is not None:
            received_chunks = list(filter(lambda c: not c.outgoing, previous_state.result_suite.chunks))
            treshold = previous_state.result_suite.treshold_chunks
            if 0 <= treshold <= len(received_chunks):
                return previous_state
            src = previous_state.result_suite
            time_ms = time.time() * 1000
            delta_ms = time_ms - previous_state.result_suite.start_time
            sent_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            new_chunk = MinOSSuitePacket(
                event.parsed_chunk,
                delta_ms,
                sent_timestamp,
                True
            )
            new_suite = dataclasses.replace(previous_state.result_suite, chunks=src.chunks + [new_chunk])
            return dataclasses.replace(previous_state, result_suite=new_suite)
        return previous_state

    async def suite_chunk_queue(self, chunk: ParsedChunk, death: Death, sent_at: int, queue: ManagedQueue):
        timeout = sent_at / 1000
        death_or_outgoing = await death.or_awaitable(asyncio.sleep(timeout))
        if isinstance(death_or_outgoing, Err):
            return
        await queue.put(SendParsedChunk(chunk))

    async def suite_timeout(self, state_ref: EngineMonitorMinOSState):
        timeout = state_ref.source_suite.treshold_time / 1000
        death_or_outgoing = await state_ref.base.death.or_awaitable(asyncio.sleep(timeout))
        if isinstance(death_or_outgoing, Err):
            return
        await state_ref.base.incoming_message_queue.put(MinOSSuiteTimeout())

    async def effect_project(self, previous_state: EngineMonitorMinOSState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, AuthSucceeded):
            await previous_state.base.incoming_message_queue.put(StartTUI())
            pass
        elif isinstance(event, StartingTUI):
            debugging = environ.get('DEBUG_NO_TUI') == "1"
            is_suite = previous_state.source_suite is not None
            loop = asyncio.get_event_loop()
            if not (debugging or is_suite):
                loop.create_task(MinOSApp.run_with_state(previous_state))
            if is_suite:
                loop.create_task(self.suite_timeout(previous_state))
                for chunk in previous_state.source_suite.chunks:
                    if chunk.outgoing:
                        loop.create_task(self.suite_chunk_queue(
                            chunk.parsed_chunk, previous_state.base.death,
                            chunk.sent_at, previous_state.base.incoming_message_queue))
        elif isinstance(event, IndexButtonClicked):
            parsed_chunk = IndexedButtonChunk(event.button_index)
            await previous_state.base.incoming_message_queue.put(SendParsedChunk(parsed_chunk))
        elif isinstance(event, SwitchesChanged):
            parsed_chunk = SwitchChunk(event.fancy_byte)
            await previous_state.base.incoming_message_queue.put(SendParsedChunk(parsed_chunk))
        elif isinstance(event, ReceivedChunkBytes):
            chunks, garbage, leftover = MinOSChunker.decode_stream(event.old_stream + event.incoming)
            await previous_state.base.incoming_message_queue.put(ReceiveChunks(chunks, garbage, leftover))
        elif isinstance(event, TextToAgent):
            parsed_chunk = TextChunk(event.text)
            await previous_state.base.incoming_message_queue.put(SendParsedChunk(parsed_chunk))
        elif isinstance(event, SendingParsedChunk):
            chunk = event.parsed_chunk.to_chunk()
            encoded = MinOSChunker.encode(chunk)
            await previous_state.base.outgoing_message_queue.put(SerialMonitorMessageToAgent(encoded))
        if isinstance(event, GoodChunkReceived) or isinstance(event, MinOSSuiteTimedOut):
            if previous_state.result_suite is not None:
                received_chunks = list(filter(lambda c: not c.outgoing, previous_state.result_suite.chunks))
                treshold = previous_state.result_suite.treshold_chunks
                force_end = isinstance(event, MinOSSuiteTimedOut)
                if force_end or (0 <= treshold <= len(received_chunks)):
                    await previous_state.base.incoming_message_queue.put(InternalEndLifecycle(NotAnError(
                        COMMON_MINOS_SUITE_ENCODER_JSON.json_encode(previous_state.result_suite)
                    )))

        # No matter what is the event, also pass it to subscribed event handlers (TUI app components)
        for event_handler in previous_state.event_handlers:
            event_handler(previous_state, event)
