from fastapi import APIRouter, Depends, HTTPException

from src.core.deps import get_port_manager
from src.schemas.dcsa import PortStatusResponse
from src.services.port_manager import PortManager, UnknownPortError

router = APIRouter(prefix="/api/v1/pcs/terminals", tags=["pcs"])


@router.get("/{portCode}/status", response_model=PortStatusResponse)
def get_terminal_status(
    portCode: str,
    port_manager: PortManager = Depends(get_port_manager),
) -> PortStatusResponse:
    try:
        return port_manager.get_port_status(portCode)
    except UnknownPortError as exc:
        raise HTTPException(status_code=404, detail="Port not found") from exc
