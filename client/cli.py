#!/usr/bin/env python
"""Command line interface definition"""

import os
import sys
from uuid import UUID
import click
from result import Err
import agent_util
from agent import AgentConfig
from agent_nrf52 import EngineNRF52Config
import entrypoint
import log

LOGGER = log.timed_named_logger("cli")
PASS_AGENT_CONFIG = click.make_pass_decorator(AgentConfig)
AGENT_CONFIG_ARGS = [
    click.option('--force_rebuild', '-f', is_flag=True, default=False, help='Force rebuild'),
]


@click.group()
@click.option("--hardware-id", '-i', "hardware_id_str",
              type=str, envvar="AGENT_HARDWARE_ID", required=True,
              help='UUID for the hardware to be managed. '
                   'E.g. 5400636e-2d91-11ec-9628-8fb2659e451f')
@click.option("--control-server", '-c', "control_server_str",
              type=str, envvar="AGENT_CONTROL_SERVER", required=True,
              help='WebSocket server URL to the client commanding/controlling backend server. '
                   'E.g. ws://localhost:9000/')
@click.option("--static-server", '-s', "static_server_str",
              type=str, envvar="AGENT_STATIC_SERVER", required=True,
              help='HTTP server URL to the client commanding/controlling backend server. '
                   'E.g. http://localhost:9000/')
@click.pass_context
def cli_agent(ctx, hardware_id_str, control_server_str, static_server_str):
    """DIP Testbed Agent is a command line tool that serves as a remote
     microcontroller management middleman for the DIP Testbed Backend"""
    # Hardware id validation
    try:
        hardware_id = UUID(hardware_id_str)
    except Exception as e:
        print(f"Invalid hardware id: ${e}")
        sys.exit(1)

    # Control server validation
    control_server_result = agent_util.parse_url(control_server_str)
    if isinstance(control_server_result, Err):
        print(f"Invalid control-server URL: {control_server_result.value}")
        sys.exit(1)
    control_server = control_server_result.value

    # Static server validation
    static_server_result = agent_util.parse_url(static_server_str)
    if isinstance(static_server_result, Err):
        print(f"Invalid static-server URL: {static_server_result.value}")
        sys.exit(1)
    static_server = static_server_result.value

    # Agent configuration
    ctx.obj = AgentConfig(hardware_id, control_server, static_server)


@cli_agent.command()
@click.make_pass_decorator(AgentConfig)
@click.option('--device', '-d', "device_str", type=str, envvar="NRF52_BAUDRATE", required=True,
              help='Serial device file path for NRF52 microcontroller serial port communications. '
                   'E.g. /dev/ttyUSB0')
@click.option('--baudrate', '-b', "baudrate", type=int, envvar="NRF52_BAUDRATE", required=True,
              help='Baudrate for NRF52 microcontroller serial port communications. '
                   'E.g. baud rate of 115200')
def cli_agent_nrf52(agent_config: AgentConfig, device_str: str, baudrate: int):
    """DIP Testbed Agent for managing NRF52 microcontroller"""
    # Validate device
    if not os.path.exists(device_str):
        print(f"Device path '{device_str}' does not exist")
        sys.exit(1)

    # Validate baudrate
    if baudrate <= 0:
        print("Baudrate must be a positive number")
        sys.exit(1)

    # Construct engine
    engine_config = EngineNRF52Config(agent_config, device_str, baudrate)
    entrypoint.supervise_agent_nrf52(agent_config, engine_config)
