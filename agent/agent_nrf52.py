#!/usr/bin/env python
"""NRF52 micro-controller agent functionality."""

import subprocess
from subprocess import CalledProcessError
from typing import Iterable, Tuple
from sh import root_relative_path
from fp import Either

FIRMWARE_UPLOAD_PATH = 'static/adafruit_nrf52/upload.sh'


def firmware_upload_args(firmware_path: str, device_path: str, baud_rate: int) -> Iterable[str]:
    """Create command line arguments to initiate firmware upload"""
    upload_script_path = root_relative_path(FIRMWARE_UPLOAD_PATH)
    return [
        "bash",
        "-c",
        f"{upload_script_path} -d {device_path} -b {baud_rate} -f {firmware_path}"
    ]


def firmware_upload(
        firmware_path: str,
        device_path: str,
        baud_rate: int
) -> Either[Tuple[int, bytes], bytes]:
    """Run firmware upload command and return error code & stderr or stdout"""
    runner_args = firmware_upload_args(firmware_path, device_path, baud_rate)
    try:
        return Either.as_right(subprocess.check_output(runner_args))  # type: ignore
    except CalledProcessError as e:
        return Either.as_left((e.returncode, e.output))
    except Exception as e:
        return Either.as_left((1, str.encode(f"{e}")))
