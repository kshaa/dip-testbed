#!/usr/bin/env python
"""Hardware management agent configuration"""
from dataclasses import dataclass
from uuid import UUID
from result import Result, Err

from src.domain.managed_uuid import ManagedUUID
from src.service.backend import BackendConfig


@dataclass(frozen=True)
class EngineConfig:
    """Generic agent configuration options"""
    hardware_id: ManagedUUID
    backend: BackendConfig
    heartbeat_seconds: int

    @staticmethod
    def build(
        hardware_id_str: str,
        backend_config: BackendConfig,
        heartbeat_seconds_int: int
    ) -> Result['EngineConfig', str]:
        # Hardware id validation
        hardware_id_result = ManagedUUID.build(hardware_id_str)
        if isinstance(hardware_id_result, Err):
            return Err(f"Invalid hardware id: ${hardware_id_result.value}")

        # Heartbeat validation
        if heartbeat_seconds_int <= 0:
            return Err("Heartbeat seconds must be positive number")

        return EngineConfig(hardware_id_result.value, backend_config, heartbeat_seconds_int)
