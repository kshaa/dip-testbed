#!/usr/bin/env python
"""Icestick micro-controller client functionality."""

from typing import Sequence, TypeVar
from src.engine.board.icestick.engine_icestick_state import EngineIcestickBoardState
from dataclasses import dataclass
from typing import Tuple, Optional
from result import Result
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.engine.board.engine_upload import EngineUpload
from src.util.sh import outcome_sh, src_relative_path

FIRMWARE_UPLOAD_PATH = '../../../static/lattice_semiconductor_icestick/upload.sh'
SERIALIZABLE = TypeVar('SERIALIZABLE')


@dataclass
class EngineIcestickUpload(EngineUpload):
    @staticmethod
    def firmware_upload_args(
        firmware_path: str,
        device_name: str
    ) -> Sequence[str]:
        """Create command line arguments to initiate firmware upload"""
        upload_script_path = src_relative_path(FIRMWARE_UPLOAD_PATH)
        return [
            "bash",
            "-c",
            f"{upload_script_path} "
            f"-d \"{device_name}\" "
            f"-f \"{firmware_path}\""
        ]

    @staticmethod
    async def shell_upload(
        state: EngineIcestickBoardState,
        file: ExistingFilePath
    ) -> Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]:
        return outcome_sh(
            EngineIcestickUpload.firmware_upload_args(file.value, state.device_name))

    @staticmethod
    async def upload(
        state: EngineIcestickBoardState,
        file: ExistingFilePath
    ) -> Optional[DIPClientError]:
        return await EngineUpload.shell_as_generic_upload(EngineIcestickUpload.shell_upload, state, file)

