#!/usr/bin/env python
"""Command line interface definition"""

import click
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
@click.option('--control_server', '-c', envvar="AGENT_CONTROL_SERVER", required=True,
              help='WebSocket server URL to the agent commanding/controlling backend server.')
@click.option('--static_server', '-s', envvar="AGENT_STATIC_SERVER", required=True,
              help='HTTP server URL to the agent commanding/controlling backend server.')
@click.pass_context
def cli_agent(ctx, control_server, static_server):
    """DIP Testbed Agent is a command line tool that serves as a remote
     microcontroller management middleman for the DIP Testbed Backend"""
    ctx.obj = AgentConfig(control_server, static_server)


@cli_agent.command()
@click.make_pass_decorator(AgentConfig)
@click.option('--baudrate', '-b', envvar="NRF52_BAUDRATE", required=True,
              help='Baudrate for NRF52 microcontroller serial port monitoring')
def cli_agent_nrf52(agent_config: AgentConfig, baudrate: int):
    """DIP Testbed Agent for managing NRF52 microcontroller"""
    engine_config = EngineNRF52Config(baudrate)
    entrypoint.supervise_agent_nrf52(agent_config, engine_config)
