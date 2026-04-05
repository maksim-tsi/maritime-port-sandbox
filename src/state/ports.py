from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class PortConfig:
    max_capacity_teu_per_day: int
    initial_yard_density_percent: float
    initial_available_reefer_plugs: int
    initial_available_capacity_teu: int


SUPPORTED_PORTS: Final[dict[str, PortConfig]] = {
    "DEHAM": PortConfig(
        max_capacity_teu_per_day=25_000,
        initial_yard_density_percent=65.0,
        initial_available_reefer_plugs=120,
        initial_available_capacity_teu=25_000,
    ),
    "NLRTM": PortConfig(
        max_capacity_teu_per_day=40_000,
        initial_yard_density_percent=60.0,
        initial_available_reefer_plugs=200,
        initial_available_capacity_teu=40_000,
    ),
    "BEANR": PortConfig(
        max_capacity_teu_per_day=32_000,
        initial_yard_density_percent=62.0,
        initial_available_reefer_plugs=160,
        initial_available_capacity_teu=32_000,
    ),
    "CNSHA": PortConfig(
        max_capacity_teu_per_day=130_000,
        initial_yard_density_percent=60.0,
        initial_available_reefer_plugs=650,
        initial_available_capacity_teu=130_000,
    ),
    "SGSIN": PortConfig(
        max_capacity_teu_per_day=100_000,
        initial_yard_density_percent=60.0,
        initial_available_reefer_plugs=500,
        initial_available_capacity_teu=100_000,
    ),
    "DEBRV": PortConfig(
        max_capacity_teu_per_day=15_000,
        initial_yard_density_percent=60.0,
        initial_available_reefer_plugs=120,
        initial_available_capacity_teu=15_000,
    ),
    "MYPKG": PortConfig(
        max_capacity_teu_per_day=38_000,
        initial_yard_density_percent=60.0,
        initial_available_reefer_plugs=190,
        initial_available_capacity_teu=38_000,
    ),
}


def get_port_config(port_code: str) -> PortConfig:
    return SUPPORTED_PORTS[port_code]
