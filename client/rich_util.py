#!/usr/bin/env python
"""Command line interface rich library functionality"""

from typing import Any
import json
from rich import print as richprint
from rich.console import Console
console = Console()


def print_error(error: str):
    """Print styled error message"""
    richprint("[bold red]Error:[/bold red]", error)


def print_json(obj: Any):
    """Print styled dictionary"""
    console.print_json(json.dumps(obj))
