#!/usr/bin/env python
"""Execute CLI definition which will trigger various client entrypoints"""

from src.service.click import cli_client

if __name__ == '__main__':
    # This function auto-magically receives arguments/parameters
    # from the click library, therefore we can ignore type errors
    # pylint: disable=E1120
    cli_client()
