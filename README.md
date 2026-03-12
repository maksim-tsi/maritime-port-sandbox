# Maritime Port Sandbox ⚓️

A lightweight, deterministic API emulator for European maritime logistics. This sandbox simulates Port Community Systems (PCS) and returns structured, industry-standard data based on the **Digital Container Shipping Association (DCSA)** schemas. 

This repository serves as the "Ground Truth" environment for testing AI agents and Operations Research (OR) solvers in supply chain disruption scenarios, specifically developed for the baseline experiments of our IDWL 2026 submission.

## 🎯 Purpose
When testing autonomous supply chain agents, continuous scraping of live news or commercial APIs is computationally expensive, prone to rate limits, and non-reproducible. This Sandbox solves this by providing:
1. **DCSA-compliant Artifacts:** Agents consume standard JSON objects instead of unstructured HTML.
2. **Absolute Reproducibility:** Disruptions (e.g., a storm closing a port) are injected deterministically via an Admin API.
3. **Zero Cost:** No paid subscriptions to AIS aggregators or commercial PCS platforms required.

## 🚀 Features (Baseline Version)
* **FastAPI Backend:** High-performance, async REST API.
* **Terminal Status Endpoint:** Simulates port availability for the Northern European triad (`DEHAM` - Hamburg, `NLRTM` - Rotterdam, `BEANR` - Antwerp).
* **Chaos Injection (Admin API):** A hidden endpoint to artificially degrade port capacities to trigger rerouting scenarios for external OR solvers.

## 🛠️ Quick Start

### Requirements
* Python 3.11+
* Docker & Docker Compose (optional but recommended)

### Running Locally
```bash
# Clone the repository
git clone https://github.com/maksim-tsi/maritime-port-sandbox.git
cd maritime-port-sandbox

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000

```

### Example Usage

**1. Querying Port Status (Agent View):**

```bash
curl -X GET http://localhost:8000/api/v1/pcs/terminals/DEHAM/status

```

*Response (DCSA format):*

```json
{
  "portCode": "DEHAM",
  "operationalStatus": "NORMAL",
  "metrics": {
    "yardDensityPercent": 65.0,
    "availableReeferPlugs": 120
  }
}

```

**2. Injecting a Disruption (Simulation Controller View):**

```bash
curl -X POST http://localhost:8000/admin/simulation/scenario \
-H "Content-Type: application/json" \
-d '{"targetPort": "DEHAM", "scenarioType": "STORM_SURGE", "severity": "HIGH"}'

```

## 📖 Roadmap (WSC 2026 Advanced Version)

* Dynamic AIS congestion emulation (vessel dwell times).
* Automatic Port Congestion Surcharge (PCS) generation based on yard density.
* Spillover effects (closing Hamburg automatically congests Rotterdam over 24h).

## 📝 License

MIT License.
