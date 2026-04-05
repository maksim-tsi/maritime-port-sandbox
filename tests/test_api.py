from __future__ import annotations

from fastapi.testclient import TestClient

from src.core.app import create_app
from src.schemas.dcsa import PortStatusResponse
from src.state.store import InMemoryPortStore


def test_get_port_status_response_is_dcsa_valid() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    resp = client.get("/api/v1/pcs/terminals/DEHAM/status")
    assert resp.status_code == 200
    PortStatusResponse.model_validate(resp.json(), strict=False)


def test_sea_ports_start_normal() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    for port_code in ["CNSHA", "SGSIN", "MYPKG"]:
        resp = client.get(f"/api/v1/pcs/terminals/{port_code}/status")
        assert resp.status_code == 200
        assert resp.json()["operationalStatus"] == "NORMAL"


def test_admin_scenario_mutates_state() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    before = client.get("/api/v1/pcs/terminals/DEHAM/status").json()
    resp = client.post(
        "/admin/simulation/scenario",
        json={"targetPort": "DEHAM", "scenarioType": "STORM_SURGE", "severity": "HIGH"},
    )
    assert resp.status_code == 200

    after = resp.json()
    assert after["operationalStatus"] == "CLOSED"
    assert after["metrics"]["availableCapacityTEU"] == 0
    assert after["metrics"]["yardDensityPercent"] == before["metrics"]["yardDensityPercent"]


def test_admin_set_state_updates_and_confirms() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    resp = client.post(
        "/api/v1/admin/set-state",
        json={"closed_ports": ["DEHAM"], "capacities": {"NLRTM": 5000, "BEANR": 2000}},
    )
    assert resp.status_code == 200
    assert resp.json() == {"stateUpdated": True}

    deham = client.get("/api/v1/pcs/terminals/DEHAM/status").json()
    assert deham["operationalStatus"] == "CLOSED"
    assert deham["metrics"]["availableCapacityTEU"] == 0

    nlrtm = client.get("/api/v1/pcs/terminals/NLRTM/status").json()
    assert nlrtm["operationalStatus"] == "NORMAL"
    assert nlrtm["metrics"]["availableCapacityTEU"] == 5000

    beanr = client.get("/api/v1/pcs/terminals/BEANR/status").json()
    assert beanr["operationalStatus"] == "NORMAL"
    assert beanr["metrics"]["availableCapacityTEU"] == 2000


def test_admin_set_state_full_overwrite_resets_unlisted_ports() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    inject_resp = client.post(
        "/admin/simulation/scenario",
        json={"targetPort": "CNSHA", "scenarioType": "STORM_SURGE", "severity": "HIGH"},
    )
    assert inject_resp.status_code == 200
    assert inject_resp.json()["operationalStatus"] == "CLOSED"

    set_resp = client.post(
        "/api/v1/admin/set-state",
        json={"closed_ports": ["DEHAM"], "capacities": {"NLRTM": 5000}},
    )
    assert set_resp.status_code == 200

    cnsha = client.get("/api/v1/pcs/terminals/CNSHA/status").json()
    assert cnsha["operationalStatus"] == "NORMAL"
    assert cnsha["metrics"]["availableCapacityTEU"] == 130000

    sgsin = client.get("/api/v1/pcs/terminals/SGSIN/status").json()
    assert sgsin["operationalStatus"] == "NORMAL"
    assert sgsin["metrics"]["availableCapacityTEU"] == 100000


def test_admin_set_state_closed_ports_override_capacity_conflicts() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    resp = client.post(
        "/api/v1/admin/set-state",
        json={"closed_ports": ["BEANR"], "capacities": {"BEANR": 2000}},
    )
    assert resp.status_code == 200

    beanr = client.get("/api/v1/pcs/terminals/BEANR/status").json()
    assert beanr["operationalStatus"] == "CLOSED"
    assert beanr["metrics"]["availableCapacityTEU"] == 0


def test_admin_set_state_unknown_port_is_atomic_404() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    before_deham = client.post(
        "/admin/simulation/scenario",
        json={"targetPort": "DEHAM", "scenarioType": "STORM_SURGE", "severity": "HIGH"},
    )
    assert before_deham.status_code == 200
    assert before_deham.json()["operationalStatus"] == "CLOSED"

    resp = client.post(
        "/api/v1/admin/set-state",
        json={"closed_ports": ["DEHAM"], "capacities": {"NLRTM": 5000, "ZZZZZ": 8000}},
    )
    assert resp.status_code == 404

    deham_after = client.get("/api/v1/pcs/terminals/DEHAM/status").json()
    assert deham_after["operationalStatus"] == "CLOSED"
    assert deham_after["metrics"]["availableCapacityTEU"] == 0

    nlrtm_after = client.get("/api/v1/pcs/terminals/NLRTM/status").json()
    assert nlrtm_after["operationalStatus"] == "NORMAL"
    assert nlrtm_after["metrics"]["availableCapacityTEU"] == 40000


def test_unknown_port_returns_404() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    resp = client.get("/api/v1/pcs/terminals/ZZZZZ/status")
    assert resp.status_code == 404


def test_openapi_hides_admin_routes_by_default_and_can_expose_them() -> None:
    app_hidden = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    openapi_hidden = TestClient(app_hidden).get("/openapi.json").json()
    assert "/admin/simulation/scenario" not in openapi_hidden["paths"]
    assert "/api/v1/admin/set-state" not in openapi_hidden["paths"]

    app_exposed = create_app(port_store=InMemoryPortStore(), expose_admin_docs=True)
    openapi_exposed = TestClient(app_exposed).get("/openapi.json").json()
    assert "/admin/simulation/scenario" in openapi_exposed["paths"]
    assert "/api/v1/admin/set-state" in openapi_exposed["paths"]
