from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChaosScenarioType(StrEnum):
    STORM_SURGE = "STORM_SURGE"
    LABOR_STRIKE = "LABOR_STRIKE"
    YARD_CONGESTION = "YARD_CONGESTION"


class Severity(StrEnum):
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


class SetStateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    closed_ports: list[str] = Field(default_factory=list)
    capacities: dict[str, int] = Field(default_factory=dict)

    @field_validator("closed_ports", mode="before")
    @classmethod
    def _normalize_closed_ports(cls, value: object) -> object:
        if not isinstance(value, list):
            return value
        normalized: list[str] = []
        for entry in value:
            if isinstance(entry, str):
                normalized.append(entry.strip().upper())
            else:
                normalized.append(entry)
        return normalized

    @field_validator("capacities", mode="before")
    @classmethod
    def _normalize_capacity_port_codes(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        normalized: dict[Any, Any] = {}
        for key, amount in value.items():
            normalized_key = key.strip().upper() if isinstance(key, str) else key
            normalized[normalized_key] = amount
        return normalized

    @field_validator("capacities")
    @classmethod
    def _validate_non_negative_capacity(cls, value: dict[str, int]) -> dict[str, int]:
        for port_code, capacity in value.items():
            if capacity < 0:
                raise ValueError(f"capacity for {port_code} must be >= 0")
        return value


class SetStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    stateUpdated: bool = True
