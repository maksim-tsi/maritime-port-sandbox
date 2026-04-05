# Maritime Port Sandbox ⚓️

A deterministic **Discrete Event Simulator (DES)** and Operational Research evaluation environment for maritime logistics. Built on strict **Pydantic API boundaries** compliant with the Digital Container Shipping Association (DCSA) schemas.

This repository serves as the "Ground Truth" environment for testing AI agents and Operations Research (OR) solvers in supply chain disruption scenarios, evolving from a static mock API to a dynamic physics engine.

## 🏗️ Hybrid Architecture

* **Time Stepping:** A high-performance `heapq`-based DES loop deterministically evaluates events over chronological time.
* **Capacity Constraints:** The `Pyomo` Operations Research solver validates capacity using constrained optimizations to generate mathematically sound allocation decisions.
* **Strict Contracts:** Pydantic strictly governs all DCSA ingress and egress, ensuring perfectly reproducible scenarios.

## 🎯 Purpose
When testing autonomous supply chain agents, continuous scraping of live news or commercial APIs is computationally expensive, prone to rate limits, and non-reproducible. This Sandbox solves this by providing:
1. **DCSA-compliant Artifacts:** Agents consume standard JSON objects instead of unstructured HTML.
2. **Absolute Reproducibility:** Engine natively simulates congestion, queue wait times, and bottleneck penalties, rather than returning static numbers.
3. **Zero Cost:** No paid subscriptions to AIS aggregators or commercial PCS platforms required.

## 🚀 Features (End-to-End Environment)
* **Discrete Event Simulation Engine:** Priority queues and chronological time jumping out to 300+ hours natively.
* **Pyomo Allocator:** Mathematical capacity checks per vessel integration.
* **Chaos Injection (Admin API):** A hidden endpoint to artificially degrade port capacities to trigger rerouting scenarios for external OR solvers.

## 🛠️ Quick Start

### Requirements
* Python 3.11+
* Docker & Docker Compose (optional but recommended)

### Running with Docker Compose
```bash
docker compose up -d
```

This starts the `sandbox` service on port `8001` and enables in-container hot reload for development.

Check status:

```bash
docker compose ps
```

Stop the service:

```bash
docker compose down
```

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Start the server (recommended)
./scripts/run_dev.sh

# Manual equivalent
EXPOSE_ADMIN_DOCS=1 uvicorn main:app --reload --host 0.0.0.0 --port 8001

```

### Fallback Run Mode (Without Docker)
If Docker is not available, run the sandbox in background with `nohup`:

```bash
nohup env EXPOSE_ADMIN_DOCS=1 uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/maritime-sandbox.log 2>&1 &
```

Check process/socket and logs:

```bash
ss -ltnp | grep 8001
tail -n 100 /tmp/maritime-sandbox.log
```

Stop the background process:

```bash
pkill -f "uvicorn main:app --host 0.0.0.0 --port 8001"
```

### Verify API Availability
In multi-machine development, do not use `localhost` for API checks.
Use `DEV_NODE_IP` from `.env` (the sandbox host), expected to point to `skz-data-lv` in this project setup.

```bash
set -a && source .env && set +a
curl -i --max-time 10 "http://${DEV_NODE_IP}:8001/docs"
curl -i --max-time 10 "http://${DEV_NODE_IP}:8001/openapi.json"
```

Success criteria:
* `/docs`: `HTTP 200` (or `307` redirect to `/docs/`, followed by `200`)
* `/openapi.json`: `HTTP 200`

### Developer Tooling
```bash
pip install -r requirements-dev.txt
ruff check .
mypy .
pytest
```

### Admin Docs Visibility (Swagger/OpenAPI)
Admin endpoints are always callable, but hidden from Swagger/OpenAPI by default.

```bash
EXPOSE_ADMIN_DOCS=1 uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## Security Note (Public Repository)
Do not commit private hosts, tokens, or credentials to docs or source files.
Store all sensitive values in `.env` (gitignored) and inject them at runtime.

### Example Usage

**1. Querying Port Status (Agent View):**

```bash
set -a && source .env && set +a
curl -X GET "http://${DEV_NODE_IP}:8001/api/v1/pcs/terminals/DEHAM/status"

```

*Response (DCSA format):*

```json
{
  "portCode": "DEHAM",
  "operationalStatus": "NORMAL",
  "metrics": {
    "yardDensityPercent": 65.0,
    "availableReeferPlugs": 120,
    "availableCapacityTEU": 25000
  },
  "updatedAt": "2026-01-01T00:00:00Z"
}

```

**2. Injecting a Disruption (Simulation Controller View):**

```bash
set -a && source .env && set +a
curl -X POST "http://${DEV_NODE_IP}:8001/admin/simulation/scenario" \
-H "Content-Type: application/json" \
-d '{"targetPort": "DEHAM", "scenarioType": "STORM_SURGE", "severity": "HIGH"}'

```

## 📖 Roadmap (WSC 2026 Advanced Version)

* Dynamic AIS congestion emulation (vessel dwell times).
* Automatic Port Congestion Surcharge (PCS) generation based on yard density.
* Spillover effects (closing Hamburg automatically congests Rotterdam over 24h).

## 📝 License

MIT License.
