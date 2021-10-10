#!/usr/bin/env python
"""Command line interface definition"""

import sys
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
@click.option("--control-server", '-c', "control_server_str",
              type=str, envvar="AGENT_CONTROL_SERVER", required=True,
              help='WebSocket server URL to the agent commanding/controlling backend server.')
@click.option("--static-server", '-s', "static_server_str",
              type=str, envvar="AGENT_STATIC_SERVER", required=True,
              help='HTTP server URL to the agent commanding/controlling backend server.')
@click.pass_context
def cli_agent(ctx, control_server_str, static_server_str):
    """DIP Testbed Agent is a command line tool that serves as a remote
     microcontroller management middleman for the DIP Testbed Backend"""
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
    ctx.obj = AgentConfig(control_server, static_server)


@cli_agent.command()
@click.make_pass_decorator(AgentConfig)
@click.option('--baudrate', '-b', "baudrate", type=int, envvar="NRF52_BAUDRATE", required=True,
              help='Baudrate for NRF52 microcontroller serial port monitoring')
def cli_agent_nrf52(agent_config: AgentConfig, baudrate: int):
    """DIP Testbed Agent for managing NRF52 microcontroller"""
    engine_config = EngineNRF52Config(baudrate)
    entrypoint.supervise_agent_nrf52(agent_config, engine_config)
