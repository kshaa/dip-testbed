#!/usr/bin/env python
"""NRF52 micro-controller client functionality."""

from typing import Sequence, TypeVar
from src.engine.board.nrf52.engine_nrf52_state import EngineNRF52BoardState
from dataclasses import dataclass
from typing import Tuple, Optional
from result import Result
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.engine.engine_upload import EngineUpload
from src.util.sh import outcome_sh, src_relative_path

FIRMWARE_UPLOAD_PATH = '../../../static/adafruit_nrf52/upload.sh'
SERIALIZABLE = TypeVar('SERIALIZABLE')


@dataclass
class EngineNRF52Upload(EngineUpload):
    @staticmethod
    def firmware_upload_args(
        firmware_path: str,
        device_path: str,
        baud_rate: int
    ) -> Sequence[str]:
        """Create command line arguments to initiate firmware upload"""
        upload_script_path = src_relative_path(FIRMWARE_UPLOAD_PATH)
        return [
            "bash",
            "-c",
            f"{upload_script_path} "
            f"-d \"{device_path}\" "
            f"-b \"{baud_rate}\" "
            f"-f \"{firmware_path}\""
        ]

    @staticmethod
    async def shell_upload(
        state: EngineNRF52BoardState,
        file: ExistingFilePath
    ) -> Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]:
        return outcome_sh(
            EngineNRF52Upload.firmware_upload_args(file.value, state.device_path.value, state.upload_baud_rate.value))

    @staticmethod
    async def upload(
        state: EngineNRF52BoardState,
        file: ExistingFilePath
    ) -> Optional[DIPClientError]:
        return await EngineUpload.shell_as_generic_upload(EngineNRF52Upload.shell_upload, state, file)

