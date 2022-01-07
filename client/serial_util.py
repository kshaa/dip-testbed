"""Module for shell-scripting-specific functionality"""

from dataclasses import dataclass
from pprint import pformat
from result import Result, Err, Ok
import log
import serial
from serial import Serial

LOGGER = log.timed_named_logger("serial")


@dataclass(frozen=True, eq=False)
class SerialConfig:
    """Configurations for how to monitor a serial device"""
    receive_size: int
    baudrate: int
    timeout: float

    @staticmethod
    def empty():
        """Create empty serial config"""
        return SerialConfig(
            receive_size=4096,
            baudrate=115200,
            timeout=0.01
        )


def monitor_serial(
    device: str,
    config: SerialConfig
) -> Result[Serial, Exception]:
    """Connect to a serial device"""
    try:
        # Define serial interface
        serial = Serial(
            device,
            baudrate=config.baudrate
        )
        serial.timeout = config.timeout

        # Log success
        LOGGER.info(
            "Configured serial device '%s' w/ config %s",
            device,
            pformat(config, indent=4))

        # Return device
        return Ok(serial)
    except Exception as e:
        return Err(e)
