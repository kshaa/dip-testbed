#!/usr/bin/env python
"""Rich table definitions"""

from typing import List
from rich.table import Table
from backend_domain import User, Hardware, Software


def user_table(users: List[User]) -> Table:
    """Create a table of users"""
    table = Table("Id", "Username", title="User list")
    for user in users:
        table.add_row(str(user.id), user.username)
    return table


def hardware_table(hardwares: List[Hardware]) -> Table:
    """Create a table of hardware"""
    table = Table("Id", "Name", "Owner id", title="Hardware list")
    for hardware in hardwares:
        table.add_row(str(hardware.id), hardware.name, str(hardware.owner_uuid))
    return table


def software_table(softwares: List[Software]) -> Table:
    """Create a table of software"""
    table = Table("Id", "Name", "Owner id", title="Software list")
    for software in softwares:
        table.add_row(str(software.id), software.name, str(software.owner_uuid))
    return table
