# Core: Discrete Event Simulation (DES)

This directory houses the foundational simulation mechanics for the Maritime Port Sandbox.

## DES Loop Mechanics (`des_loop.py`)

The simulation engine is implemented as a lightweight, deterministic Discrete Event Simulator. Instead of advancing time linearly (e.g., tick-by-tick), the engine advances chronologically based on scheduled events.

### Priority Queue and Event Scheduling

At the heart of the engine is `SimulationEnvironment`, which manages a priority queue (`heapq`).
* **`DESEvent`**: Wraps simulation actions with a timestamp. Events are ordered naturally by timestamp out to an arbitrary time horizon. A sequence number resolves ties deterministically.
* **Scheduling**: New actions are scheduled with delays (e.g., pushing `VESSEL_ARRIVAL_RETRY` out by 24 hours). The heap is correctly maintained, guaranteeing temporal correctness.
* **Execution**: the `.run()` loop continuously pops the next chronological event from the heap, fast-forwards the clock (`self.now`) to that exact moment, and evaluates the callback constraint.
* **History Trailing**: Each event appends an immutable `SimulationEvent` to `SimulationEnvironment.history` establishing explainability logic and enabling Pareto objective calculation.
