from dataclasses import dataclass
from typing import List
from src.domain.minos_chunks import ParsedChunk


@dataclass
class MinOSSuitePacket:
    parsed_chunk: ParsedChunk
    sent_at: int
    outgoing: bool


@dataclass
class MinOSSuite:
    chunks: List[MinOSSuitePacket]
    treshold_time: int
    treshold_chunks: int
    start_time: int
