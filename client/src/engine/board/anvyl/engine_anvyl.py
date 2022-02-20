"""Anvyl FPGA client functionality."""
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.engine.board.anvyl.engine_anvyl_state import EngineAnvylState
from src.engine.board.anvyl.engine_anvyl_upload import EngineAnvylUpload
from src.engine.engine_common import EngineCommon
from src.engine.engine_events import COMMON_ENGINE_EVENT
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, COMMON_OUTGOING_MESSAGE


@dataclass
class EngineAnvyl(EngineCommon[
    COMMON_INCOMING_MESSAGE,
    COMMON_OUTGOING_MESSAGE,
    EngineAnvylState,
    COMMON_ENGINE_EVENT,
    DIPClientError
]):
    engine_upload: EngineAnvylUpload
