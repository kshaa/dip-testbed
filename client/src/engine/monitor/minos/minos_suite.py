from dataclasses import dataclass
from typing import List
from src.domain.minos_chunks import ParsedChunk


@dataclass
class MinOSSuitePacket:
    parsed_chunk: ParsedChunk
    sent_at: float
    sent_timestamp: str
    outgoing: bool


@dataclass
class MinOSSuite:
    chunks: List[MinOSSuitePacket]
    treshold_time: float
    treshold_chunks: int
    start_time: float
    start_timestamp: str
