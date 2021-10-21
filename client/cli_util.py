#!/usr/bin/env python
"""Command line interface definition for client"""

from typing import Optional
from uuid import UUID
import click
from result import Err, Ok
import log
from agent_util import AgentConfig
from backend_util import BackendConfig
import url

LOGGER = log.timed_named_logger("cli")
CONTROL_SERVER_OPTION = click.option(
    "--control-server", '-c', "control_server_str", show_envvar=True,
    type=str, envvar="CLIENT_CONTROL_SERVER", required=True,
    help='WebSocket server URL to the backend server. '
    'E.g. ws://localhost:9000/'
)
STATIC_SERVER_OPTION = click.option(
    "--static-server", '-s', "static_server_str", show_envvar=True,
    type=str, envvar="CLIENT_STATIC_SERVER", required=True,
    help='HTTP server URL to the backend server. '
    'E.g. http://localhost:9000/'
)
HARDWARE_ID_OPTION = click.option(
    "--hardware-id", '-i', "hardware_id_str", show_envvar=True,
    type=str, envvar="AGENT_HARDWARE_ID", required=True,
    help='UUID for the hardware to be managed. '
    'E.g. 5400636e-2d91-11ec-9628-8fb2659e451f'
)


def backend_config(control_server_str: Optional[str], static_server_str: Optional[str]):
    """Construct backend config from CLI params"""
    # Control server validation
    if control_server_str is not None:
        control_server_result = url.parse_url(control_server_str)
        if isinstance(control_server_result, Err):
            return Err(f"Invalid control-server URL: {control_server_result.value}")
        control_server = control_server_result.value
    else:
        control_server = None

    # Static server validation
    if static_server_str is not None:
        static_server_result = url.parse_url(static_server_str)
        if isinstance(static_server_result, Err):
            return Err(f"Invalid static-server URL: {static_server_result.value}")
        static_server = static_server_result.value
    else:
        static_server = None

    # Agent configuration
    return Ok(BackendConfig(control_server, static_server))


def agent_config(hardware_id_str: str, control_server_str: str, static_server_str: str):
    """Construct common agent config from CLI params"""
    # Hardware id validation
    try:
        hardware_id = UUID(hardware_id_str)
    except Exception as e:
        return Err(f"Invalid hardware id: ${e}")

    # Backend config constructor
    be_config_result = backend_config(control_server_str, static_server_str)
    if isinstance(be_config_result, Err):
        return Err(f"Failed to construct backend config: {be_config_result.value}")
    be_config = be_config_result.value

    # Agent configuration
    return Ok(AgentConfig(hardware_id, be_config))
