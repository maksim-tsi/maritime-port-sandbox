from __future__ import annotations

from datetime import timedelta

import pytest

from src.schemas.admin import ChaosScenarioType, InjectScenarioRequest, Severity
from src.schemas.dcsa import OperationalStatus
from src.services.port_manager import PortManager, UnknownPortError
from src.state.store import SIMULATION_EPOCH_UTC, InMemoryPortStore


def test_get_unknown_port_raises() -> None:
    manager = PortManager(store=InMemoryPortStore())
    with pytest.raises(UnknownPortError):
        manager.get_port_status("ZZZZZ")


def test_storm_surge_closes_port_and_keeps_yard_density() -> None:
    store = InMemoryPortStore()
    manager = PortManager(store=store)

    before = manager.get_port_status("DEHAM")
    assert before.updatedAt == SIMULATION_EPOCH_UTC

    payload = InjectScenarioRequest(
        targetPort="DEHAM",
        scenarioType=ChaosScenarioType.STORM_SURGE,
        severity=Severity.HIGH,
    )
    after = manager.inject_scenario(payload)

    assert after.operationalStatus == OperationalStatus.CLOSED
    assert after.metrics.availableCapacityTEU == 0
    assert after.metrics.yardDensityPercent == before.metrics.yardDensityPercent
    assert after.updatedAt == SIMULATION_EPOCH_UTC + timedelta(seconds=1)


def test_yard_congestion_transitions_normal_to_restricted() -> None:
    store = InMemoryPortStore()
    manager = PortManager(store=store)

    payload = InjectScenarioRequest(
        targetPort="DEHAM",
        scenarioType=ChaosScenarioType.YARD_CONGESTION,
        severity=Severity.MEDIUM,
    )
    after = manager.inject_scenario(payload)

    assert after.metrics.yardDensityPercent > 90.0
    assert after.operationalStatus == OperationalStatus.RESTRICTED
    assert after.metrics.availableCapacityTEU <= 25_000


def test_updated_at_increments_per_successful_mutation() -> None:
    store = InMemoryPortStore()
    manager = PortManager(store=store)

    first = manager.inject_scenario(
        InjectScenarioRequest(
            targetPort="DEHAM",
            scenarioType=ChaosScenarioType.LABOR_STRIKE,
            severity=Severity.LOW,
        )
    )
    second = manager.inject_scenario(
        InjectScenarioRequest(
            targetPort="DEHAM",
            scenarioType=ChaosScenarioType.YARD_CONGESTION,
            severity=Severity.LOW,
        )
    )

    assert first.updatedAt == SIMULATION_EPOCH_UTC + timedelta(seconds=1)
    assert second.updatedAt == SIMULATION_EPOCH_UTC + timedelta(seconds=2)
