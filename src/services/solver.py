import pyomo.environ as pyo


class AllocationInfeasibleError(Exception):
    """Raised when the solver determines the payload allocation is mathematically infeasible."""

    pass


class TerminalCapacitySolver:
    """
    Isolated Operational Research solver validating whether a terminal
    can support a vessel's payload based on deterministic rules.
    """

    def __init__(self, solver_name: str = "appsi_highs") -> None:
        self.solver_name = solver_name
        self.solver = pyo.SolverFactory(solver_name)

    def validate_allocation(self, available_capacity_teu: int, vessel_payload_teu: int) -> bool:
        """
        Validates whether unloading `vessel_payload_teu` into `available_capacity_teu`
        is feasible. Formulates a basic Linear Programming constraint.
        Raises AllocationInfeasibleError if mathematically infeasible.
        """
        model = pyo.ConcreteModel()

        # Decision Variable: Amount of TEU transferred
        model.allocation = pyo.Var(within=pyo.NonNegativeReals, bounds=(0, vessel_payload_teu))

        # Constraint 1: We must allocate the exact full payload of the vessel
        model.full_unload = pyo.Constraint(expr=model.allocation == vessel_payload_teu)

        # Constraint 2: The terminal cannot exceed its available capacity
        model.capacity_check = pyo.Constraint(expr=model.allocation <= available_capacity_teu)

        # Dummy objective (we just want to check feasibility)
        model.obj = pyo.Objective(expr=model.allocation, sense=pyo.maximize)

        # Check solver availability
        if self.solver is None:
            self.solver = pyo.SolverFactory(self.solver_name)

        # We suppress output and avoid loading solutions automatically in case of infeasibility
        results = self.solver.solve(model, tee=False, load_solutions=False)

        # Evaluate solver status
        cond = results.solver.termination_condition
        if cond in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
            return True
        elif cond == pyo.TerminationCondition.infeasible:
            raise AllocationInfeasibleError(
                f"Infeasible: Required {vessel_payload_teu} TEU, but terminal only has "
                f"{available_capacity_teu} TEU available."
            )

        return False
