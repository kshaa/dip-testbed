#!/usr/bin/env python
"""Run an asynchronous agent instance till it fails or gracefully finishes"""

import asyncio
from typing import TypeVar
import sys
from pprint import pformat
from codec import Encoder, Decoder
from engine import Engine
from agent import AgentConfig, agent
from agent_nrf52 import EngineNRF52Config, EngineNRF52
import log

LOGGER = log.timed_named_logger("entrypoint")

PI = TypeVar('PI')
PO = TypeVar('PO')


def supervise_agent(
        config: AgentConfig,
        encoder: Encoder[PO],
        decoder: Decoder[PI],
        engine: Engine[PI, PO]):
    """Run any given, configured async agent"""
    LOGGER.info("Configuring agent: %s", pformat(config, indent=4))
    async_agent = agent(config, encoder, decoder, engine)
    LOGGER.info("Running async agent")
    agent_return_code = asyncio.run(async_agent)
    LOGGER.info("Exiting with status code: %s", agent_return_code)
    sys.exit(agent_return_code)


def supervise_agent_nrf52(agent_config: AgentConfig, engine_config: EngineNRF52Config):
    """Initiate NRF52 microcontroller agent"""
    engine = EngineNRF52(engine_config)
    encoder = NotImplemented  # FIXME: Define an actual encoder for NRF52
    decoder = NotImplemented  # FIXME: Define an actual decoder for NRF52
    supervise_agent(agent_config, encoder, decoder, engine)
