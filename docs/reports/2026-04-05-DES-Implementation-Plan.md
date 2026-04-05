# DES & OR Implementation Plan

**Date:** 2026-04-05
**Target:** `maritime-port-sandbox`
**Context:** Transitioning Phase from Stubs to Real Operations Research and DES Simulation.

## 1. Current Gap Analysis

We completed a codebase review focusing on Pydantic schemas (`src/schemas/simulation.py`) and the execution layer (`src/services/simulation_engine.py`). Here are the identified gaps where hardcoding currently bypasses dynamic computation:

- **Orchestrator Routing Ignored:** The loop currently iterates `request.scenarios` but entirely ignores `target_ports` parameter inside the nested `CandidateScenario`. The sandbox applies no geographical or logistical transit contexts.
- **Stubbed Axis 1 (Time & SLA):**
    - `total_lead_time_hours` is strictly hardcoded to return `120.0`.
    - `average_queue_time_hours` defaults mechanically to `2.5`.
    - `sla_breach_probability` remains set at `0.05`.
- **Stubbed Axis 2 (Financial Cost):**
    - `total_cost_usd` is hardcoded to `50000.0`.
    - `penalty_cost_usd` is clamped globally to `0.0`.
- **Stubbed Axis 3 (Risk & Utilization):**
    - `max_yard_utilization_pct` returns a flat `85.0`.
    - `bottleneck_severity` sits statically at `0.2`.
- **Static Event Generation:** The generation mechanism exclusively outputs a generic `SIMULATION_START` (timestamp `0.0`) and `SIMULATION_END` (timestamp `120.0`). It currently fails to output state lifecycle markers (e.g., vessel arrivals, failures, queue overflows) standard to the `SimulationEvent` schema.
- **Port State Disconnect:** The engine runs strictly isolated from `services/port_manager.py` bypassing entirely the dynamic physical constraints mappings (like `availableCapacityTEU`, `yardDensityPercent`, and `operationalStatus` restrictions) that form the DCSA domain standard.

## 2. Architectural Proposal (The Engine)

### Discrete Event Simulation (DES) Strategy
**Recommendation:** Implement a **Custom Lightweight DES Loop** utilizing Python's `heapq` module.
*Why not SimPy?* While `SimPy` is highly efficient, our engine serves exactly one role: parsing deterministic mathematical constraints to formulate explicitly required JSON payload metrics. A bespoke Priority Queue loop mitigates potential generic Async-generator complexity with FastAPI, enforces perfectly trackable step definitions yielding explicitly isolated `SimulationEvent` payloads to the consumer without abstract nesting overheads. 

Time-stepping will be strictly Event-Based. The simulator advances precisely to the next scheduled context marker (e.g. `TIME_T_TRANSIT_COMPLETE`) rather than stepping forward on uniform ticks.

### Operations Research (OR) Integration
**Recommendation:** Combine simulation runs alongside **Pyomo** MILP formulations.
- We will encapsulate a `Pyomo` logic solver under an isolated `src/services/solver.py` module acting natively as a deterministic terminal constraint evaluator.
- Upon dispatching logic into the simulation loop (e.g., `PORT_CAPACITY_CHECK` or `VESSEL_UNLOADING_INIT`), the DES pauses temporal execution and feeds the node configurations to the OR optimizer.
- The solver analyzes whether allocating incoming payload mass will violate rules, such as `yardDensityPercent` hitting the `DCSA` >`85.0` restriction or `availableCapacityTEU` limits. Once validated, queuing mathematical times, processing success branches or penalties append accordingly, and time processing resumes.

## 3. Execution Roadmap

Executing this plan follows a precise path to guarantee 100% testing coverage per our mandate with exactly ZERO mutation to standard API contracts:

### Step 1: Base DES Event Loop
- Initialize foundational state tracking objects (like `Vessel` and `Terminal`).
- Create `src/core/des_loop.py` featuring the `heapq`-powered Priority Event Queue. 
- Formulate exhaustive unit test suites running bare logic using dummy execution `SimulationEvent` types. (Validate deterministic ordering of temporal queues).

### Step 2: Implement OR Constraints Engine
- Add operations logic (`pyomo` and solver deps) inside `requirements.txt`.
- Develop `src/services/solver.py` specifically mapped onto the numerical DCSA standards capabilities defined within the UN/LOCODE mapping.
- Wire deterministic testing suites checking isolated Pyomo boundaries and solver fallback conditions.

### Step 3: Integrating the DCSA Physics
- Establish metric accumulator classes dynamically compiling metrics directly calculated by running iterations: tracking total times, queuing costs offsets, and dynamically measuring peak usage metrics based strictly off state node results.
- Implement API linkages to pull live DCSA terminal attributes from `services/port_manager.py` to drive accurate baseline stats for evaluation runs.

### Step 4: Routing Execution Payloads
- Replace all static output parameters populated within `SimulationEngine.execute_scenarios()`. 
- Feed scenarios seamlessly into the new backend queue structure, capturing raw temporal feedback.
- Guarantee execution seamlessly outputs validated arrays strictly adhering to `SandboxExecutionOutput` standards. Expand all `pytest` validation testing suites per the `AGENTS.md` directive requirements to achieve complete end-to-end integration safety.
