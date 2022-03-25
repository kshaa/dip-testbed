from dataclasses import dataclass
from typing import Optional
from src.agent.agent import Agent
from src.agent.agent_config import AgentConfig
from src.domain.dip_client_error import DIPClientError
from src.domain.dip_runnable import DIPRunnable
from src.domain.fancy_byte import FancyByte
from src.domain.positive_integer import PositiveInteger
from src.engine.engine_auth import EngineAuth
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.engine.engine_state import EngineBase
from src.engine.monitor.minos.engine_monitor_minos import EngineMonitorMinOS
from src.engine.monitor.minos.engine_monitor_minos_app import EngineMonitorMinOSApp
from src.engine.monitor.minos.engine_monitor_minos_state import EngineMonitorMinOSState
from src.protocol import s11n_hybrid
from src.service.backend_config import UserPassAuthConfig
from src.service.managed_url import ManagedURL
from src.service.ws import WebSocket


@dataclass
class MonitorSerialMinOS(DIPRunnable):
    heartbeat_seconds: PositiveInteger
    auth: UserPassAuthConfig
    monitor_url: ManagedURL

    async def run(self) -> Optional[DIPClientError]:
        base = await EngineBase.build()
        engine_state = EngineMonitorMinOSState(
            base, self.auth, [], self.heartbeat_seconds, b"", False, "", "", FancyByte.fromInt(0).value)
        engine_lifecycle = EngineLifecycle()
        engine_ping = EnginePing()
        engine_minos_app = EngineMonitorMinOSApp()
        engine_auth = EngineAuth()
        engine = EngineMonitorMinOS(
            engine_state, engine_lifecycle, engine_ping, engine_minos_app, engine_auth)

        decoder = s11n_hybrid.MONITOR_LISTENER_INCOMING_MESSAGE_DECODER
        encoder = s11n_hybrid.MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER
        websocket = WebSocket(self.monitor_url, decoder, encoder)
        agent = Agent(AgentConfig(engine, websocket))

        return await agent.run()
