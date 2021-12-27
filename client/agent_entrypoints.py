#!/usr/bin/env python
"""Run an asynchronous client instance till it fails or gracefully finishes"""

import asyncio
from typing import TypeVar
import sys
from pprint import pformat
import s11n_json_protocol
from codec import Encoder, Decoder
from engine import Engine
from agent import AgentConfig, agent
from agent_nrf52 import EngineNRF52Config, EngineNRF52
from agent_anvyl import EngineAnvylConfig, EngineAnvyl
import log

LOGGER = log.timed_named_logger("entrypoint")

RAW = TypeVar('RAW')
SERIALIZABLE = TypeVar('SERIALIZABLE')
PI = TypeVar('PI')
PO = TypeVar('PO')


def supervise_agent(
        config: AgentConfig,
        encoder: Encoder[RAW, SERIALIZABLE, PO],
        decoder: Decoder[RAW, SERIALIZABLE, PI],
        engine: Engine[SERIALIZABLE, PI, PO]):
    """Run any given, configured async client"""
    LOGGER.debug("Configuring client: %s", pformat(config, indent=4))
    async_agent = agent(config, encoder, decoder, engine)
    LOGGER.info("Running async client")
    agent_return_code = asyncio.run(async_agent)
    LOGGER.info("Exiting with status code: %s", agent_return_code)
    sys.exit(agent_return_code)


def supervise_agent_nrf52(agent_config: AgentConfig, engine_config: EngineNRF52Config):
    """Initiate NRF52 microcontroller client"""
    engine = EngineNRF52(engine_config)
    encoder = s11n_json_protocol.COMMON_OUTGOING_MESSAGE_ENCODER_JSON
    decoder = s11n_json_protocol.COMMON_INCOMING_MESSAGE_DECODER_JSON
    supervise_agent(agent_config, encoder, decoder, engine)


def supervise_agent_anvyl(agent_config: AgentConfig, engine_config: EngineAnvylConfig):
    """Initiate Anvyl FPGA client"""
    engine = EngineAnvyl(engine_config)
    encoder = s11n_json_protocol.COMMON_OUTGOING_MESSAGE_ENCODER_JSON
    decoder = s11n_json_protocol.COMMON_INCOMING_MESSAGE_DECODER_JSON
    supervise_agent(agent_config, encoder, decoder, engine)
