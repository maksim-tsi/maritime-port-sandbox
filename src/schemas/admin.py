from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChaosScenarioType(str, Enum):
    STORM_SURGE = "STORM_SURGE"
    LABOR_STRIKE = "LABOR_STRIKE"
    YARD_CONGESTION = "YARD_CONGESTION"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class InjectScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    targetPort: str = Field(..., description="5-character UN/LOCODE")
    scenarioType: ChaosScenarioType
    severity: Severity = Severity.MEDIUM

    @field_validator("targetPort", mode="before")
    @classmethod
    def _normalize_port(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("scenarioType", mode="before")
    @classmethod
    def _parse_scenario_type(cls, value: object) -> object:
        if isinstance(value, str):
            return ChaosScenarioType(value)
        return value

    @field_validator("severity", mode="before")
    @classmethod
    def _parse_severity(cls, value: object) -> object:
        if isinstance(value, str):
            return Severity(value)
        return value
