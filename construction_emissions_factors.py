"""
Construction & Installation emission factors (A5)
--------------------------------------------------
Scope: Emissions from on-site construction activities

Typical A5 activities for solar PV:
- Site preparation (earthworks, leveling)
- Foundation installation (excavation, concrete pouring)
- Module mounting and racking installation
- Electrical installation (cabling, inverters, transformers)
- Equipment usage (cranes, forklifts, diesel generators)
- Worker transportation to site
- Construction waste

Data sources:
- UK Government GHG Conversion Factors 2024 (BEIS/DESNZ)
  For: Diesel, petrol, grid electricity emission factors
  For: Average car emissions (worker transport)
  Source: https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024

- Construction industry benchmarks
  For: Typical equipment fuel consumption rates
  Source: Construction Equipment Guide, industry standards

- Simple method percentage (3-7% of A1-A3)
  Source: Industry benchmarks for solar PV construction
  Based on typical ratios for similar infrastructure projects

Design:
- Simple method: percentage of embodied carbon (typical: 3-7% of A1-A3)
- Detailed method: itemized equipment usage, fuel consumption, worker transport
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class ConstructionActivity:
    """A single construction activity with emissions."""
    activity: str
    emissions_kgCO2e: float
    description: str
    source: str


# =============================================================================
# Fuel emission factors
# Source: UK Government GHG Conversion Factors 2024
# =============================================================================

FUEL_EMISSION_FACTORS = {
    "diesel": {
        "value": 2.69,  # kgCO2e per liter
        "unit": "kgCO2e/L",
        "source": "UK Government GHG Conversion Factors 2024",
        "notes": "Average diesel (100% mineral diesel)"
    },
    "petrol": {
        "value": 2.32,  # kgCO2e per liter
        "unit": "kgCO2e/L",
        "source": "UK Government GHG Conversion Factors 2024",
        "notes": "Average petrol (100% mineral petrol)"
    },
    "grid_electricity": {
        "value": 0.234,  # kgCO2e per kWh (UK 2023 average)
        "unit": "kgCO2e/kWh",
        "source": "UK Government GHG Conversion Factors 2024",
        "notes": "UK electricity grid average. Use actual grid factor if available from country-specific data."
    },
}


# =============================================================================
# Equipment fuel consumption rates
# Source: Construction Equipment Guide, industry averages
# =============================================================================

EQUIPMENT_FUEL_RATES = {
    "mobile_crane_medium": {
        "fuel_type": "diesel",
        "consumption_l_per_hour": 15.0,
        "description": "Medium mobile crane (20-50 tonne capacity)",
        "source": "Construction Equipment Guide - typical medium crane consumption"
    },
    "mobile_crane_large": {
        "fuel_type": "diesel",
        "consumption_l_per_hour": 25.0,
        "description": "Large mobile crane (50+ tonne capacity)",
        "source": "Construction Equipment Guide - typical large crane consumption"
    },
    "excavator_medium": {
        "fuel_type": "diesel",
        "consumption_l_per_hour": 12.0,
        "description": "Medium excavator (10-20 tonne)",
        "source": "Construction Equipment Guide - typical excavator consumption"
    },
    "forklift_diesel": {
        "fuel_type": "diesel",
        "consumption_l_per_hour": 3.5,
        "description": "Diesel forklift (2-5 tonne capacity)",
        "source": "Construction Equipment Guide - typical forklift consumption"
    },
    "telehandler": {
        "fuel_type": "diesel",
        "consumption_l_per_hour": 8.0,
        "description": "Telescopic handler",
        "source": "Construction Equipment Guide - typical telehandler consumption"
    },
    "generator_small": {
        "fuel_type": "diesel",
        "consumption_l_per_hour": 2.5,
        "description": "Small diesel generator (20-50 kVA)",
        "source": "Generator manufacturer specifications - typical small unit"
    },
    "generator_medium": {
        "fuel_type": "diesel",
        "consumption_l_per_hour": 5.0,
        "description": "Medium diesel generator (50-150 kVA)",
        "source": "Generator manufacturer specifications - typical medium unit"
    },
}


# Worker transport emission factor
# Source: UK Government GHG Conversion Factors 2024
WORKER_CAR_EMISSION_FACTOR = {
    "value": 0.17058,  # kgCO2e per km
    "unit": "kgCO2e/km",
    "source": "UK Government GHG Conversion Factors 2024",
    "notes": "Average car (medium, unknown fuel type)"
}


# =============================================================================
# Public API - Simple Method
# =============================================================================

def calculate_construction_simple(
    embodied_carbon_kgCO2e: float,
    percentage: float = 5.0,
) -> Dict[str, Any]:
    """
    Simple method: Calculate A5 as percentage of A1-A3 embodied carbon.
    
    Typical range: 3-7% for solar PV installations.
    Use 5% as default conservative estimate.
    
    Source: Industry benchmarks for solar PV construction emissions
    
    Parameters
    ----------
    embodied_carbon_kgCO2e : float
        Total embodied carbon from materials (A1-A3) in kgCO2e
    percentage : float, optional
        Percentage of embodied carbon (default: 5.0%)
        
    Returns
    -------
    dict
        Construction emissions breakdown
        
    Example
    -------
    >>> # If A1-A3 = 10,000 kgCO2e
    >>> result = calculate_construction_simple(10000, percentage=5.0)
    >>> print(result['total_kgCO2e'])  # 500 kgCO2e
    """
    
    construction_emissions = embodied_carbon_kgCO2e * (percentage / 100.0)
    
    return {
        "method": "simple_percentage",
        "total_kgCO2e": round(construction_emissions, 2),
        "total_tonnesCO2e": round(construction_emissions / 1000.0, 3),
        "assumptions": {
            "embodied_carbon_kgCO2e": embodied_carbon_kgCO2e,
            "percentage_used": percentage,
            "note": f"A5 estimated as {percentage}% of A1-A3 embodied carbon",
            "source": "Industry benchmark (3-7% typical for solar PV construction)",
        },
    }


# =============================================================================
# Public API - Detailed Method
# =============================================================================

class EquipmentUsage:
    """Equipment usage for detailed A5 calculation."""
    def __init__(self, equipment_type: str, hours: float):
        self.equipment_type = equipment_type
        self.hours = hours


def calculate_construction_detailed(
    equipment_usage: List[EquipmentUsage],
    worker_transport_km: Optional[float] = None,
    num_workers: Optional[int] = None,
    num_days: Optional[int] = None,
    grid_electricity_kwh: Optional[float] = None,
    grid_carbon_factor: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Detailed method: Calculate A5 from itemized equipment and activities.
    
    All emission factors sourced from UK Government GHG Conversion Factors 2024.
    
    Parameters
    ----------
    equipment_usage : List[EquipmentUsage]
        List of equipment types and hours used
    worker_transport_km : float, optional
        Average daily round-trip distance per worker (km)
    num_workers : int, optional
        Number of workers on site
    num_days : int, optional
        Number of working days
    grid_electricity_kwh : float, optional
        Grid electricity used on site (kWh)
    grid_carbon_factor : float, optional
        Grid carbon factor (kgCO2e/kWh), defaults to UK average
        
    Returns
    -------
    dict
        Detailed construction emissions breakdown with sources
    """
    
    activities = []
    total_emissions = 0.0
    
    # 1. Equipment fuel consumption
    for usage in equipment_usage:
        if usage.equipment_type not in EQUIPMENT_FUEL_RATES:
            continue
            
        equip = EQUIPMENT_FUEL_RATES[usage.equipment_type]
        fuel_consumed_l = equip["consumption_l_per_hour"] * usage.hours
        fuel_factor = FUEL_EMISSION_FACTORS[equip["fuel_type"]]["value"]
        emissions = fuel_consumed_l * fuel_factor
        
        total_emissions += emissions
        
        activities.append(ConstructionActivity(
            activity=f"{equip['description']} ({usage.hours}h)",
            emissions_kgCO2e=round(emissions, 2),
            description=f"{fuel_consumed_l:.1f}L {equip['fuel_type']} consumed",
            source=f"{FUEL_EMISSION_FACTORS[equip['fuel_type']]['source']} (fuel) + {equip['source']} (consumption rate)",
        ))
    
    # 2. Worker transportation
    if worker_transport_km and num_workers and num_days:
        car_factor = WORKER_CAR_EMISSION_FACTOR["value"]
        total_worker_km = worker_transport_km * num_workers * num_days
        worker_emissions = total_worker_km * car_factor
        
        total_emissions += worker_emissions
        
        activities.append(ConstructionActivity(
            activity=f"Worker transport ({num_workers} workers, {num_days} days)",
            emissions_kgCO2e=round(worker_emissions, 2),
            description=f"{total_worker_km:.0f} km total travel @ {car_factor} kgCO2e/km",
            source=WORKER_CAR_EMISSION_FACTOR["source"],
        ))
    
    # 3. Grid electricity on site
    if grid_electricity_kwh:
        grid_factor = grid_carbon_factor or FUEL_EMISSION_FACTORS["grid_electricity"]["value"]
        elec_emissions = grid_electricity_kwh * grid_factor
        
        total_emissions += elec_emissions
        
        activities.append(ConstructionActivity(
            activity=f"Grid electricity on site",
            emissions_kgCO2e=round(elec_emissions, 2),
            description=f"{grid_electricity_kwh:.1f} kWh @ {grid_factor} kgCO2e/kWh",
            source=FUEL_EMISSION_FACTORS["grid_electricity"]["source"],
        ))
    
    return {
        "method": "detailed_itemized",
        "total_kgCO2e": round(total_emissions, 2),
        "total_tonnesCO2e": round(total_emissions / 1000.0, 3),
        "breakdown": [
            {
                "activity": act.activity,
                "emissions_kgCO2e": act.emissions_kgCO2e,
                "description": act.description,
                "source": act.source,
            }
            for act in activities
        ],
        "data_sources": {
            "fuel_factors": "UK Government GHG Conversion Factors 2024",
            "equipment_consumption": "Construction Equipment Guide, industry standards",
            "worker_transport": "UK Government GHG Conversion Factors 2024 (average car)",
        }
    }


# =============================================================================
# Smoke test
# =============================================================================

if __name__ == "__main__":
    print("=== Construction A5 - Simple Method ===")
    print("Source: Industry benchmark (3-7% typical for solar PV)")
    print()
    
    # Example: 10 tonnes (10,000 kg) embodied carbon from materials
    result_simple = calculate_construction_simple(10000, percentage=5.0)
    print(f"A1-A3 Embodied: 10,000 kgCO2e")
    print(f"A5 Construction (5%): {result_simple['total_kgCO2e']} kgCO2e")
    print()
    
    print("=== Construction A5 - Detailed Method ===")
    print("Sources: UK Government GHG Conversion Factors 2024 + Construction Equipment Guide")
    print()
    
    # Example: Medium-scale ground mount installation
    equipment = [
        EquipmentUsage("mobile_crane_medium", hours=16),  # 2 days of crane work
        EquipmentUsage("excavator_medium", hours=24),     # 3 days of excavation
        EquipmentUsage("forklift_diesel", hours=40),      # 5 days of material handling
        EquipmentUsage("generator_small", hours=80),      # Generator running 10 days
    ]
    
    result_detailed = calculate_construction_detailed(
        equipment_usage=equipment,
        worker_transport_km=50,  # 50km round trip
        num_workers=10,
        num_days=15,
        grid_electricity_kwh=200,  # Some grid power for tools
    )
    
    print(f"Total A5: {result_detailed['total_kgCO2e']} kgCO2e")
    print("\nBreakdown:")
    for item in result_detailed['breakdown']:
        print(f"  - {item['activity']}: {item['emissions_kgCO2e']} kgCO2e")
        print(f"    {item['description']}")
        print(f"    Source: {item['source']}")
        print()
