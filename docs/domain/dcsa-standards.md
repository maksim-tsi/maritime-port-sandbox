# Domain Knowledge: DCSA Standards & Port Logistics 🚢

As an autonomous agent developing the Maritime Port Sandbox, you must strictly adhere to the domain rules defined in this document. The sandbox emulates the **Digital Container Shipping Association (DCSA)** Track & Trace and Operational Vessel Schedule (OVS) standards, specifically focusing on terminal availability and capacity metrics.

## 1. Supported UN/LOCODEs
In the maritime industry, locations are identified by 5-character UN/LOCODEs. For the IDWL 2026 baseline, the sandbox supports **only** the following ports. 
 
Any request for a port outside this list must result in an `HTTP 404 Not Found`.

| UN/LOCODE | City | Country | Max Capacity (Mock TEU/day) |
| :--- | :--- | :--- | :--- |
| **DEHAM** | Hamburg | Germany | 25,000 |
| **NLRTM** | Rotterdam | Netherlands | 40,000 |
| **BEANR** | Antwerp | Belgium | 32,000 |
| **CNSHA** | Shanghai | China | 130,000 |
| **SGSIN** | Singapore | Singapore | 100,000 |
| **MYPKG** | Port Klang | Malaysia | 38,000 |

*(Note: TEU stands for Twenty-foot Equivalent Unit, the standard measure of container capacity).*

## 2. Terminal Operational Status
Ports do not simply turn "on" or "off". We use a strict enumeration for the operational status of a port:

* `NORMAL`: Port is operating efficiently. Yard density is < 70%.
* `RESTRICTED`: Port is experiencing delays (e.g., due to weather, minor strikes, or high density). Operations continue but at reduced capacity. Yard density is 70% - 85%.
* `CLOSED`: Port operations are completely halted (e.g., severe storm surge). Available capacity is 0.

## 3. Pydantic Schemas (The DCSA Contract)
When generating the FastAPI responses in `src/schemas/dcsa.py`, you MUST use the following structure. Do not invent new fields.

```python
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime

class OperationalStatus(str, Enum):
    NORMAL = "NORMAL"
    RESTRICTED = "RESTRICTED"
    CLOSED = "CLOSED"

class TerminalMetrics(BaseModel):
    yardDensityPercent: float = Field(..., description="Current yard density. 0.0 to 100.0")
    availableReeferPlugs: int = Field(..., description="Number of available refrigerated container plugs")
    availableCapacityTEU: int = Field(..., description="Available daily processing capacity in TEU")

class PortStatusResponse(BaseModel):
    portCode: str = Field(..., description="5-character UN/LOCODE")
    operationalStatus: OperationalStatus
    metrics: TerminalMetrics
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

```

## 4. Business Rules for State Orchestration

When the Simulation Controller (Admin API) injects a chaos event, the `services/port_manager.py` must enforce the following physical constraints:

1. **The Closure Rule:** If `operationalStatus` is forcefully set to `CLOSED`, the `availableCapacityTEU` must immediately drop to `0`.
2. **The Density Rule:** If `yardDensityPercent` exceeds `85.0`, the `operationalStatus` must automatically transition to `RESTRICTED` (if it was `NORMAL`).
3. **The Spillover Cap:** `availableCapacityTEU` can never exceed the "Max Capacity" defined in the UN/LOCODE table above.

## 5. Event Types (Admin API Chaos Injection)

When building `src/schemas/admin.py` for the Chaos API, use these specific disruption types:

```python
class ChaosScenarioType(str, Enum):
    STORM_SURGE = "STORM_SURGE"         # Sets status to CLOSED
    LABOR_STRIKE = "LABOR_STRIKE"       # Sets status to RESTRICTED, drops TEU by 50%
    YARD_CONGESTION = "YARD_CONGESTION" # Spikes Yard Density > 90%

```

## Summary for the Agent

Do not use generic JSON structures. Every endpoint returning port data MUST serialize through the `PortStatusResponse` Pydantic model. If a test fails because a field is missing, refer back to this exact schema.
