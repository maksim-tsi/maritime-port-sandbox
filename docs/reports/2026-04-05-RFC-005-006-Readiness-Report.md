# Gap Analysis: RFC-005 and RFC-006 Readiness Report
Date: 2026-04-05

## Executive Summary
This report provides a comprehensive Gap Analysis of the `maritime-port-sandbox` repository regarding its readiness to transition from a static mock API to a Discrete Event Simulation (DES) engine as mandated by **RFC-005** and **RFC-006**. The focus is on the `schemas/`, `api/`, and `services/` layers, comparing the As-Is state against the requirements. No application code has been modified during the generation of this report.

---

## 1. As-Is State

### 1.1 `schemas/`
Currently, the `src/schemas/` directory houses strict Pydantic v2 models designed exclusively around static state queries and admin scenarios.
* **`dcsa.py`:** Contains DCSA standard models (`TerminalMetrics`, `PortStatusResponse`, `OperationalStatus`) utilized for returning deterministic state representations for terminals.
* **`admin.py`:** Contains models required for deterministic state mutation (`SetStateRequest`, `InjectScenarioRequest`) and chaos scenarios (`ChaosScenarioType`, `Severity`).

### 1.2 `api/`
The API layout relies heavily on simple state lookups or targeted state injections. 
* **`public/pcs.py`:** Exposes a simple `GET /api/v1/pcs/terminals/{portCode}/status` endpoint. 
* **`admin/...`:** Handles out-of-band administrative setups and scenario injections.
It relies purely on REST principles around accessing static states and does not currently expose any analytical or simulation interfaces.

### 1.3 `services/`
* **`port_manager.py`:** The singular business logic unit handling the repository context. Its role is confined to querying `InMemoryPortStore`, and applying deterministic formulas (such as spillover capping and capacity calculation under chaos scenarios). It contains no discrete event simulation structures, queues, or timeline progression functionality.

---

## 2. To-Be State (Gaps)

In order to meet the specifications of **RFC-005** and **RFC-006**, the primary identified gaps are:

### 2.1 Missing Pydantic Models (The `schemas/` Gap - RFC-005)
The repository lacks standard DES models. Per RFC-005, the following models must be implemented to establish a firm contract between the Sandbox and the Orchestrator without modifying existing DCSA endpoints:
* `ScenarioMetrics` (capturing Time/SLA, Financial Cost, and Risk utilization)
* `SimulationEvent` (representing atomic timeframe milestones or breakdowns)
* `ScenarioExecutionResult` (yielding either Success, Infeasible, or Error markers)
* `SandboxExecutionOutput` (the root execution representation)

### 2.2 Missing Endpoints (The `api/` Gap - RFC-005)
There is no routing present that can ingest an execution run of multiple proposals. There must be a new endpoint routing (e.g., `POST /api/v1/simulation/execute`) built strictly to parse proposals and flush the `SandboxExecutionOutput` response.

### 2.3 Separation of Concerns (The `services/` Gap - RFC-006)
According to RFC-006, evaluating simulation queues and resolving scenario validity across a time-step must live in the Sandbox, and `services/port_manager.py` should NOT be expanded to perform this.
* **Missing Engine:** A new, separated subsystem (`src/services/simulation_engine.py` or equivalent) is missing outright. It must serve as the "Physics and Rules engine" that processes internal time-stepping and OR probability, returning raw scalar events.
* **Strict Abstraction Limit:** The existing services strictly govern state mutation. Operations to discern the Pareto-optimal frontier must remain offloaded. The new engine needs to be implemented simply mapping raw outcomes into the DES schema—maintaining the firm separation constraint against agent retries or Markdown report formatting.

---

## 3. Step-by-Step Implementation Plan

To close the identified gaps efficiently, the following prioritized execution plan is recommended:

**Phase 1: Execution Interface schemas (Addressing RFC-005)**
1. Create `src/schemas/simulation.py`.
2. Implement `ScenarioMetrics`, `SimulationEvent`, `ScenarioExecutionResult`, and `SandboxExecutionOutput` utilizing strict `Pydantic v2` model specifications.

**Phase 2: DES Simulation Mechanics (Addressing RFC-006)**
1. Create a segregated domain module `src/services/simulation_engine.py`.
2. Implement the mathematical algorithms for capacity checking, queuing formulas, and disruption handling without bleeding over into Pareto frontier optimizations or retry-loops.
3. Hook these logic bounds to emit instantiated metrics conforming to the schemas in Phase 1.

**Phase 3: Transport Layer (Addressing RFC-005)**
1. Create `src/api/public/simulation.py` and assign a `POST /api/v1/simulation/execute` endpoint handler.
2. Route this controller purely to `simulation_engine.py` (maintaining the legacy `port_manager.py` strictly for context gathering).
3. Bind the new API router to `src/core/app.py` / `main.py`.

**Phase 4: Validation**
1. Conform with CI enforcement by running `ruff check .` on the newly introduced modules.
2. Build corresponding strict test modules (`tests/services/test_simulation_engine.py`, `tests/api/test_simulation.py`). The project mandate expects 100% test coverage around domain logic changes. 
3. Validate OpenAPI schemas against the proposed metrics structure and regenerate dependent documentation.
