
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos
from flatlib import aspects, const
from astral import moon
import datetime

app = FastAPI()

class ChartRequest(BaseModel):
    birth_date: str
    birth_time: str
    birth_place: str

class TransitRequest(BaseModel):
    chart1: Dict[str, Any]
    chart2: Dict[str, Any]

@app.post("/chart")
def get_chart(request: ChartRequest):
    date = request.birth_date  # 'YYYY-MM-DD'
    time = request.birth_time  # 'HH:MM'
    place = request.birth_place  # e.g. 'New York,US'
    # For demo, use fixed coordinates. You can use geopy for real geocoding.
    pos = GeoPos('40.7128', '-74.0060')  # New York
    dt = Datetime(date, time, '+00:00')
    chart = Chart(dt, pos)

    # Get positions and retrograde status
    positions = {}
    retrograde = {}
    for obj in const.MAJOR_OBJECTS:
        planet = chart.get(obj)
        positions[obj] = planet.sign
        retrograde[obj] = planet.isRetrograde()

    # Get aspects
    aspect_list = []
    for aspect in aspects.getAspects(chart.objects):
        aspect_list.append({
            "aspect": aspect.type,
            "planets": [aspect.obj1, aspect.obj2]
        })

    # Get moon phase
    moon_date = datetime.date.fromisoformat(date)
    phase = moon.phase(moon_date)

    chart_data = {
        "positions": positions,
        "retrograde": retrograde,
        "aspects": aspect_list,
        "moon_phase": phase
    }
    return chart_data

@app.post("/transits")
def get_transits(request: TransitRequest):
    def build_chart(chart_data):
        date = chart_data.get('birth_date')
        time = chart_data.get('birth_time')
        pos = GeoPos('40.7128', '-74.0060')  # New York
        dt = Datetime(date, time, '+00:00')
        return Chart(dt, pos)

    chart1 = build_chart(request.chart1)
    chart2 = build_chart(request.chart2)

    transits = []
    for obj in const.MAJOR_OBJECTS:
        planet1 = chart1.get(obj)
        planet2 = chart2.get(obj)
        diff = abs(planet1.lon - planet2.lon)
        aspect_types = {
            'conjunction': 0,
            'opposition': 180,
            'square': 90,
            'trine': 120,
            'sextile': 60
        }
        for aspect, angle in aspect_types.items():
            if abs(diff - angle) < 6:
                transits.append({
                    "planet": obj,
                    "transit": aspect,
                    "chart1_longitude": planet1.lon,
                    "chart2_longitude": planet2.lon
                })
    return {"transits": transits}
