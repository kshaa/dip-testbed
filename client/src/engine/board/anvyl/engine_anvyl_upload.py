"""Anvyl FPGA client functionality."""
from dataclasses import dataclass
from typing import Tuple, List, Optional
from result import Result
from src.domain.dip_client_error import DIPClientError
from src.domain.existing_file_path import ExistingFilePath
from src.engine.board.anvyl.engine_anvyl_state import EngineAnvylBoardState
from src.engine.board.engine_upload import EngineUpload
from src.util.sh import outcome_sh, src_relative_path

FIRMWARE_UPLOAD_PATH = 'static/digilent_anvyl/upload.sh'


@dataclass
class EngineAnvylUpload(EngineUpload):
    @staticmethod
    def firmware_upload_args(
        firmware_path: str,
        device_name: str,
        scan_chain_index: int
    ) -> List[str]:
        """Create command line arguments to initiate firmware upload"""
        upload_script_path = src_relative_path(FIRMWARE_UPLOAD_PATH)
        return [
            "bash",
            "-c",
            f"{upload_script_path} "
            f"-d \"{device_name}\" "
            f"-s \"{scan_chain_index}\" "
            f"-f \"{firmware_path}\""
        ]

    @staticmethod
    async def shell_upload(
        state: EngineAnvylBoardState,
        file: ExistingFilePath
    ) -> Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]:
        return outcome_sh(EngineAnvylUpload.firmware_upload_args(file.value, state.device_name, state.scan_chain_index))

    @staticmethod
    async def upload(
        state: EngineAnvylBoardState,
        file: ExistingFilePath
    ) -> Optional[DIPClientError]:
        return await EngineUpload.shell_as_generic_upload(EngineAnvylUpload.shell_upload, state, file)

