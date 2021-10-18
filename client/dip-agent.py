#!/usr/bin/env python
"""Execute CLI definition which will trigger various agent entrypoints"""

from cli import cli_agent
import log

LOGGER = log.timed_named_logger("main")

if __name__ == '__main__':
    # This function auto-magically receives arguments/parameters
    # from the click library, therefore we can ignore type errors
    # pylint: disable=E1120
    cli_agent()
