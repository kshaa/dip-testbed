#!/usr/bin/env python
"""Command line interface definition for agent"""
import asyncio
import webbrowser
from typing import Optional
import click
from src.monitor.monitor_type import MonitorType
from src.service.cli import CLI
from src.protocol import s11n_json, s11n_rich

ENV_PREFIX = "DIP"

# Config
CONFIG_PATH_OPTION = click.option(
    "--config-path", '-x', "config_path_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_CONFIG_PATH", required=False,
    help='Path to configuration file, should be an absolute path e.g.'
         '/home/user/.local/share/dip_platform/bin/'
)

# Server connection
CONTROL_SERVER_OPTION = click.option(
    "--control-server", '-c', "control_server_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_CONTROL_SERVER", required=False,
    help='WebSocket server URL to the backend server. '
    'E.g. ws://localhost:9000/'
)
STATIC_SERVER_OPTION = click.option(
    "--static-server", '-s', "static_server_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STATIC_SERVER", required=False,
    help='HTTP server URL to the backend server. '
    'E.g. http://localhost:9000/'
)

# Backend management content
HARDWARE_ID_OPTION = click.option(
    "--hardware-id", '-b', "hardware_id_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_HARDWARE_ID", required=True,
    help='UUID for the hardware to be managed. '
    'E.g. 5400636e-2d91-11ec-9628-8fb2659e451f'
)
HARDWARE_NAME_OPTION = click.option(
    '--name', '-n', "hardware_name", show_envvar=True,
    type=str, envvar="DIP_HARDWARE_NAME", required=True,
    help='Hardware name (e.g. \'adafruit-nrf52-no-1\').')
SOFTWARE_ID_OPTION = click.option(
    '--software-id', '-i', "software_id_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_SOFTWARE_ID", required=True,
    help='Software id (e.g. \'16db6c30-3328-11ec-ae41-ff1d66202dcc\')'
)
SOFTWARE_NAME_OPTION = click.option(
    '--software-name', '-n', "software_name", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_SOFTWARE_NAME", required=False,
    help='Software name (e.g. \'adafruit-nrf52-hello-world.bin\' '
       'or \'my-beautiful-program\' or whatever), default: file name.')
SOFTWARE_FILE_PATH_OPTION = click.option(
    '--software-file', '-f', "software_file_path", show_envvar=True,
    type=str, envvar="DIP_SOFTWARE_FILE_PATH", required=True,
    help='Software file path (e.g. \'./hello-world.bin\' '
        'or \'$HOME/code/project/hello-world.bin\' or whatever).')

# Engine options
HEARTBEAT_SECONDS_OPTION = click.option(
    '--heartbeat-seconds', '-r', "heartbeat_seconds", show_envvar=True,
    type=int, envvar=f"{ENV_PREFIX}_HEARTBEAT_SECONDS", required=True, default=25,
    help='Regular interval in which to ping the server'
)
DEVICE_PATH_OPTION = click.option(
    '--device-path', '-f', "device_path_str",
    type=str, envvar=f"{ENV_PREFIX}_DEVICE_PATH",
    required=True, show_envvar=True,
    help='Device file path serial port communications, e.g. /dev/ttyUSB0'
)
DEVICE_NAME_OPTION = click.option(
    '--device-name', '-n', "device_name_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_DEVICE_NAME", required=True,
    help='Device identification name (e.g. Anvyl), used for upload')
SCAN_CHAIN_INDEX_OPTION = click.option(
    '--scanchainindex', '-s', "scan_chain_index", show_envvar=True,
    type=int, envvar=f"{ENV_PREFIX}_SCAN_CHAIN_INDEX", required=True,
    help='Scan chain index of target JTAG device (e.g. 0), used for upload')

# Monitor options
MONITOR_TYPE_OPTION = click.option(
    "--monitor-type", "-t", "monitor_type_str", type=click.Choice([t.name for t in MonitorType]),
    show_envvar=True, envvar=f"{ENV_PREFIX}_MONITOR_TYPE", required=False, default=MonitorType.buttonleds.name,
    help="Sets the type of monitor implementation to be used")

# Formatting
JSON_OUTPUT_OPTION = click.option(
    "--json-output", '-j', "json_output", show_envvar=True, default=False,
    type=bool, envvar=f"{ENV_PREFIX}_JSON_OUTPUT", required=False,
    help='Print client output as JSON when appropriate'
)

# Authentication
USERNAME_OPTION = click.option(
    '--username', '-u', "username_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_AUTH_USERNAME", required=False,
    help='User username (e.g. \'johndoe\').'
)
PASSWORD_OPTION = click.option(
    '--password', '-p', "password_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_AUTH_PASSWORD", required=False,
    help='User password (e.g. \'12345\').'
)

# Video  streaming options
IS_STREAM_EXISTING_OPTION = click.option(
    '--stream-exists', '-e', "is_stream_existing", show_envvar=True,
    type=bool, envvar=f"{ENV_PREFIX}_STREAM_IS_EXISTING", required=True,
    help='Should the video stream be broadcasted from an existing source.'
)
# Video stream (existing)
STREAM_URL_OPTION = click.option(
    '--stream-url', '-l', "stream_url_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_URL", required=False,
    help='URL for an existing video source (if is_stream_existing), e.g. http://localhost:8081/webcam.ogg'
)
# Video stream (non-existing)
STREAM_VLC_OPTION = click.option(
    '--stream-vlc', '-r', "video_vlc", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_VLC", required=False,
    help='VLC command to be used, e.g. "vlc" or "vlc-pi"'
)
STREAM_AUDIO_DEVICE_OPTION = click.option(
    '--stream-audio', '-z', "audio_device", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_AUDIO_DEVICE", required=False,
    help='VLC slave audio device to be used, e.g. "alsa://"'
)
STREAM_DEVICE_PATH_OPTION = click.option(
    '--stream-device', '-d', "video_device", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_DEVICE_PATH", required=False,
    help='File path to V4L2 video source (if not is_stream_existing), e.g. /dev/video0'
)
STREAM_WIDTH_OPTION = click.option(
    '--stream-width', '-w', "video_width", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_WIDTH", required=False,
    help='Size in pixels for video source width (if not is_stream_existing), e.g. 1280'
)
STREAM_HEIGHT_OPTION = click.option(
    '--stream-height', '-h', "video_height", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_HEIGHT", required=False,
    help='Size in pixels for video source height (if not is_stream_existing), e.g. 720'
)
STREAM_VIDEO_BUFFER_OPTION = click.option(
    '--stream-video-buffer', '-v', "video_buffer_size", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_VIDEO_BUFFER", required=False,
    help='Size in bytes for video stream buffer (if not is_stream_existing), default: 50'
)
STREAM_SAMPLE_RATE_OPTION = click.option(
    '--stream-sample-rate', '-s', "audio_sample_rate", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_SAMPLE_RATE", required=False,
    help='Video stream sample rate (if not is_stream_existing), default: 44100'
)
STREAM_AUDIO_BUFFER_OPTION = click.option(
    '--stream-audio-buffer', '-a', "audio_buffer_size", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_AUDIO_BUFFER", required=False,
    help='Size in bytes for audio stream buffer (if not is_stream_existing), default: 50'
)
STREAM_PORT_OPTION = click.option(
    '--stream-url', '-p', "port", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STREAM_URL", required=False,
    help='Port number for VLC video source (if not is_stream_existing), default: 8081'
)

@click.group()
def cli_client():
    """DIP Testbed Agent is a command line tool that serves as a remote
     microcontroller management middleman for the DIP Testbed Backend

     Use environment variable LOG_LEVEL with values CRITICAL, ERROR,
     WARNING, INFO, DEBUG, NOTSET to configure amount of printed logs

     Use <command> --help for more information about commands. Note that
     most command options can also be defined as environment variables!
     """


# Command
CLI_COMMAND = cli_client.command(context_settings=dict(max_content_width=300))


@CLI_COMMAND
@CONFIG_PATH_OPTION
def session_debug(config_path_str: Optional[str]):
    """Print out all session data"""
    CLI.execute_table_result(
        True,
        CLI.session_debug(config_path_str),
        s11n_json.CONFIG_SERVICE_ENCODER_JSON,
        None
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
def session_auth(
    config_path_str: Optional[str],
    static_server_str: Optional[str],
    username_str: Optional[str],
    password_str: Optional[str],
):
    """Add authentication data to session"""
    CLI.execute_optional_result(
        False,
        CLI.session_auth(config_path_str, static_server_str, username_str, password_str),
        f"Authenticated against backend"
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
def session_auth_remove(
    config_path_str: Optional[str],
):
    """Remove authentication data from session"""
    CLI.execute_optional_result(
        False,
        CLI.session_auth_remove(config_path_str),
        f"Deleted backend authentication data"
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@STATIC_SERVER_OPTION
def session_static_server(
    config_path_str: Optional[str],
    static_server_str: Optional[str],
):
    """Add static server to session"""
    CLI.execute_optional_result(
        False,
        CLI.session_static_server(config_path_str, static_server_str),
        f"Set static server URL"
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
def session_static_server_remove(
    config_path_str: Optional[str]
):
    """Remove static server from session"""
    CLI.execute_optional_result(
        False,
        CLI.session_static_server_remove(config_path_str),
        f"Deleted static server URL"
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@CONTROL_SERVER_OPTION
def session_control_server(
    config_path_str: Optional[str],
    control_server_str: Optional[str],
):
    """Add control server to session"""
    CLI.execute_optional_result(
        False,
        CLI.session_control_server(config_path_str, control_server_str),
        f"Set control server URL"
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
def session_control_server_remove(
    config_path_str: Optional[str]
):
    """Remove control server from session"""
    CLI.execute_optional_result(
        False,
        CLI.session_control_server_remove(config_path_str),
        f"Deleted control server URL"
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@HARDWARE_ID_OPTION
@CONTROL_SERVER_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
@HEARTBEAT_SECONDS_OPTION
@DEVICE_PATH_OPTION
def agent_nrf52(
    config_path_str: Optional[str],
    hardware_id_str: str,
    control_server_str: Optional[str],
    static_server_str: Optional[str],
    username_str: Optional[str],
    password_str: Optional[str],
    heartbeat_seconds: int,
    device_path_str: str
):
    """NRF52 MCU agent (Linux specific)"""
    async def exec():
        return await CLI.execute_runnable_result(
            await CLI.agent_nrf52(
                config_path_str,
                hardware_id_str,
                control_server_str,
                static_server_str,
                username_str,
                password_str,
                heartbeat_seconds,
                device_path_str), "NRF52 agent finished work")
    asyncio.run(exec())


@CLI_COMMAND
@CONFIG_PATH_OPTION
@HARDWARE_ID_OPTION
@CONTROL_SERVER_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
@HEARTBEAT_SECONDS_OPTION
@DEVICE_NAME_OPTION
@SCAN_CHAIN_INDEX_OPTION
@DEVICE_PATH_OPTION
def agent_anvyl(
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
):
    """Anvyl FPGA agent (Linux specific)"""
    async def exec():
        return await CLI.execute_runnable_result(
            await CLI.agent_anvyl(
                config_path_str,
                hardware_id_str,
                control_server_str,
                static_server_str,
                username_str,
                password_str,
                heartbeat_seconds,
                device_name_str,
                scan_chain_index,
                device_path_str), "NRF52 agent finished work")
    asyncio.run(exec())


@CLI_COMMAND
@CONFIG_PATH_OPTION
@HARDWARE_ID_OPTION
@CONTROL_SERVER_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
@HEARTBEAT_SECONDS_OPTION
def agent_fake(
    config_path_str: Optional[str],
    hardware_id_str: str,
    control_server_str: Optional[str],
    static_server_str: Optional[str],
    username_str: Optional[str],
    password_str: Optional[str],
    heartbeat_seconds: int
):
    """Fake board agent"""
    async def exec():
        return await CLI.execute_runnable_result(
            await CLI.agent_fake(
                config_path_str,
                hardware_id_str,
                control_server_str,
                static_server_str,
                username_str,
                password_str,
                heartbeat_seconds), "Fake agent finished work")
    asyncio.run(exec())


@CLI_COMMAND
@CONFIG_PATH_OPTION
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
def user_list(
    config_path_str: Optional[str],
    json_output: bool,
    static_server_str: Optional[str]
):
    """Fetch list of users"""
    CLI.execute_table_result(
        json_output,
        CLI.user_list(config_path_str, static_server_str),
        s11n_json.list_encoder_json(s11n_json.USER_ENCODER_JSON),
        s11n_rich.RichUserEncoder()
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
def user_create(
    config_path_str: Optional[str],
    json_output: bool,
    static_server_str: Optional[str],
    username_str: Optional[str],
    password_str: Optional[str]
):
    """Create new user"""
    CLI.execute_table_result(
        json_output,
        CLI.user_create(config_path_str, static_server_str, username_str, password_str).map(lambda x: [x]),
        s11n_json.list_encoder_json(s11n_json.USER_ENCODER_JSON),
        s11n_rich.RichUserEncoder()
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
def hardware_list(
    config_path_str: Optional[str],
    json_output: bool,
    static_server_str: Optional[str]
):
    """Fetch list of hardware"""
    CLI.execute_table_result(
        json_output,
        CLI.hardware_list(config_path_str, static_server_str),
        s11n_json.list_encoder_json(s11n_json.HARDWARE_ENCODER_JSON),
        s11n_rich.RichHardwareEncoder()
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
@HARDWARE_NAME_OPTION
def hardware_create(
    config_path_str: Optional[str],
    json_output: bool,
    static_server_str: Optional[str],
    username_str: Optional[str],
    password_str: Optional[str],
    hardware_name: str
):
    """Create new hardware"""
    CLI.execute_table_result(
        json_output,
        CLI.hardware_create(
            config_path_str, static_server_str, username_str, password_str, hardware_name).map(lambda x: [x]),
        s11n_json.list_encoder_json(s11n_json.HARDWARE_ENCODER_JSON),
        s11n_rich.RichHardwareEncoder()
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
def software_list(
    config_path_str: Optional[str],
    json_output: bool,
    static_server_str: Optional[str]
):
    """Fetch list of software"""
    CLI.execute_table_result(
        json_output,
        CLI.software_list(config_path_str, static_server_str),
        s11n_json.list_encoder_json(s11n_json.SOFTWARE_ENCODER_JSON),
        s11n_rich.RichSoftwareEncoder()
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
@SOFTWARE_NAME_OPTION
@SOFTWARE_FILE_PATH_OPTION
def software_upload(
    config_path_str: Optional[str],
    json_output: bool,
    static_server_str: Optional[str],
    username_str: Optional[str],
    password_str: Optional[str],
    software_name: Optional[str],
    software_file_path: str,
):
    """Upload new software"""
    CLI.execute_table_result(
        json_output,
        CLI.software_upload(
            config_path_str, static_server_str, username_str, password_str, software_name, software_file_path).map(lambda x: [x]),
        s11n_json.list_encoder_json(s11n_json.SOFTWARE_ENCODER_JSON),
        s11n_rich.RichSoftwareEncoder()
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@STATIC_SERVER_OPTION
@SOFTWARE_ID_OPTION
@SOFTWARE_FILE_PATH_OPTION
def software_download(
    config_path_str: Optional[str],
    static_server_str: Optional[str],
    software_id_str: str,
    software_file_path: str
):
    """Download existing software"""
    CLI.execute_optional_result(
        False,
        CLI.software_download(config_path_str, static_server_str, software_id_str, software_file_path),
        f"Downloaded software at '{software_file_path}'"
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@STATIC_SERVER_OPTION
@HARDWARE_ID_OPTION
@SOFTWARE_ID_OPTION
def hardware_software_upload(
    config_path_str: Optional[str],
    static_server_str: Optional[str],
    hardware_id_str: str,
    software_id_str: str
):
    """Upload software to hardware"""
    CLI.execute_optional_result(
        False,
        CLI.hardware_software_upload(config_path_str, static_server_str, hardware_id_str, software_id_str),
        f"Uploaded software '{software_id_str}' to hardware '{hardware_id_str}'"
    )


@CLI_COMMAND
@CONFIG_PATH_OPTION
@CONTROL_SERVER_OPTION
@HARDWARE_ID_OPTION
@MONITOR_TYPE_OPTION
def hardware_serial_monitor(
    config_path_str: Optional[str],
    control_server_str: Optional[str],
    hardware_id_str: str,
    monitor_type_str: str
):
    """Monitor hardware's serial port"""
    async def exec():
        await CLI.execute_runnable_result(CLI.hardware_serial_monitor(
            config_path_str,
            control_server_str,
            hardware_id_str,
            monitor_type_str), "Finished monitoring")
    asyncio.run(exec())


@CLI_COMMAND
@CONFIG_PATH_OPTION
@CONTROL_SERVER_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
@SOFTWARE_FILE_PATH_OPTION
@SOFTWARE_NAME_OPTION
@HARDWARE_ID_OPTION
@MONITOR_TYPE_OPTION
@MONITOR_SCRIPT_PATH_OPTION
def quick_run(
    config_path_str: Optional[str],
    control_server_str: Optional[str],
    static_server_str: Optional[str],
    username_str: Optional[str],
    password_str: Optional[str],
    software_file_path: Optional[str],
    software_name: Optional[str],
    hardware_id_str: str,
    monitor_type_str: str,
    monitor_script_path_str: str
):
    """Upload, forward & monitor board software"""
    async def exec():
        await CLI.execute_runnable_result(
            await CLI.quick_run(
                config_path_str,
                control_server_str,
                static_server_str,
                username_str,
                password_str,
                software_file_path,
                software_name,
                hardware_id_str,
                monitor_type_str,
                monitor_script_path_str
            ), "Finished quick run")
    asyncio.run(exec())

@CLI_COMMAND
@CONFIG_PATH_OPTION
@HARDWARE_ID_OPTION
@CONTROL_SERVER_OPTION
@HEARTBEAT_SECONDS_OPTION
@IS_STREAM_EXISTING_OPTION
@STREAM_URL_OPTION
@STREAM_VLC_OPTION
@STREAM_AUDIO_DEVICE_OPTION
@STREAM_DEVICE_PATH_OPTION
@STREAM_WIDTH_OPTION
@STREAM_HEIGHT_OPTION
@STREAM_VIDEO_BUFFER_OPTION
@STREAM_SAMPLE_RATE_OPTION
@STREAM_AUDIO_BUFFER_OPTION
@STREAM_PORT_OPTION
def agent_hardware_video(
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
):
    """Hardware video stream broadcast"""
    async def exec():
        return await CLI.execute_runnable_result(
            await CLI.agent_hardware_camera(
                config_path_str,
                hardware_id_str,
                control_server_str,
                heartbeat_seconds,
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
                port
            ), "Hardware camera agent finished work")
    asyncio.run(exec())

@CLI_COMMAND
@CONFIG_PATH_OPTION
@HARDWARE_ID_OPTION
@STATIC_SERVER_OPTION
def hardware_stream_open(
    config_path_str: Optional[str],
    hardware_id_str: str,
    static_server_str: Optional[str]
):
    """Open hardware video stream in a browser"""
    CLI.execute_optional_result(
        False,
        CLI.hardware_stream_open(config_path_str, static_server_str, hardware_id_str),
        f"Opening hardware stream for '{hardware_id_str}'"
    )
