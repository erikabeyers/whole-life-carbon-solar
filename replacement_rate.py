from typing import Optional, Dict, Any

from pydantic import BaseModel


class ReplacementInput(BaseModel):
    """Component replacements & degradation (B2-B5)"""
    system_lifetime_years: int = 25
    module_degradation_rate_pct_per_year: float = 0.5
    inverter_lifetime_years: Optional[int] = 12
    inverter_embodied_kgCO2e_per_kwp: Optional[float] = 30.0
    additional_replacement_percent_of_embodied: Optional[float] = 0.0


def calculate_replacement_emissions(
    replacements_input: Optional[ReplacementInput],
    capacity_kwp: float,
    annual_generation_kwh: float,
    embodied_carbon_kgCO2e: float,
    carbon_factor: float,
) -> Dict[str, Any]:
    """Calculate replacement emissions and degraded lifetime output (B2-B5)."""
    if replacements_input is None:
        return {
            "total_kgCO2e": 0.0,
            "total_tonnesCO2e": 0.0,
            "note": "No replacement inputs provided",
        }

    lifetime_years = max(1, replacements_input.system_lifetime_years)
    degradation_rate = max(0.0, replacements_input.module_degradation_rate_pct_per_year) / 100.0
    degradation_factor = 1.0 - degradation_rate

    lifetime_generation_kwh = 0.0
    for year_index in range(lifetime_years):
        yearly_generation = annual_generation_kwh * (degradation_factor ** year_index)
        lifetime_generation_kwh += yearly_generation

    lifetime_avoided_kg = lifetime_generation_kwh * carbon_factor

    inverter_lifetime = replacements_input.inverter_lifetime_years or 0
    if inverter_lifetime > 0:
        inverter_replacements = (lifetime_years - 1) // inverter_lifetime
    else:
        inverter_replacements = 0

    inverter_factor = replacements_input.inverter_embodied_kgCO2e_per_kwp or 0.0
    inverter_emissions_kg = inverter_replacements * inverter_factor * capacity_kwp

    additional_percent = replacements_input.additional_replacement_percent_of_embodied or 0.0
    additional_emissions_kg = embodied_carbon_kgCO2e * (additional_percent / 100.0)

    total_replacement_kg = inverter_emissions_kg + additional_emissions_kg

    return {
        "system_lifetime_years": lifetime_years,
        "module_degradation_rate_pct_per_year": replacements_input.module_degradation_rate_pct_per_year,
        "lifetime_generation_kwh": round(lifetime_generation_kwh, 1),
        "lifetime_avoided_kgCO2e": round(lifetime_avoided_kg, 1),
        "lifetime_avoided_tonnesCO2e": round(lifetime_avoided_kg / 1000.0, 3),
        "average_annual_generation_kwh": round(lifetime_generation_kwh / lifetime_years, 1),
        "inverter_lifetime_years": inverter_lifetime,
        "inverter_replacements": inverter_replacements,
        "inverter_emissions_kgCO2e": round(inverter_emissions_kg, 2),
        "additional_replacement_percent_of_embodied": additional_percent,
        "additional_replacement_emissions_kgCO2e": round(additional_emissions_kg, 2),
        "total_kgCO2e": round(total_replacement_kg, 2),
        "total_tonnesCO2e": round(total_replacement_kg / 1000.0, 3),
    }
