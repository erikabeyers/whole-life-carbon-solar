from typing import Optional, Dict, Any

from pydantic import BaseModel


class BessInput(BaseModel):
    """Battery Energy Storage System (BESS) inputs."""
    included: bool = False
    capacity_kwh: float = 0.0
    embodied_kgCO2e_per_kwh: float = 75.0
    roundtrip_efficiency: Optional[float] = 0.9


def calculate_bess_emissions(bess_input: Optional[BessInput]) -> Dict[str, Any]:
    """Calculate BESS embodied emissions."""
    if bess_input is None or not bess_input.included:
        return {
            "total_kgCO2e": 0.0,
            "total_tonnesCO2e": 0.0,
            "note": "No BESS included",
        }

    capacity_kwh = max(0.0, bess_input.capacity_kwh)
    factor = max(0.0, bess_input.embodied_kgCO2e_per_kwh)
    total_kg = capacity_kwh * factor

    return {
        "capacity_kwh": capacity_kwh,
        "embodied_kgCO2e_per_kwh": factor,
        "roundtrip_efficiency": bess_input.roundtrip_efficiency,
        "total_kgCO2e": round(total_kg, 2),
        "total_tonnesCO2e": round(total_kg / 1000.0, 3),
    }