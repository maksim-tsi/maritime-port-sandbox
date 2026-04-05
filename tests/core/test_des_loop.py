from src.core.des_loop import SimulationEnvironment, Terminal, Vessel


def test_vessel_and_terminal_dataclasses() -> None:
    """Verify basic instantiation of state trackers."""
    vessel = Vessel(vessel_id="V-123", teu_payload=5000)
    assert vessel.vessel_id == "V-123"
    assert vessel.teu_payload == 5000

    terminal = Terminal(
        terminal_id="DEHAM",
        available_capacity_teu=25000,
        yard_density_percent=10.5,
    )
    assert terminal.terminal_id == "DEHAM"
    assert terminal.available_capacity_teu == 25000
    assert terminal.yard_density_percent == 10.5


def test_simulation_environment_deterministic_ordering() -> None:
    """
    Verify events are processed in exact temporal order.
    If timestamps are equal, processing defaults deterministically to the queue sequence number.
    """
    env = SimulationEnvironment()

    # Schedule items completely out of order
    env.schedule(5.0, "EVENT_LATE", "Should be third")
    env.schedule(1.0, "EVENT_EARLY", "Should be first")
    env.schedule(1.0, "EVENT_TIEBREAKER", "Should be second because of sequence")

    env.run()

    assert env.now == 5.0
    assert len(env.history) == 3

    assert env.history[0].event_type == "EVENT_EARLY"
    assert env.history[0].timestamp == 1.0

    assert env.history[1].event_type == "EVENT_TIEBREAKER"
    assert env.history[1].timestamp == 1.0

    assert env.history[2].event_type == "EVENT_LATE"
    assert env.history[2].timestamp == 5.0


def test_simulation_environment_action_chains() -> None:
    """
    Verify that executing actions correctly pushes new events sequentially on the fly
    without breaking the simulation clock sequence.
    """
    env = SimulationEnvironment()

    def unload_action(e: SimulationEnvironment) -> None:
        # Once unloaded, we schedule departure 2.0 hours later
        e.schedule(delay=2.0, event_type="VESSEL_DEPARTURE", details="Vessel leaves")

    env.schedule(10.0, "VESSEL_UNLOADING_START", "Vessel begins unloading", action=unload_action)

    env.run()

    # Total simulated time should finish at 10.0 + 2.0 = 12.0
    assert env.now == 12.0
    assert len(env.history) == 2

    assert env.history[0].event_type == "VESSEL_UNLOADING_START"
    assert env.history[0].timestamp == 10.0

    assert env.history[1].event_type == "VESSEL_DEPARTURE"
    assert env.history[1].timestamp == 12.0


def test_simulation_environment_run_until() -> None:
    """Verify simulation halt conditions when `until` is utilized."""
    env = SimulationEnvironment()

    env.schedule(5.0, "FIRST", "")
    env.schedule(10.0, "SECOND", "")
    env.schedule(15.0, "THIRD", "")

    # Run strictly up to timestep 10.0
    env.run(until=10.0)

    assert env.now == 10.0
    assert len(env.history) == 2
    assert len(env.event_queue) == 1
    
    # Only 1st and 2nd should have fired
    assert env.history[-1].event_type == "SECOND"
