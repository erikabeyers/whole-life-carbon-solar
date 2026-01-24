"""
Transport emission factors (A4)
--------------------------------
Scope: Emissions from transporting materials to site

Units: kgCO2e per tonne-km (tkm)
- 1 tkm = transporting 1 tonne of material over 1 km

Data sources:
- UK Government GHG Conversion Factors (BEIS/DESNZ)
- DEFRA guidelines
- ICE Database v4.1

Design:
- Default factors based on typical UK/EU transport
- User can override with project-specific data
- Supports multiple transport modes and legs
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class TransportEmissionFactor:
    """Emission factor for a transport mode."""
    mode: str
    value: float  # kgCO2e per tonne-km
    unit: str
    source: str
    notes: Optional[str] = None


@dataclass
class TransportLeg:
    """A single leg of a transport journey."""
    mode: str  # e.g., "truck", "ship", "rail"
    distance_km: float
    mass_tonnes: float


# =============================================================================
# Default transport emission factors (kgCO2e per tonne-km)
# =============================================================================

TRANSPORT_EMISSION_FACTORS = {
    # Road freight
    "truck_hgv": TransportEmissionFactor(
        mode="Heavy Goods Vehicle (HGV) - Average",
        value=0.11072,  # kgCO2e/tkm
        unit="kgCO2e/tkm",
        source="UK Government GHG Conversion Factors 2024 (DESNZ)",
        notes="Average laden HGV (all diesel). Typical for UK/EU road freight.",
    ),
    
    "truck_rigid": TransportEmissionFactor(
        mode="Rigid HGV (average)",
        value=0.26587,  # kgCO2e/tkm
        unit="kgCO2e/tkm",
        source="UK Government GHG Conversion Factors 2024 (DESNZ)",
        notes="Rigid trucks, average weight class.",
    ),
    
    "truck_articulated": TransportEmissionFactor(
        mode="Articulated HGV (average)",
        value=0.06294,  # kgCO2e/tkm
        unit="kgCO2e/tkm",
        source="UK Government GHG Conversion Factors 2024 (DESNZ)",
        notes="Articulated trucks, more efficient for long-haul.",
    ),
    
    # Sea freight
    "ship_container": TransportEmissionFactor(
        mode="Container ship",
        value=0.00631,  # kgCO2e/tkm
        unit="kgCO2e/tkm",
        source="UK Government GHG Conversion Factors 2024 (DESNZ)",
        notes="Large container ship. Very efficient per tkm.",
    ),
    
    "ship_bulk": TransportEmissionFactor(
        mode="Bulk carrier",
        value=0.00494,  # kgCO2e/tkm
        unit="kgCO2e/tkm",
        source="UK Government GHG Conversion Factors 2024 (DESNZ)",
        notes="Bulk cargo ships (e.g., steel, materials).",
    ),
    
    # Rail freight
    "rail_freight": TransportEmissionFactor(
        mode="Rail freight",
        value=0.02678,  # kgCO2e/tkm
        unit="kgCO2e/tkm",
        source="UK Government GHG Conversion Factors 2024 (DESNZ)",
        notes="UK rail freight average.",
    ),
    
    # Air freight (rarely used for PV but included for completeness)
    "air_freight": TransportEmissionFactor(
        mode="Air freight",
        value=1.13,  # kgCO2e/tkm
        unit="kgCO2e/tkm",
        source="UK Government GHG Conversion Factors 2024 (DESNZ)",
        notes="Very high emissions. Avoid for bulk materials.",
    ),
}


# =============================================================================
# Public API
# =============================================================================

def get_transport_factor(
    mode: str,
    *,
    override_value: Optional[float] = None,
    override_source: Optional[str] = None,
) -> TransportEmissionFactor:
    """
    Get emission factor for a transport mode.
    
    Parameters
    ----------
    mode : str
        Transport mode key (e.g., 'truck_hgv', 'ship_container')
    override_value : float, optional
        User-supplied factor (kgCO2e/tkm)
    override_source : str, optional
        Source description for override
        
    Returns
    -------
    TransportEmissionFactor
    """
    
    # User override
    if override_value is not None:
        return TransportEmissionFactor(
            mode=mode,
            value=float(override_value),
            unit="kgCO2e/tkm",
            source=override_source or "User override",
            notes="User-supplied transport emission factor",
        )
    
    # Default lookup
    mode_key = mode.lower().replace(" ", "_")
    
    if mode_key not in TRANSPORT_EMISSION_FACTORS:
        available = ", ".join(TRANSPORT_EMISSION_FACTORS.keys())
        raise KeyError(
            f"Transport mode '{mode}' not found. "
            f"Available modes: {available}"
        )
    
    return TRANSPORT_EMISSION_FACTORS[mode_key]


def calculate_transport_emissions(
    legs: List[TransportLeg],
    *,
    custom_factors: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Calculate total transport emissions (A4) from multiple transport legs.
    
    Parameters
    ----------
    legs : List[TransportLeg]
        List of transport legs (mode, distance, mass)
    custom_factors : dict, optional
        Custom emission factors by mode {mode: kgCO2e/tkm}
        
    Returns
    -------
    dict
        Total emissions and breakdown by leg
        
    Example
    -------
    >>> legs = [
    ...     TransportLeg(mode="ship_container", distance_km=8000, mass_tonnes=50),
    ...     TransportLeg(mode="truck_hgv", distance_km=200, mass_tonnes=50),
    ... ]
    >>> result = calculate_transport_emissions(legs)
    >>> print(result['total_kgCO2e'])
    """
    
    total_kgco2e = 0.0
    breakdown = []
    
    for i, leg in enumerate(legs):
        # Get emission factor
        override_val = custom_factors.get(leg.mode) if custom_factors else None
        
        try:
            factor = get_transport_factor(
                leg.mode,
                override_value=override_val,
            )
        except KeyError as e:
            breakdown.append({
                "leg": i + 1,
                "mode": leg.mode,
                "error": str(e),
            })
            continue
        
        # Calculate emissions for this leg
        # Emissions = mass (tonnes) × distance (km) × factor (kgCO2e/tkm)
        tonne_km = leg.mass_tonnes * leg.distance_km
        emissions_kg = tonne_km * factor.value
        
        total_kgco2e += emissions_kg
        
        breakdown.append({
            "leg": i + 1,
            "mode": factor.mode,
            "mass_tonnes": leg.mass_tonnes,
            "distance_km": leg.distance_km,
            "tonne_km": round(tonne_km, 2),
            "factor_kgCO2e_per_tkm": factor.value,
            "emissions_kgCO2e": round(emissions_kg, 2),
            "source": factor.source,
        })
    
    return {
        "total_kgCO2e": round(total_kgco2e, 2),
        "total_tonnesCO2e": round(total_kgco2e / 1000.0, 3),
        "breakdown": breakdown,
    }


# =============================================================================
# Smoke test
# =============================================================================

if __name__ == "__main__":
    print("=== Transport emission factors ===\n")
    
    # Show available modes
    for key, factor in TRANSPORT_EMISSION_FACTORS.items():
        print(f"{key}: {factor.value} {factor.unit}")
    
    print("\n=== Example calculation ===")
    
    # Example: 50 tonnes of PV equipment
    # Shipped from China (8000 km) then trucked locally (200 km)
    legs = [
        TransportLeg(mode="ship_container", distance_km=8000, mass_tonnes=50),
        TransportLeg(mode="truck_hgv", distance_km=200, mass_tonnes=50),
    ]
    
    result = calculate_transport_emissions(legs)
    
    print(f"\nTotal transport emissions: {result['total_kgCO2e']} kgCO2e")
    print("\nBreakdown:")
    for leg in result['breakdown']:
        print(f"  Leg {leg['leg']}: {leg['mode']}")
        print(f"    {leg['mass_tonnes']} tonnes × {leg['distance_km']} km = {leg['tonne_km']} tkm")
        print(f"    {leg['tonne_km']} tkm × {leg['factor_kgCO2e_per_tkm']} kgCO2e/tkm = {leg['emissions_kgCO2e']} kgCO2e")
