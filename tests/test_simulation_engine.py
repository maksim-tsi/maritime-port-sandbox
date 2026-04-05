from src.schemas.simulation import CandidateScenario, SimulationExecutionRequest
from src.services.simulation_engine import SimulationEngine


def test_simulation_engine_initialization() -> None:
    engine = SimulationEngine()
    assert engine is not None


def test_execute_scenarios() -> None:
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
    assert scenario_res.metrics.total_lead_time_hours == 120.0
    assert len(scenario_res.critical_events) == 2
    assert scenario_res.critical_events[0].event_type == "SIMULATION_START"
    assert scenario_res.critical_events[1].event_type == "SIMULATION_END"
