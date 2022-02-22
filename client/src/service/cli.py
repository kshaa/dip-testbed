#!/usr/bin/env python
"""Command line interface definition for agent"""
import asyncio
import sys
from typing import Tuple, Optional, List, Union, TypeVar, Any, Awaitable
from result import Err, Result, Ok
from rich.table import Table
from src.agent.agent import Agent
from src.agent.agent_config import AgentConfig
from src.domain.backend_entity import User, Hardware, Software
from src.domain.dip_runnable import DIPRunnable
from src.engine.board.anvyl.engine_anvyl import EngineAnvyl
from src.engine.board.anvyl.engine_anvyl_state import EngineAnvylState, EngineAnvylBoardState
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.engine.board.anvyl.engine_anvyl_upload import EngineAnvylUpload
from src.engine.board.fake.engine_fake import EngineFakeBoardState, EngineFakeState, EngineFakeUpload, \
    EngineFakeSerialMonitor, EngineFake
from src.engine.board.nrf52.engine_nrf52 import EngineNRF52
from src.engine.board.nrf52.engine_nrf52_state import EngineNRF52State, EngineNRF52BoardState
from src.engine.board.nrf52.engine_nrf52_upload import EngineNRF52Upload
from src.engine.engine_lifecycle import EngineLifecycle
from src.engine.engine_ping import EnginePing
from src.engine.engine_serial_monitor import EngineSerialMonitor
from src.engine.engine_state import ManagedQueue, EngineBase
from src.monitor.monitor_serial import MonitorSerial
from src.monitor.monitor_type import MonitorType
from src.protocol import s11n_hybrid, s11n_json
from src.protocol.codec_json import JSON, EncoderJSON
from src.protocol.s11n_hybrid import COMMON_INCOMING_MESSAGE_DECODER, COMMON_INCOMING_MESSAGE_ENCODER, \
    COMMON_OUTGOING_MESSAGE_ENCODER
from src.protocol.s11n_rich import RichEncoder
from src.service.backend import BackendConfig, BackendService, BackendServiceInterface
from src.service.managed_url import ManagedURL
from src.service.ws import WebSocket
from src.util import log
from rich import print as richprint, print_json
from src.util.rich_util import print_error, print_success
from src.util.sh import src_relative_path

E = TypeVar('E')
LOGGER = log.timed_named_logger("cli")
VALUE_CONTENT = Union[Table, JSON]
RESULT_CONTENT = Result[Union[Table, JSON], DIPClientError]


class CLIInterface:
    @staticmethod
    def build_agent_nrf52(
            hardware_id_str: str,
            control_server_str: str,
            static_server_str: str,
            heartbeat_seconds: int,
            device_path_str: str
    ) -> Result[Agent, DIPClientError]:
        pass

    @staticmethod
    def agent_anvyl(
            hardware_id_str: str,
            control_server_str: str,
            static_server_str: str,
            heartbeat_seconds: int,
            device_name_str: str,
            scan_chain_index: int,
            device_path_str: str
    ) -> Result[Agent, DIPClientError]:
        pass

    @staticmethod
    def user_list(static_server_str: str) -> Result[List[User], DIPClientError]:
        pass

    @staticmethod
    def user_create(
        static_server_str: str,
        username: str,
        password: str
    ) -> Result[User, DIPClientError]:
        pass

    @staticmethod
    def hardware_list(static_server_str: str) -> Result[List[Hardware], DIPClientError]:
        pass

    @staticmethod
    def hardware_create(
            static_server_str: str,
            username: str,
            password: str,
            hardware_name: str
    ) -> Result[Hardware, DIPClientError]:
        pass

    @staticmethod
    def software_list(static_server_str: str) -> Result[List[Software], DIPClientError]:
        pass

    @staticmethod
    def software_upload(
            static_server_str: str,
            username: str,
            password: str,
            software_name: str,
            file_path: str,
    ) -> Result[Software, DIPClientError]:
        pass

    @staticmethod
    def software_download(
            static_server_str: str,
            software_id_str: str,
            file_path: str
    ) -> Result[ExistingFilePath, DIPClientError]:
        pass

    @staticmethod
    def hardware_software_upload(
            static_server_str: str,
            hardware_id_str: str,
            software_id_str: str
    ) -> Optional[DIPClientError]:
        pass

    @staticmethod
    def hardware_serial_monitor(
            control_server_str: str,
            hardware_id_str: str,
            monitor_type_str: str,
            monitor_script_path_str: str
    ):
        pass

    @staticmethod
    def execute_runnable_result(agent_result: Result[DIPRunnable, DIPClientError]):
        pass

    @staticmethod
    def execute_table_result(
            json_output: bool,
            result: Result[List[E], DIPClientError],
            json_encoder: EncoderJSON,
            rich_encoder: RichEncoder
    ):
        pass

    @staticmethod
    def execute_optional_result(
        json_output: bool,
        result: Optional[DIPClientError],
        success_title: str
    ):
        pass


class CLI(CLIInterface):
    @staticmethod
    def parsed_backend(
            control_server_str: Optional[str],
            static_server_str: Optional[str],
    ) -> Result[BackendServiceInterface, DIPClientError]:
        if control_server_str is None and static_server_str is None:
            return Err(GenericClientError("Backend service requires either static or control URL"))

        if control_server_str is None:
            control_server = None
        else:
            control_server_result = ManagedURL.build(control_server_str)
            if isinstance(control_server_result, Err): return Err(control_server_result.value.of_type("control server"))
            control_server = control_server_result.value

        if static_server_str is None:
            static_server = None
        else:
            static_server_result = ManagedURL.build(static_server_str)
            if isinstance(static_server_result, Err): return Err(static_server_result.value.of_type("static server"))
            static_server = static_server_result.value

        return Ok(BackendService(BackendConfig(control_server, static_server)))

    @staticmethod
    def parsed_agent_input(
            hardware_id_str: str,
            control_server_str: str,
            static_server_str: str,
            heartbeat_seconds: int,
            device_path_str: str
    ) -> Result[
        Tuple[ManagedUUID, PositiveInteger, BackendServiceInterface, ManagedURL, ExistingFilePath],
        DIPClientError
    ]:
        hardware_id_result = ManagedUUID.build(hardware_id_str)
        if isinstance(hardware_id_result, Err): return Err(hardware_id_result.value.of_type("hardware"))

        control_server_result = ManagedURL.build(control_server_str)
        if isinstance(control_server_result, Err): return Err(control_server_result.value.of_type("control server"))

        static_server_result = ManagedURL.build(static_server_str)
        if isinstance(static_server_result, Err): return Err(static_server_result.value.of_type("static server"))

        heartbeat_seconds_result = PositiveInteger.build(heartbeat_seconds)
        if isinstance(heartbeat_seconds_result, Err): return Err(heartbeat_seconds_result.value.of_type("heartbeat"))

        backend_result = CLI.parsed_backend(control_server_str, static_server_str)
        if isinstance(backend_result, Err): return Err(backend_result.value)

        control_url_result = backend_result.value.hardware_control_url(hardware_id_result.value)
        if isinstance(control_url_result, Err): return Err(control_url_result.value)

        device_path_result = ExistingFilePath.build(device_path_str)
        if isinstance(device_path_result, Err): return Err(device_path_result.value.of_type("device"))

        return Ok((
            hardware_id_result.value,
            heartbeat_seconds_result.value,
            backend_result.value,
            control_url_result.value,
            device_path_result.value
        ))

    @staticmethod
    async def agent_nrf52(
            hardware_id_str: str,
            control_server_str: str,
            static_server_str: str,
            heartbeat_seconds: int,
            device_path_str: str
    ) -> Result[Agent, DIPClientError]:
        # Common agent input
        common_agent_input_result: Result = CLI.parsed_agent_input(
            hardware_id_str, control_server_str, static_server_str, heartbeat_seconds, device_path_str)
        if isinstance(common_agent_input_result, Err): return common_agent_input_result
        (hardware_id, heartbeat_seconds, backend, hardware_control_url, device_path) = \
            common_agent_input_result.value

        # Engine
        base = await EngineBase.build()
        board_state = EngineNRF52BoardState(device_path)
        engine_state = EngineNRF52State(base, hardware_id, backend, heartbeat_seconds, board_state)
        engine_lifecycle = EngineLifecycle()
        engine_upload = EngineNRF52Upload(backend)
        engine_ping = EnginePing()
        engine_serial_monitor = EngineSerialMonitor()
        engine = EngineNRF52(engine_state, engine_lifecycle, engine_upload, engine_ping, engine_serial_monitor)

        # Agent with engine construction
        encoder = COMMON_OUTGOING_MESSAGE_ENCODER
        decoder = COMMON_INCOMING_MESSAGE_DECODER
        websocket = WebSocket(hardware_control_url, decoder, encoder)

        return Ok(Agent(AgentConfig(engine, websocket)))

    @staticmethod
    async def agent_anvyl(
        hardware_id_str: str,
        control_server_str: str,
        static_server_str: str,
        heartbeat_seconds: int,
        device_name_str: str,
        scan_chain_index: int,
        device_path_str: str
    ) -> Result[Agent, DIPClientError]:
        # Common agent input
        common_agent_input_result: Result = CLI.parsed_agent_input(
            hardware_id_str, control_server_str, static_server_str, heartbeat_seconds, device_path_str)
        if isinstance(common_agent_input_result, Err): return common_agent_input_result
        (hardware_id, heartbeat_seconds, backend, hardware_control_url, device_path) = \
            common_agent_input_result.value

        # Engine
        base = await EngineBase.build()
        board_state = EngineAnvylBoardState(device_name_str, device_path, scan_chain_index)
        engine_state = EngineAnvylState(base, hardware_id, backend, heartbeat_seconds, board_state)
        engine_lifecycle = EngineLifecycle()
        engine_upload = EngineAnvylUpload(backend)
        engine_ping = EnginePing()
        engine_serial_monitor = EngineSerialMonitor()
        engine = EngineAnvyl(engine_state, engine_lifecycle, engine_upload, engine_ping, engine_serial_monitor)

        # Agent with engine construction
        encoder = COMMON_OUTGOING_MESSAGE_ENCODER
        decoder = COMMON_INCOMING_MESSAGE_DECODER
        websocket = WebSocket(hardware_control_url, decoder, encoder)

        return Ok(Agent(AgentConfig(engine, websocket)))

    @staticmethod
    async def agent_fake(
        hardware_id_str: str,
        control_server_str: str,
        static_server_str: str,
        heartbeat_seconds: int
    ) -> Result[Agent, DIPClientError]:
        # Common agent input
        device_path = ExistingFilePath(src_relative_path("static/test/device"))
        common_agent_input_result: Result = CLI.parsed_agent_input(
            hardware_id_str, control_server_str, static_server_str, heartbeat_seconds, device_path.value)
        if isinstance(common_agent_input_result, Err): return common_agent_input_result
        (hardware_id, heartbeat_seconds, backend, hardware_control_url, device_path) = \
            common_agent_input_result.value

        # Engine
        base = await EngineBase.build()
        board_state = EngineFakeBoardState(device_path)
        engine_state = EngineFakeState(base, hardware_id, backend, heartbeat_seconds, board_state)
        engine_lifecycle = EngineLifecycle()
        engine_upload = EngineFakeUpload(backend)
        engine_ping = EnginePing()
        engine_serial_monitor = EngineFakeSerialMonitor()
        engine = EngineFake(engine_state, engine_lifecycle, engine_upload, engine_ping, engine_serial_monitor)

        # Agent with engine construction
        encoder = COMMON_OUTGOING_MESSAGE_ENCODER
        decoder = COMMON_INCOMING_MESSAGE_DECODER
        websocket = WebSocket(hardware_control_url, decoder, encoder)

        return Ok(Agent(AgentConfig(engine, websocket)))

    @staticmethod
    def user_list(static_server_str: str) -> Result[List[User], DIPClientError]:
        backend_result = CLI.parsed_backend(None, static_server_str)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.user_list()

    @staticmethod
    def user_create(
        static_server_str: str,
        username: str,
        password: str
    ) -> Result[User, DIPClientError]:
        backend_result = CLI.parsed_backend(None, static_server_str)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.user_create(username, password)

    @staticmethod
    def hardware_list(static_server_str: str) -> Result[List[Hardware], DIPClientError]:
        backend_result = CLI.parsed_backend(None, static_server_str)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.hardware_list()

    @staticmethod
    def hardware_create(
        static_server_str: str,
        username: str,
        password: str,
        hardware_name: str
    ) -> Result[Hardware, DIPClientError]:
        backend_result = CLI.parsed_backend(None, static_server_str)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.hardware_create(username, password, hardware_name)

    @staticmethod
    def software_list(static_server_str: str) -> Result[List[Software], DIPClientError]:
        backend_result = CLI.parsed_backend(None, static_server_str)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.software_list()

    @staticmethod
    def software_upload(
        static_server_str: str,
        username: str,
        password: str,
        software_name: str,
        file_path: str,
    ) -> Result[Software, DIPClientError]:
        backend_result = CLI.parsed_backend(None, static_server_str)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        file_result = ExistingFilePath.build(file_path)
        if isinstance(file_result, Err): return Err(file_result.value.of_type("software"))
        return backend_result.value.software_upload(username, password, software_name, file_result.value)

    @staticmethod
    def software_download(
        static_server_str: str,
        software_id_str: str,
        file_path: str
    ) -> Result[ExistingFilePath, DIPClientError]:
        backend_result = CLI.parsed_backend(None, static_server_str)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        software_id_result = ManagedUUID.build(software_id_str)
        if isinstance(software_id_result, Err): return Err(software_id_result.value.of_type("software"))
        return backend_result.value.software_download(software_id_result.value, file_path)

    @staticmethod
    def hardware_software_upload(
            static_server_str: str,
            hardware_id_str: str,
            software_id_str: str
    ) -> Optional[DIPClientError]:
        backend_result = CLI.parsed_backend(None, static_server_str)
        if isinstance(backend_result, Err): return backend_result.value
        software_id_result = ManagedUUID.build(software_id_str)
        if isinstance(software_id_result, Err): return software_id_result.value.of_type("software")
        hardware_id_result = ManagedUUID.build(hardware_id_str)
        if isinstance(hardware_id_result, Err): return hardware_id_result.value.of_type("hardware")
        return backend_result.value.hardware_software_upload(hardware_id_result.value, software_id_result.value)

    @staticmethod
    def print_json_error(json: Any):
        print_json(data={"error": json})

    @staticmethod
    def print_json_success(json: Any):
        print_json(data={"success": json})

    @staticmethod
    def hardware_serial_monitor(
        control_server_str: str,
        hardware_id_str: str,
        monitor_type_str: str,
        monitor_script_path_str: Optional[str]
    ) -> Result[MonitorSerial, DIPClientError]:
        # Build backend
        backend_result = CLI.parsed_backend(control_server_str, None)
        if isinstance(backend_result, Err): return Err(backend_result.value)

        # Hardware id
        hardware_id_result = ManagedUUID.build(hardware_id_str)
        if isinstance(hardware_id_result, Err): return Err(hardware_id_result.value.of_type("hardware"))

        # Build URL
        url_result = backend_result.value.hardware_serial_monitor_url(hardware_id_result.value)
        if isinstance(url_result, Err): return Err(url_result.value)

        # Monitor type
        monitor_serial_result = MonitorType.build(monitor_type_str)
        if isinstance(monitor_serial_result, Err): return Err(monitor_serial_result.value)
        monitor_serial: MonitorType = monitor_serial_result.value

        # Monitor
        decoder = s11n_hybrid.MONITOR_LISTENER_INCOMING_MESSAGE_DECODER
        encoder = s11n_hybrid.MONITOR_LISTENER_OUTGOING_MESSAGE_ENCODER
        websocket = WebSocket(url_result.value, decoder, encoder)
        return monitor_serial.resolve(websocket, monitor_script_path_str)

    @staticmethod
    async def execute_runnable_result(
        runnable_result: Result[DIPRunnable, DIPClientError],
        success_title: str = "Finished task"
    ):
        if isinstance(runnable_result, Err):
            print_error(runnable_result.value.text())
            return sys.exit(1)
        runtime_result = await runnable_result.value.run()
        await asyncio.sleep(0.1) # Hacks to yield to event loop
        if runtime_result is not None:
            print_error(runtime_result.text())
            return sys.exit(1)
        print_success(success_title)
        return sys.exit(0)

    @staticmethod
    def execute_table_result(
        json_output: bool,
        result: Result[List[E], DIPClientError],
        json_encoder: EncoderJSON,
        rich_encoder: RichEncoder
    ):
        # Handle error
        if isinstance(result, Err):
            if json_output: CLI.print_json_error(result.value.text())
            else: print_error(result.value.text())
            return

        # Handle success
        if json_output: CLI.print_json_success(s11n_json.list_encoder_json(json_encoder).json_encode(result.value))
        else: richprint(rich_encoder.toTable(result.value))

    @staticmethod
    def execute_optional_result(
        json_output: bool,
        result: Optional[DIPClientError],
        success_title: str
    ):
        # Handle error
        if result is not None:
            if json_output:
                CLI.print_json_error(result.text())
            else:
                print_error(result.text())
            return

        # Handle success
        if json_output:
            CLI.print_json_success(success_title)
        else:
            print_success(success_title)
