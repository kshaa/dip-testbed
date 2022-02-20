#!/usr/bin/env python
"""Command line interface rich library functionality"""

from typing import Any
import json
from rich import print as richprint
from rich.console import Console

RICH_CONSOLE = Console()


def print_error(error: str):
    """Print styled error message"""
    richprint("[bold red]Error:[/bold red]", error)


def print_success(success: str):
    """Print styled success message"""
    richprint("[bold green]Success:[/bold green]", success)


def print_json(obj: Any):
    """Print styled dictionary"""
    RICH_CONSOLE.print_json(json.dumps(obj))
