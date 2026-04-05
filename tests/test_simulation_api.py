from fastapi.testclient import TestClient

from src.core.app import create_app


def test_execute_simulation_api() -> None:
    app = create_app()
    client = TestClient(app)

    payload = {
        "run_id": "api-run-xyz",
        "scenarios": [
            {
                "scenario_id": "scenario-123",
                "target_ports": ["NLRTM", "USNYC"],
            }
        ],
    }

    response = client.post("/api/v1/simulation/execute", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["run_id"] == "api-run-xyz"
    assert len(data["simulated_scenarios"]) == 1

    scenario = data["simulated_scenarios"][0]
    assert scenario["scenario_id"] == "scenario-123"
    assert scenario["execution_status"] == "SUCCESS"
    
    # Validation against the newly dynamic metrics engine
    assert scenario["metrics"]["total_lead_time_hours"] == 24.0
    assert scenario["metrics"]["average_queue_time_hours"] == 0.0
    assert scenario["metrics"]["total_cost_usd"] == 30000.0
    
    # 2 Ports + Start + End = 6 total tracked events in simulation sequence
    assert len(scenario["critical_events"]) == 6
    
    events = scenario["critical_events"]
    assert events[0]["event_type"] == "SIMULATION_START"
    assert events[-1]["event_type"] == "SIMULATION_END"
    
    # Check proper DCSA time clock progression
    assert events[-1]["timestamp"] == 60.0
