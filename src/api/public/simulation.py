from fastapi import APIRouter, Depends

from src.core.deps import get_simulation_engine
from src.schemas.simulation import SandboxExecutionOutput, SimulationExecutionRequest
from src.services.simulation_engine import SimulationEngine

router = APIRouter(prefix="/api/v1/simulation", tags=["simulation"])


@router.post("/execute", response_model=SandboxExecutionOutput)
def execute_simulation(
    request: SimulationExecutionRequest,
    engine: SimulationEngine = Depends(get_simulation_engine),
) -> SandboxExecutionOutput:
    return engine.execute_scenarios(request)
