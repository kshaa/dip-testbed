#!/usr/bin/env python
"""Command line interface definition for agent"""

import os
import sys
from dataclasses import asdict
import click
from result import Err
from agent import AgentConfig
from agent_nrf52 import EngineNRF52Config
from agent_anvyl import EngineAnvylConfig
import agent_entrypoints
import log
import cli_util
from rich_util import print_error, print_json

LOGGER = log.timed_named_logger("cli")
PASS_AGENT_CONFIG = click.make_pass_decorator(AgentConfig)


@click.group()
def cli_client():
    """DIP Testbed Agent is a command line tool that serves as a remote
     microcontroller management middleman for the DIP Testbed Backend"""


@cli_client.command()
@cli_util.HARDWARE_ID_OPTION
@cli_util.CONTROL_SERVER_OPTION
@cli_util.STATIC_SERVER_OPTION
@click.option(
    '--device', '-d', "device_str",
    type=str, envvar="NRF52_DEVICE",
    required=True, show_envvar=True,
    help='Serial device file path for NRF52 microcontroller serial port communications. '
    'E.g. /dev/ttyUSB0'
)
@click.option(
    '--baudrate', '-b', "baudrate",
    type=int, envvar="NRF52_BAUDRATE",
    required=True, show_envvar=True,
    help='Baudrate for NRF52 microcontroller serial port communications. '
    'E.g. baud rate of 115200'
)
def cli_agent_nrf52_upload(
    hardware_id_str: str,
    control_server_str: str,
    static_server_str: str,
    device_str: str,
    baudrate: int
):
    """Agent for managing an NRF52 microcontroller"""
    # Agent config constructor
    agent_config_result = cli_util.agent_config(
        hardware_id_str, control_server_str, static_server_str)
    if isinstance(agent_config_result, Err):
        print_error(f"Failed to construct agent config: {agent_config_result.value}")
        sys.exit(1)
    agent_config = agent_config_result.value

    # Validate device
    if not os.path.exists(device_str):
        print_error(f"Device path '{device_str}' does not exist")
        sys.exit(1)

    # Validate baudrate
    if baudrate <= 0:
        print_error("Baudrate must be a non-negative number")
        sys.exit(1)

    # Construct engine
    engine_config = EngineNRF52Config(agent_config, device_str, baudrate)
    agent_entrypoints.supervise_agent_nrf52(agent_config, engine_config)


@cli_client.command()
@cli_util.HARDWARE_ID_OPTION
@cli_util.CONTROL_SERVER_OPTION
@cli_util.STATIC_SERVER_OPTION
@click.option('--device', '-d', "device_str", show_envvar=True,
              type=str, envvar="ANVYL_DEVICE", required=True,
              help='Device user name (e.g. Anvyl).')
@click.option('--scanchainindex', '-s', "scan_chain_index", show_envvar=True,
              type=int, envvar="ANVYL_SCAN_CHAIN_IDEX", required=True,
              help='Scan chain index of target JTAG device (e.g. 0)')
def cli_agent_anvyl_upload(
    hardware_id_str: str,
    control_server_str: str,
    static_server_str: str,
    device_str: str,
    scan_chain_index: int
):
    """Agent for managing the an Anvyl FPGA"""
    # Agent config constructor
    agent_config_result = cli_util.agent_config(
        hardware_id_str,
        control_server_str,
        static_server_str)
    if isinstance(agent_config_result, Err):
        print_error(f"Failed to construct agent config: {agent_config_result.value}")
        sys.exit(1)
    agent_config = agent_config_result.value

    # Validate device
    if not os.path.exists(device_str):
        print_error(f"Device path '{device_str}' does not exist")
        sys.exit(1)

    # Validate baudrate
    if scan_chain_index <= 0:
        print_error("Scan chain index must be a non-negative number")
        sys.exit(1)

    # Construct engine
    engine_config = EngineAnvylConfig(agent_config, device_str, scan_chain_index)
    agent_entrypoints.supervise_agent_anvyl(agent_config, engine_config)


@cli_client.command()
@cli_util.STATIC_SERVER_OPTION
def user_list(static_server_str: str):
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
    json = list(map(asdict, user_list_result.value))
    print_json(json)


@cli_client.command()
@cli_util.STATIC_SERVER_OPTION
@click.option('--username', '-u', "username", show_envvar=True,
              type=str, envvar="USER_USERNAME", required=True,
              help='User username (e.g. \'johndoe\').')
@click.option('--password', '-p', "password", show_envvar=True,
              type=str, envvar="USER_PASSWORD", required=True,
              help='User password (e.g. \'12345\').')
def user_create(static_server_str: str, username: str, password: str):
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
    json = asdict(user_create_result.value)
    print_json(json)
