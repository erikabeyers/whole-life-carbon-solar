"""
Simplified materials emission factors (A1–A3)
--------------------------------------------

Purpose:
- Provide early-stage embodied carbon factors for PV systems
- Based on interpreted mean values from ICE Database (v4.1, Oct 2025)
- Not a reproduction of the ICE database
- Intended for feasibility / optioneering studies

IMPORTANT:
- Values in this file are populated manually by the user
- Users should replace with EPDs or licensed databases at later stages

Scope:
- PV-relevant materials only
- Units explicitly stated
"""

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
# Simplified PV material factors (USER TO POPULATE)
# =============================================================================

# NOTE:
# Populate the 'value' fields below using mean values interpreted from ICE.
# Do NOT copy tables wholesale – select one representative mean per material.

SIMPLIFIED_PV_MATERIAL_FACTORS = {

    # -------------------------------------------------------------------------
    # Aluminium (PV module frames, rails)
    # -------------------------------------------------------------------------
    "aluminium": MaterialEmissionFactor(
        material="Aluminium, General worldwide (PV module frames / rails)",
        value=13.1,  #(kgCO2e/kg)
        unit="kgCO2e/kg",
        source="ICE Database v4.1 (mean of aluminium profiles)",
        notes=(
            "Generic primary aluminium; recycled content can significantly "
            "reduce this value. Early-stage assumption."
        ),
    ),

    # -------------------------------------------------------------------------
    # Steel (mounting structures, piles, frames)
    # -------------------------------------------------------------------------
    "steel": MaterialEmissionFactor(
        material="Steel (PV mounting structures)",
        value=1.64,  #(kgCO2e/kg)
        unit="kgCO2e/kg",
        source="ICE Database v4.1 (mean structural steel)",
        notes=(
            "Generic hot-rolled engineering steel. "
            "EAF steel may be lower depending on source."
        ),
    ),

    # -------------------------------------------------------------------------
    # Concrete (foundations / ballast)
    # -------------------------------------------------------------------------
    "concrete": MaterialEmissionFactor(
        material="Concrete 32/40 MPa (PV foundations / ballast)",
        value=0.134,  # (kgCO2e/kg)
        unit="kgCO2e/kg",
        source="ICE Database v4.1 (mean ready-mix concrete)",
        notes=(
            "Highly mix-dependent. Foundations often dominate "
            "A1–A3 for ground-mounted systems."
        ),
    ),

    # -------------------------------------------------------------------------
    # Glass (PV module frontsheet)
    # -------------------------------------------------------------------------
    "glass": MaterialEmissionFactor(
        material="Glass (PV module frontsheet)",
        value=0.0,  # TODO: populate (kgCO2e/kg)
        unit="kgCO2e/kg",
        source="ICE Database v4.1 (mean flat glass)",
        notes="Flat glass typical of crystalline silicon PV modules.",
    ),

    # -------------------------------------------------------------------------
    # Silicon (PV cells) – OPTIONAL early-stage
    # -------------------------------------------------------------------------
    "silicon_pv": MaterialEmissionFactor(
        material="Silicon (PV cells)",
        value=0.0,  # TODO: populate (kgCO2e/kg)
        unit="kgCO2e/kg",
        source="ICE Database v4.1 / literature (mono-Si PV cells)",
        notes=(
            "Very energy-intensive material. Strongly dependent "
            "on manufacturing electricity mix."
        ),
    ),

    # -------------------------------------------------------------------------
    # Copper (cabling, electrical components) – OPTIONAL early-stage
    # -------------------------------------------------------------------------
    "copper": MaterialEmissionFactor(
        material="Copper (PV cabling and electrical components)",
        value=0.0,  # TODO: populate (kgCO2e/kg)
        unit="kgCO2e/kg",
        source="ICE Database v4.1 (mean copper)",
        notes="Often a small contributor but included for completeness.",
    ),
}


# =============================================================================
# Public API
# =============================================================================

def get_material_factor(
    material_key: str,
    *,
    override_value: Optional[float] = None,
    override_unit: Optional[str] = None,
    override_source: Optional[str] = None,
) -> MaterialEmissionFactor:
    """
    Return embodied carbon factor for a PV material.

    Parameters
    ----------
    material_key : str
        One of the keys in SIMPLIFIED_PV_MATERIAL_FACTORS
        (e.g. 'steel', 'aluminium').
    override_value : float, optional
        User-supplied emission factor value.
    override_unit : str, optional
        Unit for override value (default: kgCO2e/kg).
    override_source : str, optional
        Source for override value (e.g. specific EPD).

    Returns
    -------
    MaterialEmissionFactor
    """

    material_key = material_key.lower()

    # ------------------------------------------------------------------
    # User override (highest priority)
    # ------------------------------------------------------------------
    if override_value is not None:
        return MaterialEmissionFactor(
            material=material_key,
            value=float(override_value),
            unit=override_unit or "kgCO2e/kg",
            source=override_source or "User override",
            notes="User-supplied value overrides simplified ICE reference",
        )

    # ------------------------------------------------------------------
    # Default lookup
    # ------------------------------------------------------------------
    if material_key not in SIMPLIFIED_PV_MATERIAL_FACTORS:
        raise KeyError(
            f"Material '{material_key}' not defined in simplified PV material list."
        )

    factor = SIMPLIFIED_PV_MATERIAL_FACTORS[material_key]

    if factor.value == 0.0:
        raise ValueError(
            f"Material '{material_key}' has not yet been populated with a value."
        )

    return factor


# =============================================================================
# Smoke test
# =============================================================================

if __name__ == "__main__":
    print("=== Simplified PV material factors ===")

    for key in SIMPLIFIED_PV_MATERIAL_FACTORS:
        try:
            print(get_material_factor(key))
        except Exception as e:
            print(f"{key}: {e}")

