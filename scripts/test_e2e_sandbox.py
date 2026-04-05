import json
from src.schemas.simulation import (
    SimulationExecutionRequest,
    CandidateScenario,
)
from src.schemas.admin import SetStateRequest
from src.services.simulation_engine import SimulationEngine
from src.services.port_manager import PortManager
from src.state.store import InMemoryPortStore

def print_result(result):
    print(f"\n{'='*50}")
    print(f"Scenario: {result.scenario_id}")
    print(f"Status:   {result.execution_status}")
    if result.failure_reason:
        print(f"Failure Reason: {result.failure_reason}")
    if result.metrics:
        print("\nMetrics:")
        print(f"  Total Lead Time (hrs): {result.metrics.total_lead_time_hours:.1f}")
        print(f"  Avg Queue Time (hrs):  {result.metrics.average_queue_time_hours:.1f}")
        print(f"  Total Cost (USD):      ${result.metrics.total_cost_usd:,.2f}")
        print(f"  Penalty Cost (USD):    ${result.metrics.penalty_cost_usd:,.2f}")
        print(f"  Bottleneck Severity:   {result.metrics.bottleneck_severity:.2f}")
        print(f"  Peak Yard Utilization: {result.metrics.max_yard_utilization_pct:.1f}%")
        print(f"  SLA Breach Prob:       {result.metrics.sla_breach_probability:.2f}")

    print("\nCritical Events Timeline:")
    for event in result.critical_events:
        print(f"  {event.timestamp:05.1f}h | {event.event_type:<30} | {event.details}")
    print(f"{'='*50}")

def main():
    print("Initialize Sandbox Environment (DES + OR Engine)...")
    store = InMemoryPortStore()
    port_manager = PortManager(store=store)
    engine = SimulationEngine(port_manager=port_manager)

    # Congestion path injection: restrict DEHAM to 2000 TEU. Vessel has 5000 TEU load.
    print("Injecting Admin State: Restricting DEHAM capacity to 2000 TEU...")
    port_manager.set_state(SetStateRequest(capacities={"DEHAM": 2000, "SGSIN": 100000}))

    print("Building Synthetic Request (Vessel Payload: ~5000 TEU)...")
    scenario_a = CandidateScenario(scenario_id="HAPPY_PATH_SGSIN", target_ports=["SGSIN"])
    scenario_b = CandidateScenario(scenario_id="CONGESTION_PATH_DEHAM", target_ports=["DEHAM"])

    request = SimulationExecutionRequest(
        run_id="E2E_FINAL_VALIDATION",
        scenarios=[scenario_a, scenario_b]
    )

    print("Submitting to SimulationEngine...")
    sandbox_output = engine.execute_scenarios(request)

    for result in sandbox_output.simulated_scenarios:
        print_result(result)

if __name__ == "__main__":
    main()
