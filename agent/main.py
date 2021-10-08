#!/usr/bin/env python
"""Run an asynchronous agent instance till it fails or gracefully finishes"""

import asyncio
import sys
from agent import agent
import log

LOGGER = log.timed_named_logger("main")

# Run async agent
LOGGER.info("Initializing agent")
agent_return_code = asyncio.run(agent())
LOGGER.info("Exiting with status code: %s", agent_return_code)
sys.exit(agent_return_code)
