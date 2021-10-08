#!/usr/bin/env python
"""Run an asynchronous agent instance till it fails or gracefully finishes"""

import asyncio
import sys
from agent import agent

# Run async agent
agent_return_code = asyncio.run(agent())
sys.exit(agent_return_code)
