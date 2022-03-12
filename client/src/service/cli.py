#!/usr/bin/env python
"""Command line interface definition for agent"""
import asyncio
import sys
import webbrowser
from typing import Tuple, Optional, List, Union, TypeVar, Any

import appdirs
from result import Err, Result, Ok
from rich.table import Table
from src.agent.agent import Agent
from src.agent.agent_config import AgentConfig
from src.domain.backend_entity import User, Hardware, Software
from src.domain.config import Config
from src.domain.death import Death
from src.domain.dip_runnable import DIPRunnable
from src.domain.hardware_control_message import InternalStartLifecycle, InternalEndLifecycle
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
from src.engine.board.engine_serial_monitor import EngineSerialMonitor
from src.engine.engine_state import EngineBase
from src.engine.video.engine_video import EngineVideo
from src.engine.video.engine_video_state import EngineVideoState
from src.engine.video.engine_video_stream import EngineVideoStream
from src.monitor.monitor_serial import MonitorSerial
from src.monitor.monitor_type import MonitorType
from src.protocol import s11n_hybrid
from src.protocol.codec_json import JSON, EncoderJSON
from src.protocol.s11n_hybrid import COMMON_INCOMING_MESSAGE_DECODER, COMMON_OUTGOING_MESSAGE_ENCODER, \
    COMMON_OUTGOING_VIDEO_MESSAGE_ENCODER, COMMON_INCOMING_VIDEO_MESSAGE_DECODER
from src.protocol.s11n_json import CONFIG_ENCODER_JSON
from src.protocol.s11n_rich import RichEncoder
from src.service.backend import BackendConfig, BackendService, BackendServiceInterface
from src.service.backend_config import UserPassAuthConfig
from src.service.config_service import ConfigService
from src.service.managed_url import ManagedURL
from src.service.managed_video_stream import VideoStreamConfig, ExistingStreamConfig, VLCStreamConfig
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
    def session_debug(
            config_path_str: Optional[str],
    ) -> Result[ConfigService, DIPClientError]:
        pass

    @staticmethod
    def session_auth(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        username: str,
        password: str,
    ) -> Optional[DIPClientError]:
        pass

    @staticmethod
    def session_auth_remove(
        config_path_str: Optional[str],
    ) -> Optional[DIPClientError]:
        pass

    @staticmethod
    def session_control_server(
        config_path_str: Optional[str],
        control_server_str: Optional[str]
    ) -> Optional[DIPClientError]:
        pass

    @staticmethod
    def session_control_server_remove(
        config_path_str: Optional[str]
    ) -> Optional[DIPClientError]:
        pass

    @staticmethod
    def session_static_server(
        config_path_str: Optional[str],
        static_server_str: Optional[str]
    ) -> Optional[DIPClientError]:
        pass

    @staticmethod
    def session_static_server_remove(
        config_path_str: Optional[str]
    ) -> Optional[DIPClientError]:
        pass

    @staticmethod
    async def agent_nrf52(
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        heartbeat_seconds: int,
        device_path_str: str
    ) -> Result[Agent, DIPClientError]:
        pass

    @staticmethod
    async def agent_anvyl(
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        heartbeat_seconds: int,
        device_name_str: str,
        scan_chain_index: int,
        device_path_str: str
    ) -> Result[Agent, DIPClientError]:
        pass

    @staticmethod
    async def agent_fake(
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        heartbeat_seconds: int
    ) -> Result[Agent, DIPClientError]:
        pass

    @staticmethod
    def user_list(
        config_path_str: Optional[str],
        static_server_str: Optional[str]
    ) -> Result[List[User], DIPClientError]:
        pass

    @staticmethod
    def user_create(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        username: Optional[str],
        password: Optional[str]
    ) -> Result[User, DIPClientError]:
        pass

    @staticmethod
    def hardware_list(
        config_path_str: Optional[str],
        static_server_str: Optional[str]
    ) -> Result[List[Hardware], DIPClientError]:
        pass

    @staticmethod
    def hardware_create(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        username: Optional[str],
        password: Optional[str],
        hardware_name: str
    ) -> Result[Hardware, DIPClientError]:
        pass

    @staticmethod
    def software_list(
        config_path_str: Optional[str],
        static_server_str: str
    ) -> Result[List[Software], DIPClientError]:
        pass

    @staticmethod
    def software_upload(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        username: Optional[str],
        password: Optional[str],
        software_name: str,
        file_path: str,
    ) -> Result[Software, DIPClientError]:
        pass

    @staticmethod
    def software_download(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        software_id_str: str,
        file_path: str
    ) -> Result[ExistingFilePath, DIPClientError]:
        pass

    @staticmethod
    def hardware_software_upload(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        hardware_id_str: str,
        software_id_str: str
    ) -> Optional[DIPClientError]:
        pass

    @staticmethod
    def hardware_serial_monitor(
        config_path_str: Optional[str],
        control_server_str: Optional[str],
        hardware_id_str: str,
        monitor_type_str: str
    ):
        pass

    @staticmethod
    async def quick_run(
        config_path_str: Optional[str],
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        file_path: Optional[str],
        software_name: Optional[str],
        hardware_id_str: str,
        monitor_type_str: str,
        monitor_script_path_str: Optional[str]
    ) -> Result[DIPRunnable, DIPClientError]:
        pass

    @staticmethod
    async def agent_hardware_camera(
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        heartbeat_seconds: int,
        is_stream_existing: bool,
        stream_url_str: Optional[str],
        video_vlc: Optional[str],
        audio_device: Optional[str],
        video_device: Optional[str],
        video_width: Optional[int],
        video_height: Optional[int],
        video_buffer_size: Optional[int],
        audio_sample_rate: Optional[int],
        audio_buffer_size: Optional[int],
        port: Optional[int]
    ) -> Result[Agent, DIPClientError]:
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
    def config_service_from_path(
        config_path_str: Optional[str],
    ) -> Result[ConfigService, DIPClientError]:
        # Fallback config path
        if config_path_str is None:
            base_path = appdirs.user_data_dir("dip_platform")
            config_path_str = f"{base_path}/config.yaml"
        # Find config file or create one
        config_path_result = ExistingFilePath.build(config_path_str)
        if isinstance(config_path_result, Err):
            config_path_result = ExistingFilePath.new(config_path_str)
            if isinstance(config_path_result, Err):
                # Accept inability to create config, assume empty config
                LOGGER.warning(config_path_result.value.of_type('config').text())
                return Ok(ConfigService(Config(), CONFIG_ENCODER_JSON))
        # Read file config
        config_result = ConfigService.from_file(CONFIG_ENCODER_JSON, config_path_result.value)
        if isinstance(config_result, Err):
            return Err(config_result.value)
        return Ok(config_result.value)

    @staticmethod
    def config_service_with_overrides(
        config_path_str: Optional[str],
        control_server_str: Optional[str] = None,
        static_server_str: Optional[str] = None,
        username_str: Optional[str] = None,
        password_str: Optional[str] = None
    ) -> Result[ConfigService, DIPClientError]:
        # Raw config
        config_service_result = CLI.config_service_from_path(config_path_str)
        if isinstance(config_service_result, Err): return Err(config_service_result.value)
        config_service = config_service_result.value

        # Build control URL
        if control_server_str is not None:
            control_server_result = ManagedURL.build(control_server_str)
            if isinstance(control_server_result, Err): return Err(control_server_result.value.of_type("control server"))
            config_service = config_service.with_config(
                config_service.config.with_control_url(control_server_result.value))

        # Build static URL
        if static_server_str is not None:
            static_server_result = ManagedURL.build(static_server_str)
            if isinstance(static_server_result, Err): return Err(static_server_result.value.of_type("static server"))
            config_service = config_service.with_config(
                config_service.config.with_static_url(static_server_result.value))

        # Build auth
        if username_str is None and password_str is None:
            # No auth configured, ignore
            pass
        elif username_str is not None and password_str is not None:
            config_service = config_service.with_config(
                config_service.config.with_auth(UserPassAuthConfig(username_str, password_str)))
        else:
            return Err(GenericClientError("Username and password must both be empty or both defined"))

        # Parsed config
        return Ok(config_service)

    @staticmethod
    def parsed_backend(
        config_path_str: Optional[str],
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str]
    ) -> Result[BackendServiceInterface, DIPClientError]:
        # Build config
        config_service_result = CLI.config_service_with_overrides(
            config_path_str,
            control_server_str,
            static_server_str,
            username_str,
            password_str)
        if isinstance(config_service_result, Err): return Err(config_service_result.value)
        config = config_service_result.value.config

        # Complete non-sense check
        if config.control_url is None and config.static_url is None:
            return Err(GenericClientError("Backend service requires either static or control URL"))

        # Successful build
        return Ok(BackendService(BackendConfig(config.control_url, config.static_url, config.auth)))

    @staticmethod
    def session_debug(
        config_path_str: Optional[str],
    ) -> Result[ConfigService, DIPClientError]:
        return CLI.config_service_from_path(config_path_str)

    @staticmethod
    def session_auth(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
    ) -> Optional[DIPClientError]:
        # Updated config
        config_service_result = CLI.config_service_with_overrides(
            config_path_str,
            None,
            static_server_str,
            username_str,
            password_str)
        if isinstance(config_service_result, Err): return config_service_result.value
        config_service = config_service_result.value
        config = config_service.config

        # Auth check
        auth_error = BackendService(BackendConfig(config.control_url, config.static_url, config.auth)).auth_check()
        if auth_error is not None: return auth_error

        # Write auth to file
        if config_service.changed:
            write_error = config_service.to_file()
            if write_error is not None: return write_error

    @staticmethod
    def session_auth_remove(
        config_path_str: Optional[str],
    ) -> Optional[DIPClientError]:
        config_service_result = CLI.config_service_with_overrides(config_path_str)
        if isinstance(config_service_result, Err): return config_service_result.value
        config_service = config_service_result.value
        new_config_service = config_service.with_config(config_service.config.with_auth(None))
        if new_config_service.changed:
            write_error = new_config_service.to_file()
            if write_error is not None: return write_error

    @staticmethod
    def session_control_server(
        config_path_str: Optional[str],
        control_server_str: str
    ) -> Optional[DIPClientError]:
        if control_server_str is None: return GenericClientError("URL required")
        config_service_result = CLI.config_service_with_overrides(config_path_str, control_server_str)
        if isinstance(config_service_result, Err): return config_service_result.value
        if config_service_result.value.changed:
            write_error = config_service_result.value.to_file()
            if write_error is not None: return write_error

    @staticmethod
    def session_control_server_remove(
        config_path_str: Optional[str]
    ) -> Optional[DIPClientError]:
        config_service_result = CLI.config_service_with_overrides(config_path_str)
        if isinstance(config_service_result, Err): return config_service_result.value
        config_service = config_service_result.value
        new_config_service = config_service.with_config(config_service.config.with_control_url(None))
        if new_config_service.changed:
            write_error = new_config_service.to_file()
            if write_error is not None: return write_error

    @staticmethod
    def session_static_server(
        config_path_str: Optional[str],
        static_server_str: Optional[str]
    ) -> Optional[DIPClientError]:
        if static_server_str is None: return GenericClientError("URL required")
        config_service_result = CLI.config_service_with_overrides(config_path_str, None, static_server_str)
        if isinstance(config_service_result, Err): return config_service_result.value
        if config_service_result.value.changed:
            write_error = config_service_result.value.to_file()
            if write_error is not None: return write_error

    @staticmethod
    def session_static_server_remove(
        config_path_str: Optional[str]
    ) -> Optional[DIPClientError]:
        config_service_result = CLI.config_service_with_overrides(config_path_str)
        if isinstance(config_service_result, Err): return config_service_result.value
        config_service = config_service_result.value
        new_config_service = config_service.with_config(config_service.config.with_static_url(None))
        if new_config_service.changed:
            write_error = new_config_service.to_file()
            if write_error is not None: return write_error

    @staticmethod
    def parsed_agent_input(
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        heartbeat_seconds: int,
        device_path_str: Optional[str],
        video_agent: bool = False
    ) -> Result[
        Tuple[ManagedUUID, PositiveInteger, BackendServiceInterface, ManagedURL, ExistingFilePath],
        DIPClientError
    ]:
        config_service_result = CLI.config_service_with_overrides(
            config_path_str, control_server_str, static_server_str, username_str, password_str)
        if isinstance(config_service_result, Err): return config_service_result.value
        config = config_service_result.value.config

        hardware_id_result = ManagedUUID.build(hardware_id_str)
        if isinstance(hardware_id_result, Err): return Err(hardware_id_result.value.of_type("hardware"))

        if config.control_url is None: return Err(GenericClientError("Control URL is required"))
        if not video_agent and config.static_url is None: return Err(GenericClientError("Static URL is required"))

        heartbeat_seconds_result = PositiveInteger.build(heartbeat_seconds)
        if isinstance(heartbeat_seconds_result, Err): return Err(heartbeat_seconds_result.value.of_type("heartbeat"))

        backend = BackendService(BackendConfig(config.control_url, config.static_url, config.auth))

        hardware_control_url_result = backend.hardware_control_url(hardware_id_result.value)
        if isinstance(hardware_control_url_result, Err): return Err(hardware_control_url_result.value)

        if device_path_str is None:
            device_path_result = Ok(None)
        else:
            device_path_result = ExistingFilePath.build(device_path_str)
            if isinstance(device_path_result, Err): return Err(device_path_result.value.of_type("device"))

        return Ok((
            hardware_id_result.value,
            heartbeat_seconds_result.value,
            backend,
            hardware_control_url_result.value,
            device_path_result.value
        ))

    @staticmethod
    async def agent_nrf52(
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        heartbeat_seconds: int,
        device_path_str: str
    ) -> Result[Agent, DIPClientError]:
        # Common agent input
        common_agent_input_result: Result = CLI.parsed_agent_input(
            config_path_str, hardware_id_str, control_server_str, static_server_str, username_str, password_str,
            heartbeat_seconds, device_path_str)
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
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        heartbeat_seconds: int,
        device_name_str: str,
        scan_chain_index: int,
        device_path_str: str
    ) -> Result[Agent, DIPClientError]:
        # Common agent input
        common_agent_input_result: Result = CLI.parsed_agent_input(
            config_path_str, hardware_id_str, control_server_str, static_server_str, username_str, password_str,
            heartbeat_seconds, device_path_str)
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
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        heartbeat_seconds: int
    ) -> Result[Agent, DIPClientError]:
        # Common agent input
        device_path = ExistingFilePath(src_relative_path("static/test/device"))
        common_agent_input_result: Result = CLI.parsed_agent_input(
            config_path_str, hardware_id_str, control_server_str, static_server_str, username_str, password_str,
            heartbeat_seconds, device_path.value)
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
    def user_list(
        config_path_str: Optional[str],
        static_server_str: Optional[str]
    ) -> Result[List[User], DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, None, None)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.user_list()

    @staticmethod
    def user_create(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        username: Optional[str],
        password: Optional[str]
    ) -> Result[User, DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, username, password)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.user_create(username, password)

    @staticmethod
    def hardware_list(
        config_path_str: Optional[str],
        static_server_str: Optional[str]
    ) -> Result[List[Hardware], DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, None, None)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.hardware_list()

    @staticmethod
    def hardware_create(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        username: Optional[str],
        password: Optional[str],
        hardware_name: str
    ) -> Result[Hardware, DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, username, password)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.hardware_create(hardware_name)

    @staticmethod
    def hardware_stream_open(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        hardware_id_str: str
    ) -> Optional[DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, None, None)
        if isinstance(backend_result, Err): return backend_result.value
        hardware_id_result = ManagedUUID.build(hardware_id_str)
        if isinstance(hardware_id_result, Err): return hardware_id_result.value.of_type("hardware")
        hardware_video_sink_url_result = backend_result.value.hardware_video_sink_url(hardware_id_result.value)
        if isinstance(hardware_video_sink_url_result, Err): return hardware_video_sink_url_result.value
        url_text_result = hardware_video_sink_url_result.value.text()
        if isinstance(url_text_result, Err): return url_text_result.value
        url = url_text_result.value
        LOGGER.info(f"Video stream available at: {url}")
        webbrowser.open(url)

    @staticmethod
    def software_list(
        config_path_str: Optional[str],
        static_server_str: Optional[str]
    ) -> Result[List[Software], DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, None, None)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        return backend_result.value.software_list()

    @staticmethod
    def software_upload(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        username: Optional[str],
        password: Optional[str],
        software_name: Optional[str],
        file_path: str,
    ) -> Result[Software, DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, username, password)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        file_result = ExistingFilePath.build(file_path)
        if isinstance(file_result, Err): return Err(file_result.value.of_type("software"))
        return backend_result.value.software_upload(file_result.value, software_name)

    @staticmethod
    def software_download(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        software_id_str: str,
        file_path: str
    ) -> Result[ExistingFilePath, DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, None, None)
        if isinstance(backend_result, Err): return Err(backend_result.value)
        software_id_result = ManagedUUID.build(software_id_str)
        if isinstance(software_id_result, Err): return Err(software_id_result.value.of_type("software"))
        return backend_result.value.software_download(software_id_result.value, file_path)

    @staticmethod
    def hardware_software_upload(
        config_path_str: Optional[str],
        static_server_str: Optional[str],
        hardware_id_str: str,
        software_id_str: str
    ) -> Optional[DIPClientError]:
        backend_result = CLI.parsed_backend(config_path_str, None, static_server_str, None, None)
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
        config_path_str: Optional[str],
        control_server_str: Optional[str],
        hardware_id_str: str,
        monitor_type_str: str
    ) -> Result[MonitorSerial, DIPClientError]:
        # Build backend
        backend_result = CLI.parsed_backend(config_path_str, control_server_str, None, None, None)
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
        return monitor_serial.resolve(websocket)

    @staticmethod
    async def quick_run(
        config_path_str: Optional[str],
        control_server_str: Optional[str],
        static_server_str: Optional[str],
        username_str: Optional[str],
        password_str: Optional[str],
        file_path: Optional[str],
        software_name: Optional[str],
        hardware_id_str: str,
        monitor_type_str: str,
        monitor_script_path_str: Optional[str]
    ) -> Result[DIPRunnable, DIPClientError]:
        # Upload software to platform
        LOGGER.info("Uploading software to platform")
        upload_result = CLI.software_upload(
            config_path_str, static_server_str, username_str, password_str, software_name, file_path)
        if isinstance(upload_result, Err): return Err(upload_result.value)
        software: Software = upload_result.value
        # Forward software to board
        LOGGER.info("Forwarding software to board")
        forward_error = CLI.hardware_software_upload(
            config_path_str, static_server_str, hardware_id_str, str(software.id.value))
        if forward_error is not None: return Err(forward_error)
        # Create serial monitor connection to board
        LOGGER.info("Configuring serial connection monitor with board")
        monitor_result = CLI.hardware_serial_monitor(
            config_path_str, control_server_str, hardware_id_str, monitor_type_str, monitor_script_path_str)
        if isinstance(monitor_result, Err): return Err(monitor_result.value)
        # Open stream in background
        LOGGER.info("Opening video stream in browser")
        stream_open_error = CLI.hardware_stream_open(config_path_str, static_server_str, hardware_id_str)
        if stream_open_error is not None: return Err(stream_open_error)
        # Return serial monitor
        return Ok(monitor_result.value)

    @staticmethod
    def parsed_video_config(
        is_stream_existing: bool,
        stream_url_str: Optional[str],
        video_vlc: Optional[str],
        audio_device: Optional[str],
        video_device: Optional[str],
        video_width: Optional[int],
        video_height: Optional[int],
        video_buffer_size: Optional[int],
        audio_sample_rate: Optional[int],
        audio_buffer_size: Optional[int],
        port: Optional[int]
    ) -> Result[VideoStreamConfig, DIPClientError]:
        if is_stream_existing:
            if stream_url_str is None:
                return Err(GenericClientError("If existing video stream is used, URL is required"))
            stream_url_result = ManagedURL.build(stream_url_str)
            if isinstance(stream_url_result, Err): return Err(stream_url_result.value.of_type("stream"))
            return Ok(ExistingStreamConfig(stream_url_result.value))
        else:
            video_device_result = ExistingFilePath.build(video_device)
            if isinstance(video_device_result, Err): return Err(video_device_result.value.of_type("video"))
            if video_width is None: return Err(GenericClientError("Video stream width is required"))
            if video_height is None: return Err(GenericClientError("Video stream height is required"))
            return Ok(VLCStreamConfig.build(
                video_vlc,
                audio_device,
                video_device_result.value,
                video_width,
                video_height,
                video_buffer_size,
                audio_sample_rate,
                audio_buffer_size,
                port))

    @staticmethod
    async def agent_hardware_camera(
        config_path_str: Optional[str],
        hardware_id_str: str,
        control_server_str: Optional[str],
        heartbeat_seconds: int,
        is_stream_existing: bool,
        stream_url_str: Optional[str],
        video_vlc: Optional[str],
        audio_device: Optional[str],
        video_device: Optional[str],
        video_width: Optional[int],
        video_height: Optional[int],
        video_buffer_size: Optional[int],
        audio_sample_rate: Optional[int],
        audio_buffer_size: Optional[int],
        port: Optional[int]
    ) -> Result[Agent, DIPClientError]:
        # Common agent input
        common_agent_input_result: Result = CLI.parsed_agent_input(
            config_path_str, hardware_id_str, control_server_str, None, None, None,
            heartbeat_seconds, None, True)
        if isinstance(common_agent_input_result, Err): return common_agent_input_result
        (hardware_id, heartbeat_seconds, backend, _, _) = \
            common_agent_input_result.value

        # Video config
        video_config_result = CLI.parsed_video_config(
            is_stream_existing,
            stream_url_str,
            video_vlc,
            audio_device,
            video_device,
            video_width,
            video_height,
            video_buffer_size,
            audio_sample_rate,
            audio_buffer_size,
            port)
        if isinstance(video_config_result, Err): return Err(video_config_result.value)

        # Build video source connection URL
        video_source_url_result = backend.hardware_video_source_url(hardware_id)
        if isinstance(video_source_url_result, Err): return video_source_url_result
        video_source_url = video_source_url_result.value

        # Engine
        base = await EngineBase.build()
        engine_state = EngineVideoState(base, hardware_id, heartbeat_seconds, video_config_result.value, None, Death())
        engine_lifecycle = EngineLifecycle()
        engine_ping = EnginePing()
        engine_video_stream = EngineVideoStream()
        engine = EngineVideo(engine_state, engine_lifecycle, engine_ping, engine_video_stream)

        # Agent with engine construction
        encoder = COMMON_OUTGOING_VIDEO_MESSAGE_ENCODER
        decoder = COMMON_INCOMING_VIDEO_MESSAGE_DECODER
        websocket = WebSocket(video_source_url, decoder, encoder)

        return Ok(Agent(AgentConfig(engine, websocket)))

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
        result: Result[E, DIPClientError],
        json_encoder: EncoderJSON,
        rich_encoder: Optional[RichEncoder]
    ):
        # Handle error
        if isinstance(result, Err):
            if json_output: CLI.print_json_error(result.value.text())
            else: print_error(result.value.text())
            return

        # Handle success
        if json_output: CLI.print_json_success(json_encoder.json_encode(result.value))
        elif rich_encoder is not None: richprint(rich_encoder.toTable(result.value))
        else: raise Exception("Programmer error: Table encoder for entity not provided")

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
