from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class OperationalStatus(str, Enum):
    NORMAL = "NORMAL"
    RESTRICTED = "RESTRICTED"
    CLOSED = "CLOSED"


class TerminalMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    yardDensityPercent: float = Field(
        ...,
        description="Current yard density. 0.0 to 100.0",
        ge=0.0,
        le=100.0,
    )
    availableReeferPlugs: int = Field(
        ...,
        description="Number of available refrigerated container plugs",
        ge=0,
    )
    availableCapacityTEU: int = Field(
        ...,
        description="Available daily processing capacity in TEU",
        ge=0,
    )


class PortStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    portCode: str = Field(..., description="5-character UN/LOCODE")
    operationalStatus: OperationalStatus
    metrics: TerminalMetrics
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

