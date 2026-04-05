from collections.abc import Callable
from typing import TYPE_CHECKING

from src.core.des_loop import SimulationEnvironment, Vessel, execute_vessel_arrival
from src.schemas.simulation import (
    SandboxExecutionOutput,
    ScenarioExecutionResult,
    ScenarioMetrics,
    SimulationEvent,
    SimulationExecutionRequest,
)

if TYPE_CHECKING:
    from src.services.port_manager import PortManager


class SimulationEngine:
    """
    The Physics and Rules Engine for evaluating shipping schemas.
    Handles Discrete Event Simulation loops and evaluates candidate scenarios.
    Returns deterministic results mapping without applying Pareto math optimizations.
    """

    def __init__(self, port_manager: "PortManager | None" = None) -> None:
        self.port_manager = port_manager

    def execute_scenarios(self, request: SimulationExecutionRequest) -> SandboxExecutionOutput:
        """
        Takes an array of proposed scenarios, loops through each, applying queuing theory
        and stochastic disruptions to yield the final outcomes.
        """
        results: list[ScenarioExecutionResult] = []

        for scenario in request.scenarios:
            env = SimulationEnvironment(port_manager=self.port_manager)

            env.history.append(
                SimulationEvent(
                    timestamp=0.0,
                    event_type="SIMULATION_START",
                    details=f"Began simulation for {scenario.scenario_id}",
                )
            )

            # Schedule arrivals natively using predictable temporal jumps
            vessel = Vessel(vessel_id=f"V-{scenario.scenario_id}", teu_payload=5000)
            base_transit_hours = 48.0

            for i, port_code in enumerate(scenario.target_ports):
                arrival_time = i * base_transit_hours

                # Bind lexical scope for the loop variable carefully
                def make_action(pc: str) -> Callable[[SimulationEnvironment], None]:
                    def _action(e: SimulationEnvironment) -> None:
                        execute_vessel_arrival(e, vessel, pc)

                    return _action

                env.schedule(
                    delay=arrival_time,
                    event_type="VESSEL_ARRIVAL",
                    details=f"Vessel transited to {port_code}",
                    action=make_action(port_code),
                )

            env.run()

            # Analyze termination boundaries
            status = "SUCCESS"
            failure_reason = None
            for event in env.history:
                if event.event_type == "INFEASIBLE_DURING_SIMULATION":
                    status = "INFEASIBLE_DURING_SIMULATION"
                    failure_reason = event.details
                    break

            metrics = None
            if status == "SUCCESS":
                metrics = ScenarioMetrics(
                    total_lead_time_hours=env.metrics.total_lead_time_hours,
                    average_queue_time_hours=env.metrics.average_queue_time_hours,
                    sla_breach_probability=0.05,  # Fixed SLA logic unless instructed otherwise
                    total_cost_usd=env.metrics.total_cost_usd,
                    penalty_cost_usd=env.metrics.penalty_cost_usd,
                    max_yard_utilization_pct=env.metrics.max_yard_utilization_pct,
                    bottleneck_severity=env.metrics.bottleneck_severity,
                )

            env.history.append(
                SimulationEvent(
                    timestamp=env.now,
                    event_type="SIMULATION_END",
                    details=f"Completed simulation for {scenario.scenario_id}",
                )
            )

            results.append(
                ScenarioExecutionResult(
                    scenario_id=scenario.scenario_id,
                    execution_status=status,
                    metrics=metrics,
                    critical_events=env.history,
                    failure_reason=failure_reason,
                )
            )

        return SandboxExecutionOutput(
            run_id=request.run_id,
            simulated_scenarios=results,
        )
