#!/usr/bin/env python
"""Command line interface definition for agent"""
import asyncio

import click
from src.monitor.monitor_type import MonitorType
from src.service.cli import CLI
from src.protocol import s11n_json, s11n_rich

ENV_PREFIX = "DIP"


# Server connection
CONTROL_SERVER_OPTION = click.option(
    "--control-server", '-c', "control_server_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_CONTROL_SERVER", required=True,
    help='WebSocket server URL to the backend server. '
    'E.g. ws://localhost:9000/'
)
STATIC_SERVER_OPTION = click.option(
    "--static-server", '-s', "static_server_str", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_STATIC_SERVER", required=True,
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
    '--name', '-n', "software_name", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_SOFTWARE_NAME", required=True,
    help='Software name (e.g. \'adafruit-nrf52-hello-world.bin\' '
       'or \'my-beautiful-program\' or whatever).')
SOFTWARE_FILE_PATH = click.option(
    '--file', '-f', "file_path", show_envvar=True,
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
    show_envvar=True, envvar=f"{ENV_PREFIX}_MONITOR_TYPE", required=True, default=MonitorType.hexbytes.name,
    help="Sets the type of monitor implementation to be used")
MONITOR_SCRIPT_PATH_OPTION = click.option(
    "--monitor-script-path", "-s", "monitor_script_path_str", type=str, default=None,
    show_envvar=True, envvar=f"{ENV_PREFIX}_MONITOR_SCRIPT_PATH", required=False,
    help="File path to the monitor implementation script e.g. './monitor-script.py'")


# Formatting
JSON_OUTPUT_OPTION = click.option(
    "--json-output", '-j', "json_output", show_envvar=True, default=False,
    type=bool, envvar=f"{ENV_PREFIX}_JSON_OUTPUT", required=False,
    help='Print client output as JSON when appropriate'
)

# Authentication
USERNAME_OPTION = click.option(
    '--username', '-u', "username", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_AUTH_USERNAME", required=True,
    help='User username (e.g. \'johndoe\').'
)
PASSWORD_OPTION = click.option(
    '--password', '-p', "password", show_envvar=True,
    type=str, envvar=f"{ENV_PREFIX}_AUTH_PASSWORD", required=True,
    help='User password (e.g. \'12345\').'
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


@cli_client.command()
@HARDWARE_ID_OPTION
@CONTROL_SERVER_OPTION
@STATIC_SERVER_OPTION
@HEARTBEAT_SECONDS_OPTION
@DEVICE_PATH_OPTION
def agent_nrf52(
        hardware_id_str: str,
        control_server_str: str,
        static_server_str: str,
        heartbeat_seconds: int,
        device_path_str: str
):
    """[Linux] NRF52 microcontroller agent"""
    async def exec():
        return await CLI.execute_runnable_result(
            await CLI.agent_nrf52(
                hardware_id_str,
                control_server_str,
                static_server_str,
                heartbeat_seconds,
                device_path_str), "NRF52 agent finished work")
    asyncio.run(exec())


@cli_client.command()
@HARDWARE_ID_OPTION
@CONTROL_SERVER_OPTION
@STATIC_SERVER_OPTION
@HEARTBEAT_SECONDS_OPTION
@DEVICE_NAME_OPTION
@SCAN_CHAIN_INDEX_OPTION
@DEVICE_PATH_OPTION
def agent_anvyl(
    hardware_id_str: str,
    control_server_str: str,
    static_server_str: str,
    heartbeat_seconds: int,
    device_name_str: str,
    scan_chain_index: int,
    device_path_str: str
):
    """[Linux] Anvyl FPGA agent"""
    async def exec():
        return await CLI.execute_runnable_result(
            await CLI.agent_anvyl(
                hardware_id_str,
                control_server_str,
                static_server_str,
                heartbeat_seconds,
                device_name_str,
                scan_chain_index,
                device_path_str), "NRF52 agent finished work")
    asyncio.run(exec())


@cli_client.command()
@HARDWARE_ID_OPTION
@CONTROL_SERVER_OPTION
@STATIC_SERVER_OPTION
@HEARTBEAT_SECONDS_OPTION
def agent_fake(
        hardware_id_str: str,
        control_server_str: str,
        static_server_str: str,
        heartbeat_seconds: int
):
    """[Linux] Fake board agent"""
    async def exec():
        return await CLI.execute_runnable_result(
            await CLI.agent_fake(
                hardware_id_str,
                control_server_str,
                static_server_str,
                heartbeat_seconds), "Fake agent finished work")
    asyncio.run(exec())


@cli_client.command()
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
def user_list(json_output: bool, static_server_str: str):
    """Fetch list of users"""
    CLI.execute_table_result(
        json_output,
        CLI.user_list(static_server_str),
        s11n_json.USER_ENCODER_JSON,
        s11n_rich.RichUserEncoder()
    )


@cli_client.command()
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
def user_create(json_output: bool, static_server_str: str, username: str, password: str):
    """Create new user"""
    CLI.execute_table_result(
        json_output,
        CLI.user_create(static_server_str, username, password).map(lambda x: [x]),
        s11n_json.USER_ENCODER_JSON,
        s11n_rich.RichUserEncoder()
    )


@cli_client.command()
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
def hardware_list(json_output: bool, static_server_str: str):
    """Fetch list of hardware"""
    CLI.execute_table_result(
        json_output,
        CLI.hardware_list(static_server_str),
        s11n_json.HARDWARE_ENCODER_JSON,
        s11n_rich.RichHardwareEncoder()
    )


@cli_client.command()
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
@HARDWARE_NAME_OPTION
def hardware_create(
    json_output: bool,
    static_server_str: str,
    username: str,
    password: str,
    hardware_name: str
):
    """Create new hardware"""
    CLI.execute_table_result(
        json_output,
        CLI.hardware_create(static_server_str, username, password, hardware_name).map(lambda x: [x]),
        s11n_json.HARDWARE_ENCODER_JSON,
        s11n_rich.RichHardwareEncoder()
    )


@cli_client.command()
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
def software_list(json_output: bool, static_server_str: str):
    """Fetch list of software"""
    CLI.execute_table_result(
        json_output,
        CLI.software_list(static_server_str),
        s11n_json.SOFTWARE_ENCODER_JSON,
        s11n_rich.RichSoftwareEncoder()
    )


@cli_client.command()
@JSON_OUTPUT_OPTION
@STATIC_SERVER_OPTION
@USERNAME_OPTION
@PASSWORD_OPTION
@SOFTWARE_NAME_OPTION
@SOFTWARE_FILE_PATH
def software_upload(
    json_output: bool,
    static_server_str: str,
    username: str,
    password: str,
    software_name: str,
    file_path: str,
):
    """Upload new software"""
    CLI.execute_table_result(
        json_output,
        CLI.software_upload(static_server_str, username, password, software_name, file_path).map(lambda x: [x]),
        s11n_json.SOFTWARE_ENCODER_JSON,
        s11n_rich.RichSoftwareEncoder()
    )


@cli_client.command()
@STATIC_SERVER_OPTION
@SOFTWARE_ID_OPTION
@SOFTWARE_FILE_PATH
def software_download(
    static_server_str: str,
    software_id_str: str,
    file_path: str
):
    """Download existing software"""
    CLI.execute_optional_result(
        False,
        CLI.software_download(static_server_str, software_id_str, file_path),
        f"Downloaded software at '{file_path}'"
    )


@cli_client.command()
@STATIC_SERVER_OPTION
@HARDWARE_ID_OPTION
@SOFTWARE_ID_OPTION
def hardware_software_upload(
    static_server_str: str,
    hardware_id_str: str,
    software_id_str: str
):
    """Upload software to hardware"""
    CLI.execute_optional_result(
        False,
        CLI.hardware_software_upload(static_server_str, hardware_id_str, software_id_str),
        f"Uploaded software '{software_id_str}' to hardware '{hardware_id_str}'"
    )


@cli_client.command()
@CONTROL_SERVER_OPTION
@HARDWARE_ID_OPTION
@MONITOR_TYPE_OPTION
@MONITOR_SCRIPT_PATH_OPTION
def hardware_serial_monitor(
    control_server_str: str,
    hardware_id_str: str,
    monitor_type_str: str,
    monitor_script_path_str: str
):
    """Monitor hardware's serial port"""
    async def exec():
        await CLI.execute_runnable_result(CLI.hardware_serial_monitor(
            control_server_str,
            hardware_id_str,
            monitor_type_str,
            monitor_script_path_str), "Finished monitoring")
    asyncio.run(exec())

