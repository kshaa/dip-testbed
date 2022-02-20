"""Module for serial connection configuration"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ManagedSerialConfig:
    """Configurations for how to monitor a serial device"""
    receive_size: int
    baudrate: int
    timeout: float

    @staticmethod
    def empty():
        """Create empty serial config"""
        return ManagedSerialConfig(
            receive_size=4096,
            baudrate=115200,
            timeout=0.01
        )
