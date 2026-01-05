"""
Emission factors module
-----------------------
Design goals:
- Use permissively licensed, publicly available historical data by default
- Keep sources transparent and cited
- Allow user override when data is missing or disputed
- Keep units explicit (kgCO2e per unit)

Current scope:
- Electricity grid emission factors (kgCO2e/kWh)
- Country-level, annual resolution

Default data source:
- Our World in Data (OWID)
  https://github.com/owid/energy-data
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from typing import Optional


# =============================================================================
# Data structure
# =============================================================================

@dataclass
class EmissionFactor:
    value: float
    unit: str
    source: str
    year: int
    region: str
    notes: Optional[str] = None


# =============================================================================
# OWID data (single stable CSV)
# =============================================================================

_OWID_ENERGY_CSV = (
    "https://raw.githubusercontent.com/owid/energy-data/master/"
    "owid-energy-data.csv"
)

_owid_cache: Optional[pd.DataFrame] = None


def _load_owid_data() -> pd.DataFrame:
    """
    Load and cache OWID energy data.

    Required columns:
    - country
    - iso_code
    - year
    - carbon_intensity_elec (gCO2/kWh)
    """
    global _owid_cache

    if _owid_cache is None:
        df = pd.read_csv(_OWID_ENERGY_CSV)

        required = {
            "country",
            "iso_code",
            "year",
            "carbon_intensity_elec",
        }

        missing = required - set(df.columns)
        if missing:
            raise KeyError(f"Missing expected OWID columns: {missing}")

        # Keep only what we need
        df = df[list(required)]

        # Drop rows without carbon intensity
        df = df.dropna(subset=["carbon_intensity_elec"])

        # Convert gCO2/kWh → kgCO2/kWh
        df["kgco2_per_kwh"] = df["carbon_intensity_elec"] / 1000.0

        _owid_cache = df

    return _owid_cache


# =============================================================================
# Public API
# =============================================================================

def get_grid_electricity_factor(
    country: str,
    year: int,
    *,
    override_value: Optional[float] = None,
    override_source: Optional[str] = None,
) -> EmissionFactor:
    """
    Return grid electricity emission factor (kgCO2e/kWh).

    Parameters
    ----------
    country : str
        Country name or ISO3 code (e.g. 'United Kingdom' or 'GBR')
    year : int
        Year of factor
    override_value : float, optional
        User-supplied factor (kgCO2e/kWh)
    override_source : str, optional
        Source description for override value

    Returns
    -------
    EmissionFactor
    """

    # ------------------------------------------------------------------
    # User override (highest priority)
    # ------------------------------------------------------------------
    if override_value is not None:
        return EmissionFactor(
            value=float(override_value),
            unit="kgCO2e/kWh",
            source=override_source or "User override",
            year=year,
            region=country,
            notes="User-supplied value overrides database",
        )

    # ------------------------------------------------------------------
    # OWID lookup
    # ------------------------------------------------------------------
    df = _load_owid_data()

    mask = (
        ((df["country"] == country) | (df["iso_code"] == country))
        & (df["year"] == year)
    )

    subset = df.loc[mask]

    if subset.empty:
        raise ValueError(
            f"No electricity emission factor found for {country} in {year}. "
            "Provide override_value if you wish to proceed."
        )

    value = float(subset.iloc[0]["kgco2_per_kwh"])

    return EmissionFactor(
        value=value,
        unit="kgCO2e/kWh",
        source="Our World in Data – electricity carbon intensity",
        year=year,
        region=country,
        notes="Annual average grid electricity carbon intensity",
    )


# =============================================================================
# Smoke test
# =============================================================================

if __name__ == "__main__":
    print("=== OWID lookup ===")
    ef = get_grid_electricity_factor("GBR", 2023)
    print(ef)

    print("\n=== Override example (licensed/manual) ===")
    ef_override = get_grid_electricity_factor(
        "GBR",
        2023,
        override_value=0.233,
        override_source="CaDI (Carbon Footprint Ltd, 2025)",
    )
    print(ef_override)
