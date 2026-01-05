from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pandas as pd
from typing import Optional
from pvlib.iotools import get_pvgis_hourly
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SolarInput(BaseModel):
    postcode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    year: int
    capacity_mwp: float
    pr: float
    carbon_factor: float
    surface_tilt: int
    surface_azimuth: int

def get_coordinates(postcode: Optional[str], lat: Optional[float], lon: Optional[float]):
    if lat is not None and lon is not None:
        return lat, lon
    elif postcode:
        r = requests.get(f"https://api.postcodes.io/postcodes/{postcode}")
        data = r.json()
        if data["status"] == 200:
            return data["result"]["latitude"], data["result"]["longitude"]
        else:
            raise ValueError("Invalid postcode.")
    else:
        raise ValueError("Must provide either postcode or latitude/longitude.")

@app.post("/calculate")
def calculate(input: SolarInput):
    lat, lon = get_coordinates(input.postcode, input.latitude, input.longitude)

    data, _ = get_pvgis_hourly(
        latitude=lat,
        longitude=lon,
        start=input.year,
        end=input.year,
        raddatabase="PVGIS-SARAH3",
        components=True,
        surface_tilt=input.surface_tilt,
        surface_azimuth=input.surface_azimuth,
        outputformat="json",
    )

    # Pick irradiance
    if "G(h)" in data.columns:
        irr = data["G(h)"]
    else:
        data["poa_global"] = data[["poa_direct","poa_sky_diffuse","poa_ground_diffuse"]].sum(axis=1)
        irr = data["poa_global"]

    capacity_kw = input.capacity_mwp * 1000
    pv_kwh = (capacity_kw * (irr / 1000) * input.pr).clip(lower=0)

    annual_total_kwh = float(pv_kwh.sum())
    avoided_total_kg = annual_total_kwh * input.carbon_factor

    # Monthly aggregations
    monthly = pv_kwh.groupby(pv_kwh.index.month).sum()
    monthly_output = {int(month): float(val) for month, val in monthly.items()}

    return {
        "location": {"lat": lat, "lon": lon},
        "annual_kwh": round(annual_total_kwh, 1),
        "annual_avoided_kgCO2e": round(avoided_total_kg, 1),
        "monthly_kwh": monthly_output
    }