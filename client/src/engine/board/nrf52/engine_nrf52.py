from src.engine.board.nrf52.engine_nrf52_state import EngineNRF52State
from src.engine.board.nrf52.engine_nrf52_upload import EngineNRF52Upload
from dataclasses import dataclass
from src.domain.dip_client_error import DIPClientError
from src.engine.board.engine_common import EngineCommon
from src.domain.hardware_control_event import COMMON_ENGINE_EVENT
from src.domain.hardware_control_message import COMMON_INCOMING_MESSAGE, COMMON_OUTGOING_MESSAGE


@dataclass
class EngineNRF52(EngineCommon[
    COMMON_INCOMING_MESSAGE,
    COMMON_OUTGOING_MESSAGE,
    EngineNRF52State,
    COMMON_ENGINE_EVENT,
    DIPClientError
]):
    engine_upload: EngineNRF52Upload
