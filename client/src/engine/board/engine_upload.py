"""Upload engine functionality."""
from dataclasses import dataclass
from typing import Callable, Tuple, List, Awaitable, Optional
from result import Result, Err, Ok
from src.domain.dip_client_error import DIPClientError, GenericClientError
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, UploadMessage, \
    InternalSucceededSoftwareDownload, InternalFailedSoftwareDownload, InternalUploadBoardSoftware, UploadResultMessage, \
    InternalSucceededSoftwareUpload, InternalFailedSoftwareUpload
from src.domain.existing_file_path import ExistingFilePath
from src.domain.managed_uuid import ManagedUUID
from src.domain.hardware_control_event import COMMON_ENGINE_EVENT, DownloadingBoardSoftware, BoardSoftwareDownloadSuccess, \
    BoardSoftwareDownloadFailure, UploadingBoardSoftware, BoardUploadSuccess, BoardUploadFailure, BoardState
from src.engine.engine_state import EngineState
from src.service.backend import BackendServiceInterface


@dataclass
class EngineUploadError(DIPClientError):
    reason: str
    exception: Optional[Exception] = None
    error: Optional[DIPClientError] = None

    def text(self):
        clarification = f", reason: {self.error.text()}" if self.error is not None \
            else f", reason: {str(self.exception)}" if self.exception is not None \
            else ""
        return f"Agent execution failure '{self.reason}'{clarification}"

@dataclass
class EngineUploadState(EngineState):
    board_state: BoardState


@dataclass
class EngineUpload:
    """Software upload related effects projected by engine"""
    backend: BackendServiceInterface

    # Must be implemented by board
    @staticmethod
    async def upload(board_state: BoardState, file: ExistingFilePath) -> Optional[DIPClientError]:
        pass

    @staticmethod
    async def shell_as_generic_upload(
        upload_script: Callable[
            [BoardState, ExistingFilePath],
            Awaitable[Result[Tuple[int, bytes, bytes], Tuple[int, bytes, bytes]]]],
        board_state: BoardState,
        file_path: ExistingFilePath
    ) -> Optional[DIPClientError]:
        """Runs a shell script which uploads software to the board"""
        # Upload software to board
        upload_result = await upload_script(board_state, file_path)

        # Parse upload outcome
        outcome = upload_result.value
        status_code = outcome[0]
        stdout = outcome[1].decode("utf-8")
        stderr = outcome[2].decode("utf-8")
        outcome_message = f"#### Status code: {status_code}\n" \
                          f"#### Stdout:\n{stdout}\n" \
                          f"#### Stderr:\n{stderr}"

        # Create upload result event
        if isinstance(upload_result, Err):
            return GenericClientError(outcome_message)
        return None

    @staticmethod
    def handle_message(
        previous_state: EngineUploadState,
        message: COMMON_INCOMING_MESSAGE
    ) -> Result[List[COMMON_ENGINE_EVENT], DIPClientError]:
        if isinstance(message, UploadMessage):
            return Ok([DownloadingBoardSoftware(message.software_id)])
        elif isinstance(message, InternalSucceededSoftwareDownload):
            return Ok([BoardSoftwareDownloadSuccess(message.file_path)])
        elif isinstance(message, InternalFailedSoftwareDownload):
            return Ok([BoardSoftwareDownloadFailure(message.reason)])
        elif isinstance(message, InternalUploadBoardSoftware):
            return Ok([UploadingBoardSoftware(message.file_path, previous_state.board_state)])
        elif isinstance(message, InternalSucceededSoftwareUpload):
            return Ok([BoardUploadSuccess()])
        elif isinstance(message, InternalFailedSoftwareUpload):
            return Ok([BoardUploadFailure(message.reason)])
        return Ok([])

    def effect_download_software(
        self,
        software_id: ManagedUUID
    ) -> Result[InternalSucceededSoftwareDownload, InternalFailedSoftwareDownload]:
        file_result = self.backend.software_download(software_id)
        if isinstance(file_result, Err):
            return Err(InternalFailedSoftwareDownload(EngineUploadError(
                "Engine failed to download software for hardware",
                error=file_result.value)))
        return Ok(InternalSucceededSoftwareDownload(file_result.value))

    async def effect_project(self, previous_state: EngineUploadState, event: COMMON_ENGINE_EVENT):
        if isinstance(event, DownloadingBoardSoftware):
            result = self.effect_download_software(event.software_id)
            await previous_state.base.incoming_message_queue.put(result.value)
        elif isinstance(event, BoardSoftwareDownloadSuccess):
            await previous_state.base.incoming_message_queue.put(InternalUploadBoardSoftware(event.file_path))
        elif isinstance(event, BoardSoftwareDownloadFailure):
            await previous_state.base.outgoing_message_queue.put(UploadResultMessage(event.reason.text()))
        elif isinstance(event, UploadingBoardSoftware):
            upload_error = await self.upload(previous_state.board_state, event.file_path)
            if upload_error is None:
                await previous_state.base.incoming_message_queue.put(InternalSucceededSoftwareUpload())
            else:
                await previous_state.base.incoming_message_queue.put(InternalFailedSoftwareUpload(upload_error))
        elif isinstance(event, BoardUploadSuccess):
            await previous_state.base.outgoing_message_queue.put(UploadResultMessage(None))
        elif isinstance(event, BoardUploadFailure):
            await previous_state.base.outgoing_message_queue.put(UploadResultMessage(event.reason.text()))
