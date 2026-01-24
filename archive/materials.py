"""
Materials emission factors module (A1–A3)
---------------------------------------
Purpose:
- Provide embodied carbon factors for common PV system materials
- Use public, transparent default sources
- Allow user override where better project-specific or EPD data exists

Design principles:
- Explicit units (kgCO2e per kg, per m2, or per unit)
- Clear source attribution
- Conservative, first-pass defaults suitable for early-stage studies

This module pairs with:
- emissions_factors.py (electricity)
- Future modules for transport (A4), installation (A5), replacements (B), EOL (C)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# =============================================================================
# Data structure
# =============================================================================

@dataclass
class MaterialEmissionFactor:
    material: str
    value: float
    unit: str
    source: str
    notes: Optional[str] = None


# =============================================================================
# Default material emission factors (PUBLIC, GENERIC)
# =============================================================================

# NOTE:
# These are order-of-magnitude, industry-typical values suitable for
# early-stage embodied carbon modelling.
# Users SHOULD override with EPDs where available.

_DEFAULT_MATERIAL_FACTORS = {
    "aluminium": MaterialEmissionFactor(
        material="aluminium",
        value=9.5,  # kgCO2e per kg
        unit="kgCO2e/kg",
        source="ICE Database v3 / literature average",
        notes="Primary aluminium; recycled content can reduce this significantly",
    ),
    "steel": MaterialEmissionFactor(
        material="steel",
        value=1.7,  # kgCO2e per kg
        unit="kgCO2e/kg",
        source="ICE Database v3 / World Steel averages",
        notes="Hot-rolled structural steel; EAF steel may be lower",
    ),
    "glass": MaterialEmissionFactor(
        material="glass",
        value=1.0,  # kgCO2e per kg
        unit="kgCO2e/kg",
        source="ICE Database v3 / EPD averages",
        notes="Flat glass typical of PV modules",
    ),
    "silicon_pv": MaterialEmissionFactor(
        material="silicon_pv",
        value=45.0,  # kgCO2e per kg (very energy intensive)
        unit="kgCO2e/kg",
        source="Literature (mono-Si PV cell manufacturing)",
        notes="Highly sensitive to manufacturing electricity mix",
    ),
    "copper": MaterialEmissionFactor(
        material="copper",
        value=4.0,  # kgCO2e per kg
        unit="kgCO2e/kg",
        source="ICE Database v3 / ecoinvent literature",
        notes="Cabling and electrical components",
    ),
    "concrete": MaterialEmissionFactor(
        material="concrete",
        value=0.13,  # kgCO2e per kg (~130 kgCO2e/m3 at 2400 kg/m3)
        unit="kgCO2e/kg",
        source="ICE Database v3 / UK generic concrete",
        notes="Highly mix-dependent; foundations dominate ground-mount systems",
    ),
}


# =============================================================================
# Public API
# =============================================================================


def get_material_emission_factor(
    material: str,
    *,
    override_value: Optional[float] = None,
    override_unit: Optional[str] = None,
    override_source: Optional[str] = None,
) -> MaterialEmissionFactor:
    """
    Return embodied carbon factor for a material.

    Parameters
    ----------
    material : str
        Material key (e.g. 'steel', 'aluminium', 'glass').
    override_value : float, optional
        User-supplied emission factor value.
    override_unit : str, optional
        Unit for override value (e.g. 'kgCO2e/kg').
    override_source : str, optional
        Source for override value (e.g. specific EPD).

    Returns
    -------
    MaterialEmissionFactor
    """

    material = material.lower()

    # ------------------------------------------------------------------
    # User override
    # ------------------------------------------------------------------
    if override_value is not None:
        return MaterialEmissionFactor(
            material=material,
            value=float(override_value),
            unit=override_unit or "kgCO2e/kg",
            source=override_source or "User override",
            notes="User-supplied value overrides default database",
        )

    # Default lookup
    if material not in _DEFAULT_MATERIAL_FACTORS:
        raise KeyError(
            f"No default emission factor for material '{material}'. "
            "Provide override_value to proceed."
        )

    return _DEFAULT_MATERIAL_FACTORS[material]


# =============================================================================
# Smoke test
# =============================================================================

if __name__ == "__main__":
    print("=== Default material factors ===")
    for m in _DEFAULT_MATERIAL_FACTORS:
        print(get_material_emission_factor(m))

    print("\n=== Override example (EPD) ===")
    aluminium_epd = get_material_emission_factor(
        "aluminium",
        override_value=4.2,
        override_source="Manufacturer EPD (70% recycled content)",
    )
    print(aluminium_epd)
