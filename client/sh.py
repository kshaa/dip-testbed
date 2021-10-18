"""Module for shell-scripting-specific functionality"""

import os

# Root path of this Python project
PYTHON_ROOT_PATH = os.path.dirname(__file__)


def root_relative_path(relative_path: str) -> str:
    """Convert a path relative to the project root into an absolute path"""
    return os.path.join(PYTHON_ROOT_PATH, relative_path)
