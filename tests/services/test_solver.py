import pytest

from src.services.solver import AllocationInfeasibleError, TerminalCapacitySolver


def test_solver_feasible_allocation() -> None:
    """Verify solver correctly identifies when payload cleanly fits into capacity."""
    solver = TerminalCapacitySolver()
    # 5000 payload fits completely into 25000 capacity
    is_feasible = solver.validate_allocation(
        available_capacity_teu=25000, vessel_payload_teu=5000
    )
    assert is_feasible is True


def test_solver_exact_boundary() -> None:
    """Verify solver accurately accepts maximum possible exact fit allocations."""
    solver = TerminalCapacitySolver()
    # 5000 payload fits precisely into 5000 capacity
    is_feasible = solver.validate_allocation(
        available_capacity_teu=5000, vessel_payload_teu=5000
    )
    assert is_feasible is True


def test_solver_infeasible_allocation() -> None:
    """Verify solver correctly raises mathematical infeasibility exception."""
    solver = TerminalCapacitySolver()
    # 5001 payload does not fit into 5000 capacity
    with pytest.raises(AllocationInfeasibleError, match="Infeasible: Required"):
        solver.validate_allocation(available_capacity_teu=5000, vessel_payload_teu=5001)
