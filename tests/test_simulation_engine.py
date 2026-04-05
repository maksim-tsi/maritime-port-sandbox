from src.schemas.simulation import CandidateScenario, SimulationExecutionRequest
from src.services.simulation_engine import SimulationEngine


def test_simulation_engine_initialization() -> None:
    engine = SimulationEngine()
    assert engine is not None


def test_execute_scenarios_success_no_queues() -> None:
    engine = SimulationEngine()
    req = SimulationExecutionRequest(
        run_id="test-run-1",
        scenarios=[CandidateScenario(scenario_id="scenario-abc", target_ports=["USNYC"])],
    )
    result = engine.execute_scenarios(req)

    assert result.run_id == "test-run-1"
    assert len(result.simulated_scenarios) == 1

    scenario_res = result.simulated_scenarios[0]
    assert scenario_res.scenario_id == "scenario-abc"
    assert scenario_res.execution_status == "SUCCESS"
    assert scenario_res.failure_reason is None
    assert scenario_res.metrics is not None

    # Processing 1 port = 12.0 lead time
    assert scenario_res.metrics.total_lead_time_hours == 12.0
    assert scenario_res.metrics.average_queue_time_hours == 0.0
    assert scenario_res.metrics.total_cost_usd == 15000.0

    events = scenario_res.critical_events
    # START, ARRIVAL, UNLOAD, END = 4 events
    assert len(events) == 4
    assert events[0].event_type == "SIMULATION_START"
    assert events[1].event_type == "VESSEL_ARRIVAL"
    assert events[2].event_type == "UNLOADING_COMPLETE"
    assert events[-1].event_type == "SIMULATION_END"


def test_execute_scenarios_multi_port() -> None:
    engine = SimulationEngine()
    req = SimulationExecutionRequest(
        run_id="test-run-2",
        scenarios=[CandidateScenario(scenario_id="multi-1", target_ports=["DEHAM", "NLRTM"])],
    )
    result = engine.execute_scenarios(req)

    scenario_res = result.simulated_scenarios[0]
    assert scenario_res.execution_status == "SUCCESS"
    assert scenario_res.metrics is not None

    # Processing 2 ports = 24.0 lead time
    assert scenario_res.metrics.total_lead_time_hours == 24.0
    assert scenario_res.metrics.total_cost_usd == 30000.0

    # START, ARRIVAL DEHAM, UNLOAD DEHAM, ARRIVAL NLRTM, UNLOAD NLRTM, END = 6 events
    assert len(scenario_res.critical_events) == 6
    assert scenario_res.critical_events[-1].timestamp == 60.0  # 48 + 12
