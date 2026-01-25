from fastapi import FastAPI
from pydantic import BaseModel
import requests
from typing import Optional, Dict, Any, List
from pvlib.iotools import get_pvgis_hourly
from fastapi.middleware.cors import CORSMiddleware

# Import your emissions factor helpers
from emissions_factors import get_grid_electricity_factor
from materials_loader_ice import get_material_factor
from transport_emissions_factors import TransportLeg, calculate_transport_emissions
from construction_emissions_factors import calculate_construction_simple, calculate_construction_detailed, EquipmentUsage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MaterialQuantities(BaseModel):
    """Material quantities for embodied carbon calculation (A1-A3)"""
    aluminium_kg: float = 0.0
    steel_kg: float = 0.0
    concrete_kg: float = 0.0
    glass_kg: float = 0.0
    silicon_pv_kg: float = 0.0
    copper_kg: float = 0.0


class TransportLegInput(BaseModel):
    """A single transport leg"""
    mode: str  # e.g., "truck_hgv", "ship_container"
    distance_km: float
    mass_tonnes: float

class ConstructionInput(BaseModel):
    """Construction & installation (A5) calculation method"""
    method: str = "simple"  # "simple"
    
    # Simple method
    percentage: Optional[float] = 5.0  # % of embodied carbon
    
    # Detailed method (optional)
    equipment_usage: Optional[List[Dict[str, Any]]] = None
    worker_transport_km: Optional[float] = None
    num_workers: Optional[int] = None
    num_days: Optional[int] = None
    grid_electricity_kwh: Optional[float] = None


class SolarInput(BaseModel):
    # Location inputs
    postcode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # PV/system inputs
    year: int
    area_m2: float 
    module_efficiency: float  # 0.0 to 1.0
    surface_tilt: int
    surface_azimuth: int

    # Material quantities (optional - A1-A3)
    materials: Optional[MaterialQuantities] = None
    
    # Transport legs (optional - A4)
    transport: Optional[List[TransportLegInput]] = None

    # Construction & installation (optional - A5)
    construction: Optional[ConstructionInput] = None

    # Emissions factor handling
    carbon_factor_override: Optional[float] = None  # kgCO2e/kWh
    country_code: str = "GBR"  # default for OWID lookup


def get_coordinates(postcode: Optional[str], lat: Optional[float], lon: Optional[float]):
    if lat is not None and lon is not None:
        return lat, lon
    elif postcode:
        r = requests.get(f"https://api.postcodes.io/postcodes/{postcode}", timeout=10)
        data = r.json()
        if data.get("status") == 200 and data.get("result"):
            return data["result"]["latitude"], data["result"]["longitude"]
        else:
            raise ValueError("Invalid postcode.")
    else:
        raise ValueError("Must provide either postcode or latitude/longitude.")


def calculate_embodied_carbon(materials: Optional[MaterialQuantities]) -> Dict[str, Any]:
    """
    Calculate embodied carbon (A1-A3) from material quantities.
    """
    if materials is None:
        return {
            "total_kgCO2e": 0.0,
            "total_tonnesCO2e": 0.0,
            "breakdown": {},
            "note": "No materials provided"
        }
    
    breakdown = {}
    total_kg = 0.0
    
    material_map = {
        "aluminium": materials.aluminium_kg,
        "steel": materials.steel_kg,
        "concrete": materials.concrete_kg,
        "glass": materials.glass_kg,
        "silicon_pv": materials.silicon_pv_kg,
        "copper": materials.copper_kg,
    }
    
    for material_key, quantity_kg in material_map.items():
        if quantity_kg > 0:
            try:
                factor = get_material_factor(material_key)
                emissions_kg = quantity_kg * factor.value
                total_kg += emissions_kg
                
                breakdown[material_key] = {
                    "quantity_kg": quantity_kg,
                    "factor_kgCO2e_per_kg": factor.value,
                    "emissions_kgCO2e": round(emissions_kg, 2),
                    "emissions_tonnesCO2e": round(emissions_kg / 1000.0, 3),
                    "source": factor.source,
                }
            except (KeyError, ValueError) as e:
                breakdown[material_key] = {
                    "quantity_kg": quantity_kg,
                    "error": str(e)
                }
    
    return {
        "total_kgCO2e": round(total_kg, 2),
        "total_tonnesCO2e": round(total_kg / 1000.0, 3),
        "breakdown": breakdown,
    }

def calculate_construction_emissions(
    construction_input: Optional[ConstructionInput],
    embodied_carbon_kgCO2e: float,
    grid_carbon_factor: Optional[float] = None,
) -> Dict[str, Any]:
    """Calculate construction emissions (A5)."""
    if construction_input is None:
        # Default: use simple method with 5%
        return calculate_construction_simple(embodied_carbon_kgCO2e, percentage=5.0)
    
    if construction_input.method == "simple":
        return calculate_construction_simple(
            embodied_carbon_kgCO2e,
            percentage=construction_input.percentage or 5.0,
        )
    
    elif construction_input.method == "detailed":
        equipment = []
        if construction_input.equipment_usage:
            for eq in construction_input.equipment_usage:
                equipment.append(EquipmentUsage(
                    equipment_type=eq.get("equipment_type", ""),
                    hours=eq.get("hours", 0.0),
                ))
        
        return calculate_construction_detailed(
            equipment_usage=equipment,
            worker_transport_km=construction_input.worker_transport_km,
            num_workers=construction_input.num_workers,
            num_days=construction_input.num_days,
            grid_electricity_kwh=construction_input.grid_electricity_kwh,
            grid_carbon_factor=grid_carbon_factor,
        )
    
    return {
        "total_kgCO2e": 0.0,
        "total_tonnesCO2e": 0.0,
        "note": "Invalid construction method",
    }

@app.post("/calculate")
def calculate(input: SolarInput) -> Dict[str, Any]:
    lat, lon = get_coordinates(input.postcode, input.latitude, input.longitude)

    # ---------------------------------------------------------------------
    # Emissions factor: auto-fetch from OWID
    # ---------------------------------------------------------------------
    ef = get_grid_electricity_factor(
        input.country_code,
        input.year,
        override_value=input.carbon_factor_override,
        override_source="User override (API request)" if input.carbon_factor_override is not None else None,
    )
    carbon_factor = ef.value  # kgCO2e/kWh

    # ---------------------------------------------------------------------
    # PVGIS hourly irradiance
    # ---------------------------------------------------------------------
    data, _, _ = get_pvgis_hourly(
        latitude=lat,
        longitude=lon,
        start=input.year,
        end=input.year,
        raddatabase="PVGIS-ERA5",
        components=True,
        surface_tilt=input.surface_tilt,
        surface_azimuth=input.surface_azimuth,
        outputformat="json",
    )

    # Pick irradiance
    if "G(h)" in data.columns:
        irr = data["G(h)"]
        irr_label = "G(h)"
    else:
        needed = {"poa_direct", "poa_sky_diffuse", "poa_ground_diffuse"}
        if not needed.issubset(set(data.columns)):
            raise KeyError("PVGIS output missing expected irradiance columns.")
        data["poa_global"] = data[["poa_direct", "poa_sky_diffuse", "poa_ground_diffuse"]].sum(axis=1)
        irr = data["poa_global"]
        irr_label = "poa_global"

    # ---------------------------------------------------------------------
    # PV generation (kWh) - Operational Carbon Savings
    # ---------------------------------------------------------------------
    irr_kw_m2 = irr / 1000.0
    pv_kwh = (input.area_m2 * irr_kw_m2 * input.module_efficiency).clip(lower=0)

    capacity_kwp = input.area_m2 * input.module_efficiency

    annual_total_kwh = float(pv_kwh.sum())
    avoided_total_kg = annual_total_kwh * carbon_factor
    avoided_total_tonnes = avoided_total_kg / 1000.0

    monthly = pv_kwh.groupby(pv_kwh.index.month).sum()
    monthly_output = {int(month): float(val) for month, val in monthly.items()}

    # ---------------------------------------------------------------------
    # Embodied Carbon (A1-A3)
    # ---------------------------------------------------------------------
    embodied_carbon = calculate_embodied_carbon(input.materials)

    # ---------------------------------------------------------------------
    # Transport Emissions (A4)
    # ---------------------------------------------------------------------
    if input.transport and len(input.transport) > 0:
        # Convert TransportLegInput to TransportLeg
        transport_legs = [
            TransportLeg(
                mode=leg.mode,
                distance_km=leg.distance_km,
                mass_tonnes=leg.mass_tonnes,
            )
            for leg in input.transport
        ]
        transport_emissions = calculate_transport_emissions(transport_legs)
    else:
        transport_emissions = {
            "total_kgCO2e": 0.0,
            "total_tonnesCO2e": 0.0,
            "breakdown": [],
            "note": "No transport legs provided"
        }
    
    # ---------------------------------------------------------------------
    # Construction Emissions (A5)
    # ---------------------------------------------------------------------
    
    construction_emissions = calculate_construction_emissions(
    input.construction,
    embodied_carbon["total_kgCO2e"],
    carbon_factor,
    )
    
    # ---------------------------------------------------------------------
    # Response
    # ---------------------------------------------------------------------
    return {
        "location": {"lat": lat, "lon": lon},
        
        # Operational carbon (B6)
        "operational": {
            "annual_generation_kwh": round(annual_total_kwh, 1),
            "annual_avoided_kgCO2e": round(avoided_total_kg, 1),
            "annual_avoided_tonnesCO2e": round(avoided_total_tonnes, 3),
            "monthly_kwh": monthly_output,
        },
        
        # Embodied carbon (A1-A3)
        "embodied": embodied_carbon,
        
        # Transport (A4)
        "transport": transport_emissions,
        
        #Construction (A5)
        "construction": construction_emissions,
        
        # Legacy top-level keys for backward compatibility
        "annual_kwh": round(annual_total_kwh, 1),
        "annual_avoided_kgCO2e": round(avoided_total_kg, 1),
        "annual_avoided_tonnesCO2e": round(avoided_total_tonnes, 3),
        "equivalent_capacity_kwp": round(capacity_kwp, 3),
        "monthly_kwh": monthly_output,

        # Assumptions
        "assumptions": {
            "area_m2": input.area_m2,
            "module_efficiency": input.module_efficiency,
            "equivalent_capacity_kwp": round(capacity_kwp, 3),
            "carbon_factor_kgCO2e_per_kwh": carbon_factor,
            "carbon_factor_source": ef.source,
            "carbon_factor_year": ef.year,
            "carbon_factor_region": ef.region,
            "irradiance_column_used": irr_label,
        },
    }
