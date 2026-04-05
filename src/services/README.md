# Services: Orchestration and Operations Research

This directory contains the higher-level service logic bridging the Core DES loop with strict terminal and physical constraint validations.

## `simulation_engine.py`

This module acts as the orchestrator.
* **Scenario Evaluation**: Receives a `SimulationExecutionRequest` containing isolated scenarios (e.g., target routing configurations).
* **Flow Management**: Wraps the `SimulationEnvironment`, injects state context via `PortManager`, and synthesizes vessel schedules.
* **Result Assembly**: Resolves metrics and event histories into deterministically reproducible `ScenarioExecutionResult` objects allowing external RL or logic evaluators to interpret simulation performance without polling.

## `solver.py`

This module integrates Operations Research bounds checking into the simulation.
* **MILP Validation**: Implements `TerminalCapacitySolver`, relying heavily on Python's `pyomo` package, to perform mathematical viability checks.
* **Deterministic Feasibility**: Models unloading logic as a linear programming constraint. If constraints cannot be met efficiently, Pyomo signals an infeasible state raising an `AllocationInfeasibleError`.
* **Coupling**: The generated exceptions are handled safely within `des_loop.py` actions, triggering DES retries, congestion delays, and financial penalties dynamically.
