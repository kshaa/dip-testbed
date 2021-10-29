#!/usr/bin/env python
"""Command line interface definition for agent"""

import asyncio
import os
import sys
import shutil
from dataclasses import asdict
from uuid import UUID
import click
from result import Err
from rich import print as richprint
from rich_util import print_error, print_success, print_json
from agent import AgentConfig
from agent_nrf52 import EngineNRF52Config
from agent_anvyl import EngineAnvylConfig
import agent_entrypoints
import log
import cli_util
from rich_tables import user_table, hardware_table, software_table

LOGGER = log.timed_named_logger("cli")
PASS_AGENT_CONFIG = click.make_pass_decorator(AgentConfig)


@click.group()
def cli_client():
    """DIP Testbed Agent is a command line tool that serves as a remote
     microcontroller management middleman for the DIP Testbed Backend

     Use environment variable LOG_LEVEL with value 'debug' for debugging
     or 'info' when running an agent in regular mode or 'error' when you
     barely care about anything

     Use <command> --help for more information about commands. Note that
     most command options can also be defined as environment variables!
     """


@cli_client.command()
@cli_util.HARDWARE_ID_OPTION
@cli_util.CONTROL_SERVER_OPTION
@cli_util.STATIC_SERVER_OPTION
@cli_util.HEARTBEAT_SECONDS_OPTION
@click.option(
    '--device-path', '-f', "device_path_str",
    type=str, envvar="DIP_NRF52_DEVICE",
    required=True, show_envvar=True,
    help='Serial device file path for NRF52 microcontroller serial port communications. '
         'E.g. /dev/ttyUSB0'
)
@click.option(
    '--baudrate', '-b', "baudrate",
    type=int, envvar="DIP_NRF52_BAUDRATE",
    required=True, show_envvar=True,
    help='Baudrate for NRF52 microcontroller serial port communications. '
         'E.g. baud rate of 115200'
)
def agent_nrf52(
        hardware_id_str: str,
        control_server_str: str,
        static_server_str: str,
        heartbeat_seconds: int,
        device_path_str: str,
        baudrate: int
):
    """[Linux] NRF52 microcontroller agent"""
    # Agent config constructor
    agent_config_result = cli_util.agent_config(
        hardware_id_str,
        control_server_str,
        static_server_str,
        heartbeat_seconds)
    if isinstance(agent_config_result, Err):
        print_error(f"Failed to construct agent config: {agent_config_result.value}")
        sys.exit(1)
    agent_config = agent_config_result.value

    # Validate device
    if not os.path.exists(device_path_str):
        print_error(f"Device path '{device_path_str}' does not exist")
        sys.exit(1)

    # Validate baudrate
    if baudrate <= 0:
        print_error("Baudrate must be a positive number")
        sys.exit(1)

    # Validate dependencies
    if shutil.which("adafruit-nrfutil") is None:
        print_error("'adafruit-nrfutil' must be installed")
        sys.exit(1)
    if shutil.which("bash") is None:
        print_error("'bash' must be installed")
        sys.exit(1)
    if shutil.which("grep") is None:
        print_error("'grep' must be installed")
        sys.exit(1)
    if shutil.which("tee") is None:
        print_error("'tee' must be installed")
        sys.exit(1)

    # Construct engine
    engine_config = EngineNRF52Config(agent_config, device_path_str, baudrate)
    agent_entrypoints.supervise_agent_nrf52(agent_config, engine_config)


@cli_client.command()
@cli_util.HARDWARE_ID_OPTION
@cli_util.CONTROL_SERVER_OPTION
@cli_util.STATIC_SERVER_OPTION
@cli_util.HEARTBEAT_SECONDS_OPTION
@click.option(
    '--device-name', '-n', "device_name_str", show_envvar=True,
    type=str, envvar="DIP_ANVYL_DEVICE_NAME", required=True,
    help='Device user name (e.g. Anvyl), used for upload')
@click.option(
    '--scanchainindex', '-s', "scan_chain_index", show_envvar=True,
    type=int, envvar="DIP_ANVYL_SCAN_CHAIN_IDEX", required=True,
    help='Scan chain index of target JTAG device (e.g. 0), used for upload')
@click.option(
    '--device-path', '-f', "device_path_str",
    type=str, envvar="DIP_ANVYL_DEVICE_PATH",
    required=True, show_envvar=True,
    help='Serial device file path for Anvyl microcontroller serial port communications. '
         'E.g. /dev/ttyUSB0. Used for monitoring.'
)
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
    # Agent config constructor
    agent_config_result = cli_util.agent_config(
        hardware_id_str,
        control_server_str,
        static_server_str,
        heartbeat_seconds)
    if isinstance(agent_config_result, Err):
        print_error(f"Failed to construct agent config: {agent_config_result.value}")
        sys.exit(1)
    agent_config = agent_config_result.value

    # Validate scan chain index
    if scan_chain_index < 0:
        print_error("Scan chain index must be a non-negative number")
        sys.exit(1)

    # Validate device
    if not os.path.exists(device_path_str):
        print_error(f"Device path '{device_path_str}' does not exist")
        sys.exit(1)

    # Validate dependencies
    if shutil.which("djtgcfg") is None:
        print_error("'djtgcfg' must be installed")
        sys.exit(1)
    if shutil.which("bash") is None:
        print_error("'bash' must be installed")
        sys.exit(1)

    # Construct engine
    engine_config = EngineAnvylConfig(agent_config, device_name_str, device_path_str, scan_chain_index)
    agent_entrypoints.supervise_agent_anvyl(agent_config, engine_config)


@cli_client.command()
@cli_util.JSON_OUTPUT_OPTION
@cli_util.STATIC_SERVER_OPTION
def user_list(json_output: bool, static_server_str: str):
    """Fetch list of users"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(None, static_server_str)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # User list fetch
    user_list_result = backend_config.user_list()
    if isinstance(user_list_result, Err):
        print_error(f"Failed to fetch user list: {user_list_result.value}")
        sys.exit(1)
    users = user_list_result.value

    # Print output
    if json_output:
        print_json(list(map(asdict, users)))
    else:
        table = user_table(users)
        richprint(table)


@cli_client.command()
@cli_util.JSON_OUTPUT_OPTION
@cli_util.STATIC_SERVER_OPTION
@cli_util.USERNAME_OPTION
@cli_util.PASSWORD_OPTION
def user_create(json_output: bool, static_server_str: str, username: str, password: str):
    """Create new user"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(None, static_server_str)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # User creation
    user_create_result = backend_config.user_create(username, password)
    if isinstance(user_create_result, Err):
        print_error(f"Failed to create user: {user_create_result.value}")
        sys.exit(1)
    user_created = user_create_result.value

    # Print output
    if json_output:
        print_json(asdict(user_created))
    else:
        table = user_table([user_created])
        richprint(table)


@cli_client.command()
@cli_util.JSON_OUTPUT_OPTION
@cli_util.STATIC_SERVER_OPTION
def hardware_list(json_output: bool, static_server_str: str):
    """Fetch list of hardware"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(None, static_server_str)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # Hardware list fetch
    hardware_list_result = backend_config.hardware_list()
    if isinstance(hardware_list_result, Err):
        print_error(f"Failed to fetch hardware list: {hardware_list_result.value}")
        sys.exit(1)
    hardwares = hardware_list_result.value

    # Print output
    if json_output:
        print_json(list(map(asdict, hardwares)))
    else:
        table = hardware_table(hardwares)
        richprint(table)


@cli_client.command()
@cli_util.JSON_OUTPUT_OPTION
@cli_util.STATIC_SERVER_OPTION
@cli_util.USERNAME_OPTION
@cli_util.PASSWORD_OPTION
@click.option('--name', '-n', "hardware_name", show_envvar=True,
              type=str, envvar="DIP_HARDWARE_NAME", required=True,
              help='Hardware name (e.g. \'adafruit-nrf52-no-1\').')
def hardware_create(
    json_output: bool,
    static_server_str: str,
    username: str,
    password: str,
    hardware_name: str
):
    """Create new hardware"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(None, static_server_str)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # Hardware creation
    hardware_create_result = \
        backend_config.hardware_create(username, password, hardware_name)
    if isinstance(hardware_create_result, Err):
        print_error(f"Failed to create hardware: {hardware_create_result.value}")
        sys.exit(1)
    hardware_created = hardware_create_result.value

    # Print output
    if json_output:
        print_json(asdict(hardware_created))
    else:
        table = hardware_table([hardware_created])
        richprint(table)


@cli_client.command()
@cli_util.JSON_OUTPUT_OPTION
@cli_util.STATIC_SERVER_OPTION
def software_list(json_output: bool, static_server_str: str):
    """Fetch list of software"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(None, static_server_str)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # Software list fetch
    software_list_result = backend_config.software_list()
    if isinstance(software_list_result, Err):
        print_error(f"Failed to fetch software list: {software_list_result.value}")
        sys.exit(1)
    softwares = software_list_result.value

    # Print output
    if json_output:
        print_json(list(map(asdict, softwares)))
    else:
        table = software_table(softwares)
        richprint(table)


@cli_client.command()
@cli_util.JSON_OUTPUT_OPTION
@cli_util.STATIC_SERVER_OPTION
@cli_util.USERNAME_OPTION
@cli_util.PASSWORD_OPTION
@click.option('--name', '-n', "software_name", show_envvar=True,
              type=str, envvar="DIP_SOFTWARE_NAME", required=True,
              help='Software name (e.g. \'adafruit-nrf52-hello-world.bin\' '
                   'or \'my-beautiful-program\' or whatever).')
@click.option('--file', '-f', "file_path", show_envvar=True,
              type=str, envvar="DIP_SOFTWARE_FILE_PATH", required=True,
              help='Software file path (e.g. \'./hello-world.bin\' '
                   'or \'$HOME/code/project/hello-world.bin\' or whatever).')
def software_upload(
    json_output: bool,
    static_server_str: str,
    username: str,
    password: str,
    software_name: str,
    file_path: str,
):
    """Upload new software"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(None, static_server_str)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # File path validation
    if not os.path.exists(file_path):
        print_error(f"File does not exist: {file_path}")
        sys.exit(1)

    # Software creation
    software_create_result = \
        backend_config.software_upload(username, password, software_name, file_path)
    if isinstance(software_create_result, Err):
        print_error(f"Failed to create software: {software_create_result.value}")
        sys.exit(1)
    software_created = software_create_result.value

    # Print output
    if json_output:
        print_json(asdict(software_created))
    else:
        table = software_table([software_created])
        richprint(table)


@cli_client.command()
@cli_util.STATIC_SERVER_OPTION
@cli_util.SOFTWARE_ID_OPTION
@click.option(
    '--file', '-f', "file_path", show_envvar=True,
    type=str, envvar="DIP_SOFTWARE_FILE_PATH", required=True,
    help='Software download file path (e.g. \'./hello-world.bin\' '
         'or \'$HOME/code/project/hello-world.bin\' or whatever).')
def software_download(
    static_server_str: str,
    software_id_str: str,
    file_path: str
):
    """Download existing software"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(None, static_server_str)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # File path validation
    if os.path.exists(file_path):
        print_error(f"File already exists: {file_path}")
        sys.exit(1)

    # Software id validation
    try:
        software_id = UUID(software_id_str)
    except Exception as e:
        print_error(f"Invalid software id: {e}")
        sys.exit(1)

    # Software download
    software_download_result = \
        backend_config.software_download(software_id, file_path)
    if isinstance(software_download_result, Err):
        print_error(f"Failed to download software: {software_download_result.value}")
        sys.exit(1)
    else:
        print_success(f"Downloaded software: {software_download_result.value}")


@cli_client.command()
@cli_util.STATIC_SERVER_OPTION
@cli_util.HARDWARE_ID_OPTION
@cli_util.SOFTWARE_ID_OPTION
def hardware_software_upload(
    static_server_str: str,
    hardware_id_str: str,
    software_id_str: str
):
    """Upload software to hardware"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(None, static_server_str)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # Hardware id validation
    try:
        hardware_id = UUID(hardware_id_str)
    except Exception as e:
        print_error(f"Invalid hardware id: {e}")
        sys.exit(1)

    # Software id validation
    try:
        software_id = UUID(software_id_str)
    except Exception as e:
        print_error(f"Invalid software id: {e}")
        sys.exit(1)

    # Software download
    software_download_result = \
        backend_config.hardware_software_upload(hardware_id, software_id)
    if isinstance(software_download_result, Err):
        print_error(f"Failed to upload software to hardware:")
        print(software_download_result.value)
        sys.exit(1)
    else:
        print_success(f"Uploaded software to hardware!")


@cli_client.command()
@cli_util.CONTROL_SERVER_OPTION
@cli_util.HARDWARE_ID_OPTION
def hardware_serial_monitor(
    control_server_str: str,
    hardware_id_str: str
):
    """Monitor hardware's serial port"""
    # Backend config constructor
    backend_config_result = cli_util.backend_config(control_server_str, None)
    if isinstance(backend_config_result, Err):
        print_error(f"Failed to construct backend config: {backend_config_result.value}")
        sys.exit(1)
    backend_config = backend_config_result.value

    # Hardware id validation
    try:
        hardware_id = UUID(hardware_id_str)
    except Exception as e:
        print_error(f"Invalid hardware id: {e}")
        sys.exit(1)

    # Monitor hardware
    monitor_result = asyncio.run(backend_config.hardware_serial_monitor(hardware_id))
    if isinstance(monitor_result, Err):
        print()
        print_error(f"Failed to monitor hardware: {monitor_result.value}")
        sys.exit(1)
    else:
        print()
        print_success(f"Finished monitoring hardware!")
