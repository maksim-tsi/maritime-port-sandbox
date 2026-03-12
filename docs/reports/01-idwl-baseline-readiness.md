# IDWL Baseline Readiness Audit — Maritime Port Sandbox

Date: 2026-03-12  
Scope: Architectural + domain audit for the IDWL “Baseline” version (deterministic FastAPI mock API).

## Executive Summary
The current codebase meets the baseline requirements for determinism and DCSA-shaped responses, and satisfies the three audit checks requested:

1. `STORM_SURGE` sets `availableCapacityTEU` to `0` while leaving `yardDensityPercent` unchanged.
2. FastAPI routers do not manipulate the in-memory store directly; state access is isolated behind dependency injection and a service layer.
3. The deterministic clock (`updatedAt`) increments by exactly **1 second** per successful mutation.

## Audit Checklist & Evidence

### 1) Domain rule: `STORM_SURGE` drops capacity to zero and preserves yard density
**Requirement:** When `scenarioType=STORM_SURGE`, the port must become `CLOSED`, capacity must drop to `0`, and `yardDensityPercent` must remain **exactly** as it was before the storm.

**Implementation evidence**
- `src/services/port_manager.py`:
  - `STORM_SURGE` uses `replace(... operational_status=CLOSED, available_capacity_teu=0)` and does **not** touch `yard_density_percent` or `available_reefer_plugs`, so they remain unchanged.
  - The “Closure Rule” re-enforces `available_capacity_teu=0` whenever status is `CLOSED`, ensuring no later rule can reintroduce capacity.

**Why yard density cannot change inadvertently**
- No rule in `PortManager.inject_scenario()` writes to `yard_density_percent` in the `STORM_SURGE` branch.
- The Density Rule only changes `operational_status` when `yard_density_percent > 85.0` **and** status is `NORMAL`. Under `STORM_SURGE` the status is `CLOSED`, so this rule cannot alter the outcome.

**Test evidence**
- `tests/test_port_manager.py` asserts:
  - `availableCapacityTEU == 0`
  - `yardDensityPercent` equals the pre-scenario value

### 2) Architecture: Dependency Injection isolates `src/state/store.py` from FastAPI routers
**Requirement:** Routers must not reach into the store directly; they must call a service, and the store must be provided via DI / app state.

**Implementation evidence**
- Routers only depend on `PortManager` via `Depends(get_port_manager)`:
  - Public router: `src/api/public/pcs.py`
  - Admin router: `src/api/admin/simulation.py`
- DI boundary is centralized in `src/core/deps.py`:
  - Reads `request.app.state.port_store` and constructs `PortManager(store=store)`.
- Store wiring happens in the app factory `src/core/app.py`:
  - `app.state.port_store = port_store or InMemoryPortStore()`
  - Optional injection point `create_app(..., port_store=...)` allows tests (and future scenarios) to provide a different store without changing router code.

**Conclusion**
The FastAPI transport layer (routers) is kept “thin” and does not mutate/inspect `InMemoryPortStore` directly; the store is accessed exclusively by the service layer via DI.

### 3) Determinism: `updatedAt` increments by exactly 1 second per mutation
**Requirement:** `updatedAt` must be deterministic and advance by **exactly** 1 second per successful mutation.

**Implementation evidence**
- `src/state/store.py`:
  - Defines `SIMULATION_EPOCH_UTC = 2026-01-01T00:00:00Z`.
  - On each `mutate(...)` call, under a lock:
    - increments `_clock` by `timedelta(seconds=1)`
    - overwrites the updated state’s `updated_at` with the new clock value
    - returns a response with `updatedAt=state.updated_at`

**Semantics note (what counts as “successful mutation”)**
- If the port does not exist, `self._ports[normalized]` raises `KeyError` and the clock does **not** increment.
- For existing ports, every call to `mutate(...)` increments the clock exactly once.

**Test evidence**
- `tests/test_port_manager.py` asserts sequential timestamps:
  - first mutation → `SIMULATION_EPOCH_UTC + 1s`
  - second mutation → `SIMULATION_EPOCH_UTC + 2s`

## Baseline Readiness Verdict
**PASS** — The baseline’s key architectural boundaries and the specified domain/determinism constraints are correctly implemented and verified by automated tests.

