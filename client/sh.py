"""Module for shell-scripting-specific functionality"""

import os
from typing import Sequence, Tuple
import subprocess
from subprocess import CalledProcessError
from result import Result, Err, Ok
import log

LOGGER = log.timed_named_logger("sh")
# Root path of this Python project
PYTHON_ROOT_PATH = os.path.dirname(__file__)


def root_relative_path(relative_path: str) -> str:
    """Convert a path relative to the project root into an absolute path"""
    return os.path.join(PYTHON_ROOT_PATH, relative_path)


def outcome_sh(
    runner_args: Sequence[str]
) -> Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]:
    """Run a shell command and return error code & stderr or stdout"""
    try:
        LOGGER.debug("Running command: %s", runner_args)
        proc = subprocess.Popen(
            runner_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        LOGGER.debug("Command returncode: %s", proc.returncode)
        LOGGER.debug("Command stdout: %s", stdout)
        LOGGER.debug("Command stderr: %s", stderr)

        if proc.returncode == 0:
            return Ok((proc.returncode, stdout, stderr))
        else:
            return Err((proc.returncode, stdout, stderr))
    except CalledProcessError as e:
        return Err((e.returncode, "", e.output))
    except Exception as e:
        return Err((1, "", str.encode(f"{e}")))
