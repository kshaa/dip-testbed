"""Module for dynamically importing python modules"""

from contextlib import contextmanager
import importlib
import os
from typing import Any
from result import Result, Err, Ok

# Implementation partially sourced from
# https://newbedev.com/python-3-5-how-to-dynamically-import-a-module-given-the-full-file-path-in-the-presence-of-implicit-sibling-imports


@contextmanager
def sys_path_switch(p):
    """Temporarily replace a given path with a system import path"""
    import sys
    old_path = sys.path
    sys.path = sys.path[:]
    sys.path.insert(0, p)
    try:
        yield
    finally:
        sys.path = old_path


def import_absolute_path_module(absolute_path: str) -> Result[Any, Exception]:
    """Implementation sourced from https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly"""

    with sys_path_switch(os.path.dirname(absolute_path)):
        try:
            spec = importlib.util.spec_from_file_location(absolute_path, absolute_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return Ok(module)
        except Exception as e:
            return Err(e)


def import_path_module(path: str) -> Result[Any, Exception]:
    """Implementation Python module from a given file path"""

    if os.path.isabs(path):
        absolute_path = path
    else:
        cwd = os.getcwd()
        absolute_path = os.path.join(cwd, path)

    return import_absolute_path_module(absolute_path)
