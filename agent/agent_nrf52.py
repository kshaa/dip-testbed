#!/usr/bin/env python

import subprocess
from subprocess import CalledProcessError
from sh import script_relative_path
from typing import Iterable, Tuple
from fp import Either

firmware_upload_relative_path = 'static/adafruit_nrf52/upload.sh'


def firmware_upload_args(firmware_path: str, device_path: str, baud_rate: int) -> Iterable[str]:
    upload_script_path = script_relative_path(firmware_upload_relative_path)
    return [
        "bash",
        "-c",
        f"{upload_script_path} -d {device_path} -b {baud_rate} -f {firmware_path}"
    ]


def firmware_upload(firmware_path: str, device_path: str, baud_rate: int) -> Either[Tuple[int, bytes], bytes]:
    runner_args = firmware_upload_args(firmware_path, device_path, baud_rate)
    try:
        return Either.as_right(subprocess.check_output(runner_args))  # type: ignore
    except CalledProcessError as e:
        return Either.as_left((e.returncode, e.output))
    except Exception as e:
        return Either.as_left((1, str.encode(f"{e}")))
