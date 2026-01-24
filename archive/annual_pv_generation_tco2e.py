# pv_model.py
import numpy as np
import matplotlib.pyplot as plt
from pvlib.iotools import get_pvgis_hourly

# User-defined parameters

LAT = 55.9 # Edinburgh
LON = -3.2  # Edinburgh
YEAR = 2023     # Year for analysis

CAPACITY_MWP = 1       # MWp (DC)
PR = 0.75                # Performance ratio (0.75–0.85 typical)
CARBON_FACTOR = 0.233  # kgCO2e per kWh grid electricity (UK average 2023)

SURFACE_TILT = 30          # degrees
SURFACE_AZIMUTH = 180     # degrees (180 = south-facing in N hemisphere)


def pvgis_irradiance_to_pv_kwh(irradiance_wh_m2, capacity_mwp, performance_ratio):
    capacity_kw = capacity_mwp * 1000.0
    pv_kwh = capacity_kw * (irradiance_wh_m2 / 1000.0) * performance_ratio
    return pv_kwh.clip(lower=0)

def pv_kwh_to_tco2e(pv_kwh, carbon_factor_kg_per_kwh):
    # emissions avoided (or attributed), in tCO2e
    return (pv_kwh * carbon_factor_kg_per_kwh / 1000.0).clip(lower=0)


if __name__ == "__main__":
    # --- Get hourly data from PVGIS ---
    data, meta = get_pvgis_hourly(
        latitude=LAT,
        longitude=LON,
        start=YEAR,
        end=YEAR,
        raddatabase="PVGIS-SARAH3",
        components=True,
        surface_tilt=SURFACE_TILT,
        surface_azimuth=SURFACE_AZIMUTH,
        outputformat="json",
    )

    print(data.head())
    print("Columns:", list(data.columns))

    # --- Choose irradiance column ---
    # For many PVGIS hourly responses:
    #   "G(h)" = Global Horizontal Irradiance (Wh/m² per hour)
    if "G(h)" in data.columns:
        irradiance = data["G(h)"]
        irradiance_label = "GHI (Wh/m² per hour)"
    elif all(c in data.columns for c in ["poa_direct", "poa_sky_diffuse", "poa_ground_diffuse"]):
        data["poa_global"] = (data["poa_direct"] + data["poa_sky_diffuse"] + data["poa_ground_diffuse"])
        irradiance = data["poa_global"]
        irradiance_label = "POA global (Wh/m² per hour)"
    else:
        raise KeyError("Couldn't find a usable irradiance column (expected 'G(h)' or POA components).")

    # --- Convert irradiance -> PV kWh/hour ---
    pv_kwh = pvgis_irradiance_to_pv_kwh(irradiance, CAPACITY_MWP, PR)

    # --- Convert PV kWh -> avoided emissions (tCO2e) ---
    pv_tco2e = pv_kwh_to_tco2e(pv_kwh, CARBON_FACTOR)

    capacity_kw = CAPACITY_MWP * 1000.0
    pv_kwh = (capacity_kw * (irradiance / 1000.0) * PR).clip(lower=0)
    annual_kwh = float(pv_kwh.sum())
    print(f"Annual PV generation: {annual_kwh:,.0f} kWh")

    annual_tco2e = float(pv_tco2e.sum())
    annual_kgco2e = annual_tco2e * 1000.0
    print(f"\nAnnual emissions avoided: {annual_tco2e:,.1f} tCO2e ({annual_kgco2e:,.0f} kgCO2e)")

    # --- Plot PV kWh across the year ---
    plt.figure()
    plt.plot(pv_tco2e.index, pv_tco2e.values)
    plt.title(f"Hourly PV Emissions Avoided (tco2e) — {CAPACITY_MWP} MWp, PR={PR}, {YEAR}")
    plt.xlabel("Date")
    plt.ylabel("PV emissions saved (tco2e)")
    plt.tight_layout()
    plt.savefig("pv_hourly_generation.png", dpi=200)
    print("Saved plot to pv_hourly_generation.png")
    plt.show() 

print()
