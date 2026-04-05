import heapq
from collections.abc import Callable
from dataclasses import dataclass, field

from src.schemas.simulation import SimulationEvent


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
    action: Callable[["SimulationEnvironment"], None] | None = field(
        default=None, compare=False
    )


class SimulationEnvironment:
    """
    A lightweight, deterministic Discrete Event Simulation loops leveraging heapq.
    Advances exactly from temporal marker to marker.
    Produces arrays of `SimulationEvent` required by the schemas.
    """

    def __init__(self) -> None:
        self.now: float = 0.0
        self.event_queue: list[DESEvent] = []
        self._sequence_counter: int = 0
        self.history: list[SimulationEvent] = []

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
