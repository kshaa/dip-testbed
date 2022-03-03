import asyncio
import unittest
from dataclasses import dataclass
from typing import Optional
from unittest import IsolatedAsyncioTestCase
from unittest.mock import MagicMock
from uuid import UUID
from result import Ok
from src.agent.agent import Agent
from src.agent.agent_config import AgentConfig
from src.agent.agent_error import AgentExecutionError
from src.domain.dip_client_error import DIPClientError
from src.domain.hardware_shared_message import InternalEndLifecycle, InternalStartLifecycle
from src.domain.managed_uuid import ManagedUUID
from src.engine.engine import Engine
from src.domain.hardware_control_event import COMMON_ENGINE_EVENT
from src.engine.engine_state import EngineState, ManagedQueue, EngineBase
from src.domain.death import Death
from src.domain.hardware_control_message import COMMON_OUTGOING_MESSAGE, COMMON_INCOMING_MESSAGE, \
    UploadMessage, UploadResultMessage
from src.service.ws import SocketInterface


@dataclass
class TestSocket(SocketInterface[COMMON_INCOMING_MESSAGE, COMMON_OUTGOING_MESSAGE]):
    socket_queue: asyncio.Queue


@dataclass
class TestEngineState(EngineState):
    base: EngineBase


@dataclass
class TestEngine(Engine[
    COMMON_INCOMING_MESSAGE,
    COMMON_OUTGOING_MESSAGE,
    TestEngineState,
    COMMON_ENGINE_EVENT,
    DIPClientError
]):
    async def start(self):
        await self.state.base.incoming_message_queue.put(InternalStartLifecycle())

    async def kill(self, reason: Optional[DIPClientError]):
        await self.state.base.incoming_message_queue.put(InternalEndLifecycle(reason))

class TestAgent(IsolatedAsyncioTestCase):
    """Test suite for agent"""

    async def test_agent(self):
        """Test agent works"""
        # Prepare agent
        death = Death()
        engine_incoming_queue = ManagedQueue.build()
        engine_outgoing_queue = ManagedQueue.build()
        engine_event_queue = ManagedQueue.build()
        engine_base = EngineBase(death, engine_incoming_queue, engine_outgoing_queue, engine_event_queue)
        state = TestEngineState(engine_base)
        engine = TestEngine(state)
        socket_incoming_queue = asyncio.Queue()
        socket_outgoing_queue = asyncio.Queue()
        socket = TestSocket(socket_incoming_queue)
        config = AgentConfig(engine, socket)
        agent = Agent(config)

        # Let socket just wrap its queue
        socket.connected = MagicMock(return_value=True)
        connect_result = asyncio.Future()
        connect_result.set_result(None)
        socket.connect = MagicMock(return_value=connect_result)
        socket.rx = socket_incoming_queue.get
        async def socket_tx(value):
            await socket_outgoing_queue.put(value)
            return None
        socket.tx = socket_tx
        disconnect_result = asyncio.Future()
        disconnect_result.set_result(None)
        socket.disconnect = MagicMock(return_value=disconnect_result)

        # Let engine ignore inputs
        processed_messages = []
        def message_project(previous_state, message):
            processed_messages.append(message)
            return Ok([])
        engine.message_project = message_project
        engine.state_project = MagicMock(return_value=state)
        effect_result = asyncio.Future()
        effect_result.set_result(None)
        engine.effect_project = MagicMock(return_value=effect_result)
        error_result = asyncio.Future()
        error_result.set_result(None)
        engine.error_project = MagicMock(return_value=error_result)

        # Let agent run
        agent_task = asyncio.create_task(agent.run())
        await asyncio.sleep(0.1)
        self.assertEqual(processed_messages, [InternalStartLifecycle()])
        processed_messages = []

        # Let agent receive socket message
        upload_message = UploadMessage(ManagedUUID(UUID("83678e9c-8c51-11ec-9358-073465fdea6a")))
        await socket_incoming_queue.put(Ok(upload_message))
        await asyncio.sleep(0.05)
        self.assertEqual(processed_messages, [upload_message])
        processed_messages = []

        # Let engine transmit outgoing message
        result_message = UploadResultMessage("Upload failed, hardware exploded")
        await engine_outgoing_queue.put(result_message)
        await asyncio.sleep(0.05)
        socket_output = await socket_outgoing_queue.get()
        self.assertEqual(socket_output, result_message)

        # Let agent receive engine message
        end_message = InternalEndLifecycle()
        await engine_incoming_queue.put(end_message)
        await asyncio.sleep(0.05)
        self.assertEqual(processed_messages, [end_message])
        processed_messages = []

        # Let agent die on engine death
        error = AgentExecutionError("Test finished")
        await asyncio.sleep(0.05)
        death.grace(error)
        agent_result = await agent_task
        self.assertEqual(agent_result, error)


if __name__ == '__main__':
    unittest.main()
