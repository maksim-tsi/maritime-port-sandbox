from __future__ import annotations

import math
from dataclasses import replace
from typing import Final

from src.schemas.admin import (
    ChaosScenarioType,
    InjectScenarioRequest,
    SetStateRequest,
    SetStateResponse,
    Severity,
)
from src.schemas.dcsa import OperationalStatus, PortStatusResponse
from src.state.ports import SUPPORTED_PORTS, get_port_config
from src.state.store import SIMULATION_EPOCH_UTC, InMemoryPortStore, PortState


class UnknownPortError(LookupError):
    pass


class PortManager:
    _YARD_DENSITY_BY_SEVERITY: Final[dict[Severity, float]] = {
        Severity.LOW: 91.0,
        Severity.MEDIUM: 93.0,
        Severity.HIGH: 96.0,
    }
    _CAPACITY_FACTOR_BY_SEVERITY: Final[dict[Severity, float]] = {
        Severity.LOW: 0.7,
        Severity.MEDIUM: 0.5,
        Severity.HIGH: 0.3,
    }

    def __init__(self, *, store: InMemoryPortStore) -> None:
        self._store = store

    def get_port_status(self, port_code: str) -> PortStatusResponse:
        normalized = port_code.strip().upper()
        response = self._store.get(normalized)
        if response is None:
            raise UnknownPortError(normalized)
        return response

    def inject_scenario(self, payload: InjectScenarioRequest) -> PortStatusResponse:
        port_code = payload.targetPort

        def apply(state: PortState) -> PortState:
            port_config = get_port_config(port_code)

            updated = state
            match payload.scenarioType:
                case ChaosScenarioType.STORM_SURGE:
                    updated = replace(
                        updated,
                        operational_status=OperationalStatus.CLOSED,
                        available_capacity_teu=0,
                    )
                case ChaosScenarioType.LABOR_STRIKE:
                    updated = replace(
                        updated,
                        operational_status=OperationalStatus.RESTRICTED,
                        yard_density_percent=80.0,
                        available_capacity_teu=math.floor(
                            port_config.max_capacity_teu_per_day * 0.5
                        ),
                    )
                case ChaosScenarioType.YARD_CONGESTION:
                    yard_density = self._YARD_DENSITY_BY_SEVERITY[payload.severity]
                    factor = self._CAPACITY_FACTOR_BY_SEVERITY[payload.severity]
                    updated = replace(
                        updated,
                        yard_density_percent=yard_density,
                        available_capacity_teu=math.floor(
                            port_config.max_capacity_teu_per_day * factor
                        ),
                    )
                case _:
                    return updated

            # Spillover cap
            updated = replace(
                updated,
                available_capacity_teu=min(
                    updated.available_capacity_teu, port_config.max_capacity_teu_per_day
                ),
            )

            # Closure rule
            if updated.operational_status == OperationalStatus.CLOSED:
                updated = replace(updated, available_capacity_teu=0)

            # Density rule
            if (
                updated.yard_density_percent > 85.0
                and updated.operational_status == OperationalStatus.NORMAL
            ):
                updated = replace(updated, operational_status=OperationalStatus.RESTRICTED)

            return updated

        try:
            return self._store.mutate(port_code, apply)
        except KeyError as exc:
            raise UnknownPortError(port_code) from exc

    def set_state(self, payload: SetStateRequest) -> SetStateResponse:
        referenced_ports = set(payload.closed_ports) | set(payload.capacities.keys())
        unknown_ports = sorted(referenced_ports - set(SUPPORTED_PORTS.keys()))
        if unknown_ports:
            raise UnknownPortError(unknown_ports[0])

        full_state: dict[str, PortState] = {
            port_code: PortState(
                operational_status=OperationalStatus.NORMAL,
                yard_density_percent=config.initial_yard_density_percent,
                available_reefer_plugs=config.initial_available_reefer_plugs,
                available_capacity_teu=config.initial_available_capacity_teu,
                updated_at=SIMULATION_EPOCH_UTC,
            )
            for port_code, config in SUPPORTED_PORTS.items()
        }

        for port_code, requested_capacity in payload.capacities.items():
            port_config = get_port_config(port_code)
            bounded_capacity = min(requested_capacity, port_config.max_capacity_teu_per_day)
            full_state[port_code] = replace(
                full_state[port_code],
                operational_status=OperationalStatus.NORMAL,
                available_capacity_teu=bounded_capacity,
            )

        for port_code in payload.closed_ports:
            full_state[port_code] = replace(
                full_state[port_code],
                operational_status=OperationalStatus.CLOSED,
                available_capacity_teu=0,
            )

        self._store.overwrite_all(full_state)
        return SetStateResponse(stateUpdated=True)
