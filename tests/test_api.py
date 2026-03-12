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


def test_unknown_port_returns_404() -> None:
    app = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    client = TestClient(app)

    resp = client.get("/api/v1/pcs/terminals/ZZZZZ/status")
    assert resp.status_code == 404


def test_openapi_hides_admin_routes_by_default_and_can_expose_them() -> None:
    app_hidden = create_app(port_store=InMemoryPortStore(), expose_admin_docs=False)
    openapi_hidden = TestClient(app_hidden).get("/openapi.json").json()
    assert "/admin/simulation/scenario" not in openapi_hidden["paths"]

    app_exposed = create_app(port_store=InMemoryPortStore(), expose_admin_docs=True)
    openapi_exposed = TestClient(app_exposed).get("/openapi.json").json()
    assert "/admin/simulation/scenario" in openapi_exposed["paths"]
