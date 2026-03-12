from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from threading import Lock

from src.schemas.dcsa import OperationalStatus, PortStatusResponse, TerminalMetrics
from src.state.ports import SUPPORTED_PORTS

SIMULATION_EPOCH_UTC = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class PortState:
    operational_status: OperationalStatus
    yard_density_percent: float
    available_reefer_plugs: int
    available_capacity_teu: int
    updated_at: datetime


class InMemoryPortStore:
    def __init__(self, *, epoch_utc: datetime = SIMULATION_EPOCH_UTC) -> None:
        self._lock = Lock()
        self._clock = epoch_utc
        self._ports: dict[str, PortState] = {
            code: PortState(
                operational_status=OperationalStatus.NORMAL,
                yard_density_percent=config.initial_yard_density_percent,
                available_reefer_plugs=config.initial_available_reefer_plugs,
                available_capacity_teu=config.initial_available_capacity_teu,
                updated_at=self._clock,
            )
            for code, config in SUPPORTED_PORTS.items()
        }

    def get(self, port_code: str) -> PortStatusResponse | None:
        normalized = port_code.strip().upper()
        with self._lock:
            state = self._ports.get(normalized)
            if state is None:
                return None
            return self._to_response(normalized, state)

    def mutate(self, port_code: str, fn: Callable[[PortState], PortState]) -> PortStatusResponse:
        normalized = port_code.strip().upper()
        with self._lock:
            state = self._ports[normalized]
            updated = fn(state)

            self._clock = self._clock + timedelta(seconds=1)
            updated = replace(updated, updated_at=self._clock)

            self._ports[normalized] = updated
            return self._to_response(normalized, updated)

    @staticmethod
    def _to_response(port_code: str, state: PortState) -> PortStatusResponse:
        return PortStatusResponse(
            portCode=port_code,
            operationalStatus=state.operational_status,
            metrics=TerminalMetrics(
                yardDensityPercent=state.yard_density_percent,
                availableReeferPlugs=state.available_reefer_plugs,
                availableCapacityTEU=state.available_capacity_teu,
            ),
            updatedAt=state.updated_at,
        )
