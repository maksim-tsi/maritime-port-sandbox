from src.core.des_loop import SimulationEnvironment, Vessel, execute_vessel_arrival
from src.schemas.admin import SetStateRequest
from src.services.port_manager import PortManager
from src.state.store import InMemoryPortStore


def test_metric_accumulator_initialization() -> None:
    env = SimulationEnvironment()
    assert env.metrics.total_lead_time_hours == 0.0
    assert env.metrics.average_queue_time_hours == 0.0
    assert env.metrics.bottleneck_severity == 0.0


def test_vessel_arrival_successful_unload() -> None:
    """Test when vessel cleanly fits into terminal capacity without queueing."""
    env = SimulationEnvironment()
    vessel = Vessel(vessel_id="V-FEASIBLE", teu_payload=5000)

    # Defaults inside execute_vessel_arrival are 50000 capacity, 50.0 density if no port_manager
    env.schedule(
        0.0,
        "VESSEL_ARRIVAL",
        "Arriving",
        action=lambda e: execute_vessel_arrival(e, vessel, "DEHAM"),
    )
    env.run()

    # 1st: VESSEL_ARRIVAL at 0.0 -> adds UNLOADING_COMPLETE at 12.0
    assert env.now == 12.0
    assert len(env.history) == 2
    assert env.history[-1].event_type == "UNLOADING_COMPLETE"
    assert env.metrics.queue_count == 0
    assert env.metrics.total_cost_usd == 15000.0


def test_vessel_arrival_infeasible_queuing_mechanics() -> None:
    """Test when vessel exceeds capacity and must queue."""
    env = SimulationEnvironment()
    # Since without port manager fallback capacity is 50000,
    # we make payload 50001 to guarantee infeasibility
    vessel = Vessel(vessel_id="V-INFEASIBLE", teu_payload=50001)

    env.schedule(
        0.0,
        "VESSEL_ARRIVAL",
        "Arriving",
        action=lambda e: execute_vessel_arrival(e, vessel, "DEHAM"),
    )
    env.run()

    # Should hit retry limit (11 fail attempts before terminating scenario)
    assert env.metrics.queue_count == 11
    assert env.history[-1].event_type == "INFEASIBLE_DURING_SIMULATION"
    assert env.metrics.total_queue_time_hours == 24.0 * 11
    assert env.metrics.penalty_cost_usd == 5000.0 * 11


def test_vessel_arrival_with_port_manager_integration() -> None:
    """Test integration with port manager for precise DCSA physical constraints."""
    store = InMemoryPortStore()
    pm = PortManager(store=store)

    # Re-initialize all ports. DEHAM bounded to 2000 capacity.
    pm.set_state(SetStateRequest(capacities={"DEHAM": 2000}, closed_ports=[]))

    env = SimulationEnvironment(port_manager=pm)

    # Payload 2500 -> exceeds DEHAM capacity of 2000.
    vessel = Vessel(vessel_id="V-OVERLOAD", teu_payload=2500)

    # We manually set retry to 10 to instantly trip the final fallback
    # on the very first execute retry wrapper
    env.schedule(
        0.0,
        "VESSEL_ARRIVAL",
        "Arriving at DEHAM",
        action=lambda e: execute_vessel_arrival(e, vessel, "DEHAM", retry_count=10),
    )
    env.run()

    # The action hits execute_vessel_arrival -> evaluates OR solver -> hits infeasible.
    # It queues a retry at retry_count=11.
    # The subsequent retry pops, evaluates `if retry_count > 10`
    # and fires INFEASIBLE_DURING_SIMULATION.
    assert env.metrics.queue_count == 1
    assert env.history[-1].event_type == "INFEASIBLE_DURING_SIMULATION"
    assert env.metrics.total_queue_time_hours == 24.0
