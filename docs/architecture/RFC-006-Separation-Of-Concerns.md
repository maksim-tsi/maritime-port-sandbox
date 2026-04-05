### RFC-006: Separation of Concerns (DES Environment vs. Multi-Agent Orchestrator)

**Status:** Approved for Variant B (MVP)
**Target:** `maritime-port-sandbox`
**Component:** `services/` and `core/`

#### 1. Context & Motivation
As the Sandbox evolves to include Discrete Event Simulation (DES) capabilities, there is a risk of domain logic leaking across system boundaries. We must strictly define what the Sandbox is responsible for computing versus what is left to the Multi-Agent Orchestrator (`scm-cognitive-sandwich`).

#### 2. Architectural Boundaries
The `maritime-port-sandbox` is the "Physics Engine" and "Rules Engine". It calculates consequences but does not make subjective decisions.

**The Sandbox MUST:**
* Manage internal time-stepping, queuing theory mathematics, and stochastic disruptions (e.g., weather delays, crane breakdowns).
* Execute Operations Research (OR) solvers internally for capacity checking during the simulation.
* Return raw, un-opinionated arrays of `SimulationEvent` and compute the scalar values for the `ScenarioMetrics` axes.

**The Sandbox MUST NOT:**
* **Calculate the Pareto Frontier:** The Sandbox will return the metrics for all requested scenarios. The Python algorithms identifying which scenarios are Pareto-optimal (non-dominated) live entirely in the Orchestrator.
* **Format Human-Readable Reports:** The Sandbox must not generate Markdown, text summaries, or LLM-driven justifications. It strictly returns the JSON schemas defined in RFC-005.
* **Handle Agent Retries:** If a scenario is infeasible, the Sandbox simply logs it in `failure_reason` and moves on. The loop logic (Clarifying Loop) is strictly the Orchestrator's responsibility.

#### 3. Implications for Layered Design (Updating `index.md`)
The directory structure outlined in the current documentation remains valid, but the internal semantics of the `services/` layer will expand:
* `services/port_manager.py` will continue to handle static DCSA state lookups.
* A new service module (e.g., `services/simulation_engine.py`) must be introduced to handle the DES time-stepping and map the results to the `SandboxExecutionOutput` schema. Direct state mutation by routers is still strictly prohibited.