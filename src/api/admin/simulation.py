from fastapi import APIRouter, Depends, HTTPException

from src.core.deps import get_port_manager
from src.schemas.admin import InjectScenarioRequest, SetStateRequest, SetStateResponse
from src.schemas.dcsa import PortStatusResponse
from src.services.port_manager import PortManager, UnknownPortError


def build_router(*, expose_in_openapi: bool) -> APIRouter:
    router = APIRouter(
        prefix="",
        tags=["admin"],
        include_in_schema=expose_in_openapi,
    )

    @router.post("/admin/simulation/scenario", response_model=PortStatusResponse)
    def inject_scenario(
        payload: InjectScenarioRequest,
        port_manager: PortManager = Depends(get_port_manager),
    ) -> PortStatusResponse:
        try:
            return port_manager.inject_scenario(payload)
        except UnknownPortError as exc:
            raise HTTPException(status_code=404, detail="Port not found") from exc

    @router.post("/api/v1/admin/set-state", response_model=SetStateResponse)
    def set_state(
        payload: SetStateRequest,
        port_manager: PortManager = Depends(get_port_manager),
    ) -> SetStateResponse:
        try:
            return port_manager.set_state(payload)
        except UnknownPortError as exc:
            raise HTTPException(status_code=404, detail="Port not found") from exc

    return router
