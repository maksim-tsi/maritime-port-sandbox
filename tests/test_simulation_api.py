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
    assert scenario["metrics"]["total_lead_time_hours"] == 120.0
    assert scenario["metrics"]["average_queue_time_hours"] == 2.5
    assert len(scenario["critical_events"]) == 2
