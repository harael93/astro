
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from skyfield.api import load, Topos
from skyfield.api import N, W
from astral import moon
import datetime



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"]
)

class ChartRequest(BaseModel):
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float

class TransitRequest(BaseModel):
    chart1: Dict[str, Any]
    chart2: Dict[str, Any]

@app.post("/chart")
def get_chart(request: ChartRequest):
    date = request.birth_date  # 'YYYY-MM-DD'
    time = request.birth_time  # 'HH:MM'
    latitude = request.latitude
    longitude = request.longitude
    ts = load.timescale()
    dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute)
    planets = {
        "sun": "SUN",
        "moon": "MOON",
        "mercury": "MERCURY BARYCENTER",
        "venus": "VENUS BARYCENTER",
        "mars": "MARS BARYCENTER",
        "jupiter": "JUPITER BARYCENTER",
        "saturn": "SATURN BARYCENTER",
        "uranus": "URANUS BARYCENTER",
        "neptune": "NEPTUNE BARYCENTER",
        "pluto": "PLUTO BARYCENTER"
    }
    eph = load('de421.bsp')
    observer = Topos(latitude*N, longitude*W)
    positions = {}
    for name, key in planets.items():
        planet = eph[key]
        astrometric = eph['earth'] + observer
        apparent = astrometric.at(t).observe(planet).apparent()
        ra, dec, distance = apparent.radec()
        positions[name] = {
            "ra": ra.hours,
            "dec": dec.degrees,
            "distance": distance.au
        }
    # Get moon phase
    moon_date = datetime.date.fromisoformat(date)
    phase = moon.phase(moon_date)
    chart_data = {
        "positions": positions,
        "moon_phase": phase
    }
    return chart_data

@app.post("/transits")
def get_transits(request: TransitRequest):
    def get_positions(chart_data):
        date = chart_data.get('birth_date')
        time = chart_data.get('birth_time')
        latitude = chart_data.get('latitude')
        longitude = chart_data.get('longitude')
        ts = load.timescale()
        dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute)
        eph = load('de421.bsp')
        observer = Topos(latitude*N, longitude*W)
        planets = {
            "sun": "SUN",
            "moon": "MOON",
            "mercury": "MERCURY BARYCENTER",
            "venus": "VENUS BARYCENTER",
            "mars": "MARS BARYCENTER",
            "jupiter": "JUPITER BARYCENTER",
            "saturn": "SATURN BARYCENTER",
            "uranus": "URANUS BARYCENTER",
            "neptune": "NEPTUNE BARYCENTER",
            "pluto": "PLUTO BARYCENTER"
        }
        positions = {}
        for name, key in planets.items():
            planet = eph[key]
            astrometric = eph['earth'] + observer
            apparent = astrometric.at(t).observe(planet).apparent()
            ra, dec, distance = apparent.radec()
            positions[name] = ra.hours
        return positions

    pos1 = get_positions(request.chart1)
    pos2 = get_positions(request.chart2)
    transits = []
    aspect_types = {
        'conjunction': 0,
        'opposition': 12,
        'square': 6,
        'trine': 8,
        'sextile': 4
    }
    for planet in pos1:
        diff = abs(pos1[planet] - pos2[planet])
        for aspect, angle in aspect_types.items():
            if abs(diff - angle) < 0.5:
                transits.append({
                    "planet": planet,
                    "transit": aspect,
                    "chart1_ra": pos1[planet],
                    "chart2_ra": pos2[planet]
                })
    return {"transits": transits}
