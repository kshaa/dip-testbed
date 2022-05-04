from src.engine.board.icestick.engine_icestick_state import EngineIcestickState
from src.engine.board.icestick.engine_icestick_upload import EngineIcestickUpload
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.engine.board.engine_common import EngineCommon
from src.domain.hardware_control_event import COMMON_ENGINE_EVENT
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, COMMON_OUTGOING_MESSAGE


@dataclass
class EngineIcestick(EngineCommon[
    COMMON_INCOMING_MESSAGE,
    COMMON_OUTGOING_MESSAGE,
    EngineIcestickState,
    COMMON_ENGINE_EVENT,
    DIPClientError
]):
    engine_upload: EngineIcestickUpload
