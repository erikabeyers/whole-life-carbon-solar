Whole Life Carbon Calculator for Solar PV

Live tool: https://erikabeyers.github.io/whole-life-carbon-solar/

What is this?
A web tool for estimating the carbon footprint of solar PV installations. It calculates both the embodied carbon (from manufacturing and transport) and the operational carbon savings (from displacing grid electricity).
This is designed for high-level project assessments - not for regulatory compliance.

How to use it
 - Pick a location on the map (or search for one)
 - Enter your system details (array size, efficiency, tilt, azimuth)
 - Optionally add material quantities and transport details
 - Hit calculate :)

The tool will show you:

 - Monthly and annual PV generation
 - CO₂ emissions avoided by displacing grid electricity
 - Embodied carbon from materials (if provided)
 - Transport emissions (if provided)

What's implemented (so far) :
 - Operational carbon (B6) - PV generation and avoided grid emissions
 - Embodied carbon (A1-A3) - Manufacturing emissions for materials (aluminium, steel, concrete, glass, silicon, copper)
 - Transport (A4) - Multi-leg transport with different modes (ship, truck, rail, air)

What's still to come
 - Construction & installation (A5) - On-site emissions from equipment, workers, etc.
 - Component replacements (B2-B5) - Inverters, module degradation over lifetime
 - BESS integration - Battery storage systems
 - Lifetime analysis - Carbon payback period, net savings over project life

Data sources
All emission factors come from open, publicly available sources:

 - PVGIS (EU Joint Research Centre) - Solar irradiance data
 - Our World in Data - Grid electricity emission factors by country
 - ICE Database v4.1 - Material embodied carbon factors
 - UK Government GHG Conversion Factors 2024 - Transport emission factors

Tech stack
 - Frontend: HTML, JavaScript, Chart.js, Leaflet (hosted on GitHub Pages
 - Backend: FastAPI, Python, pvlib (hosted on Railway)
