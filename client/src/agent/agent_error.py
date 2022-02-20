#!/usr/bin/env python
"""Supervising client, listening to server commands, passing to client-specific agent"""
from dataclasses import dataclass
from typing import Optional
from src.domain.dip_client_error import DIPClientError


@dataclass
class AgentExecutionError(DIPClientError):
    reason: str
    exception: Optional[Exception] = None
    error: Optional[DIPClientError] = None

    def text(self):
        clarification = f", reason: {self.error.text()}" if self.error is not None \
            else f", reason: {str(self.exception)}" if self.exception is not None \
            else ""
        return f"Agent execution failure '{self.reason}'{clarification}"
