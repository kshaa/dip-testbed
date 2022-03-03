from dataclasses import dataclass
from typing import Optional
from src.domain.death import Death
from src.engine.engine_ping import EnginePingState
from src.engine.engine_state import EngineBase, EngineState
from src.domain.managed_uuid import ManagedUUID
from src.domain.positive_integer import PositiveInteger
from src.engine.video.engine_video_stream import EngineVideoStreamState
from src.service.managed_video_stream import VideoStreamConfig, ManagedVideoStream


@dataclass
class EngineVideoState(EngineState, EnginePingState, EngineVideoStreamState):
    base: EngineBase
    hardware_id: ManagedUUID
    heartbeat_seconds: PositiveInteger
    initial_stream_config: VideoStreamConfig
    stream: Optional[ManagedVideoStream]
    stream_death: Death


