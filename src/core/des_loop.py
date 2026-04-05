import heapq
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.schemas.simulation import SimulationEvent
from src.services.solver import AllocationInfeasibleError, TerminalCapacitySolver

if TYPE_CHECKING:
    from src.services.port_manager import PortManager


@dataclass
class MetricAccumulator:
    """Tracks values mapped to Pareto axes during simulation."""

    total_lead_time_hours: float = 0.0
    total_queue_time_hours: float = 0.0
    queue_count: int = 0
    total_cost_usd: float = 0.0
    penalty_cost_usd: float = 0.0
    max_yard_utilization_pct: float = 0.0
    bottleneck_incidents: int = 0

    @property
    def average_queue_time_hours(self) -> float:
        if self.queue_count == 0:
            return 0.0
        return self.total_queue_time_hours / self.queue_count

    @property
    def bottleneck_severity(self) -> float:
        # A simple normalization for the bottleneck severity metric (0.0 to 1.0)
        return min(1.0, self.bottleneck_incidents * 0.1)


@dataclass
class Vessel:
    """State tracking object for a maritime vessel traversing the simulation."""

    vessel_id: str
    teu_payload: int


@dataclass
class Terminal:
    """State tracking object for a destination port terminal."""

    terminal_id: str
    available_capacity_teu: int = 0
    yard_density_percent: float = 0.0


@dataclass(order=True)
class DESEvent:
    """
    An event wrapper pushed into the priority queue.
    Ordered naturally by timestamp, with sequence_num serving as a deterministic tie-breaker.
    """

    timestamp: float
    sequence_num: int
    event_type: str = field(compare=False)
    details: str = field(compare=False)
    action: Callable[["SimulationEnvironment"], None] | None = field(default=None, compare=False)


class SimulationEnvironment:
    """
    A lightweight, deterministic Discrete Event Simulation loop leveraging heapq.
    Advances exactly from temporal marker to marker.
    Produces arrays of `SimulationEvent` required by the schemas.
    """

    def __init__(self, port_manager: "PortManager | None" = None) -> None:
        self.now: float = 0.0
        self.event_queue: list[DESEvent] = []
        self._sequence_counter: int = 0
        self.history: list[SimulationEvent] = []
        self.port_manager = port_manager
        self.metrics = MetricAccumulator()

    def schedule(
        self,
        delay: float,
        event_type: str,
        details: str,
        action: Callable[["SimulationEnvironment"], None] | None = None,
    ) -> None:
        """Schedules a future event onto the priority heap."""
        self._sequence_counter += 1
        event = DESEvent(
            timestamp=self.now + delay,
            sequence_num=self._sequence_counter,
            event_type=event_type,
            details=details,
            action=action,
        )
        heapq.heappush(self.event_queue, event)

    def run(self, until: float | None = None) -> None:
        """
        Pulls events continuously from the heap and evaluates them sequentially,
        updating the chronological clock (`self.now`) to the exact moments of transition.
        """
        while self.event_queue:
            if until is not None and self.event_queue[0].timestamp > until:
                break

            event = heapq.heappop(self.event_queue)
            self.now = event.timestamp

            # Execute behavior if an action is associated with this event
            if event.action:
                event.action(self)

            # Record strictly to history compliant with Pydantic SimulationEvent modeling
            self.history.append(
                SimulationEvent(
                    timestamp=self.now,
                    event_type=event.event_type,
                    details=event.details,
                )
            )


def execute_vessel_arrival(
    env: SimulationEnvironment, vessel: Vessel, terminal_id: str, retry_count: int = 0
) -> None:
    """
    Action logic for when a vessel attempts to arrive and unload at a terminal.
    Queries the PortManager for DCSA physical constraints, runs the OR solver,
    and implements queuing logic if capacity is infeasible.
    """
    if retry_count > 10:
        env.schedule(
            delay=0.0,
            event_type="INFEASIBLE_DURING_SIMULATION",
            details=f"Vessel {vessel.vessel_id} exceeded maximum queue retries at {terminal_id}",
        )
        return

    # 1. DCSA Integration
    capacity_teu = 50000
    density_pct = 50.0

    if env.port_manager:
        try:
            status = env.port_manager.get_port_status(terminal_id)
            capacity_teu = status.metrics.availableCapacityTEU
            density_pct = status.metrics.yardDensityPercent
        except Exception:
            pass

    # Update Peak Utilization Metric
    env.metrics.max_yard_utilization_pct = max(env.metrics.max_yard_utilization_pct, density_pct)

    # 2. Solver Check
    solver = TerminalCapacitySolver()
    try:
        # Evaluate solver constraint
        solver.validate_allocation(capacity_teu, vessel.teu_payload)

        # Success Unload!
        processing_time = 12.0
        env.metrics.total_lead_time_hours += processing_time
        env.metrics.total_cost_usd += 15000.0  # Base operational cost

        env.schedule(
            delay=processing_time,
            event_type="UNLOADING_COMPLETE",
            details=f"Vessel {vessel.vessel_id} successfully unloaded at {terminal_id}",
            action=None,
        )

    except AllocationInfeasibleError:
        # 3. Queue Mechanics
        env.metrics.queue_count += 1
        queue_delay = 24.0  # Wait 24 hours before retrying
        env.metrics.total_queue_time_hours += queue_delay
        env.metrics.total_lead_time_hours += queue_delay
        env.metrics.penalty_cost_usd += 5000.0  # Accrue penalty
        env.metrics.total_cost_usd += 5000.0
        env.metrics.bottleneck_incidents += 1

        # Schedule the retry
        env.schedule(
            delay=queue_delay,
            event_type="VESSEL_ARRIVAL_RETRY",
            details=f"Vessel {vessel.vessel_id} retrying unloading at {terminal_id} after delay",
            action=lambda e: execute_vessel_arrival(
                e, vessel, terminal_id, retry_count=retry_count + 1
            ),
        )
