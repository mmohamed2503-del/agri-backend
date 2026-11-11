import sys
from datetime import date
from pathlib import Path
from fastapi import APIRouter, HTTPException

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import nasa_power
from nasa_power import PowerDataError
from schemas import CompareWeatherRequest, NasaPowerRequest, WeatherPeriodRequest

router = APIRouter(tags=["weather"])


@router.post("/api/nasa-power")
@router.post("/nasa-power", include_in_schema=False)
def get_nasa_power(request: NasaPowerRequest):
    try:
        return nasa_power.fetch_annual_grid(
            latitude=request.latitude,
            longitude=request.longitude,
            year=request.year,
        )
    except (ValueError, PowerDataError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/wheat-weather")
@router.post("/wheat-weather", include_in_schema=False)
def get_wheat_weather(request: WeatherPeriodRequest):
    try:
        start_date = date.fromisoformat(request.start_date)
        end_date = date.fromisoformat(request.end_date)
        return nasa_power.fetch_grid_period(
            latitude=request.latitude,
            longitude=request.longitude,
            start=start_date,
            end=end_date,
        )
    except (ValueError, PowerDataError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/compare-weather")
@router.post("/compare-weather", include_in_schema=False)
def compare_weather(request: CompareWeatherRequest):
    try:
        selected_start = date.fromisoformat(request.selected_start)
        selected_end = date.fromisoformat(request.selected_end)
        reference_start = date.fromisoformat(request.reference_start)
        reference_end = date.fromisoformat(request.reference_end)

        selected = nasa_power.fetch_grid_period(
            latitude=request.latitude,
            longitude=request.longitude,
            start=selected_start,
            end=selected_end,
        )
        reference = nasa_power.fetch_grid_period(
            latitude=request.latitude,
            longitude=request.longitude,
            start=reference_start,
            end=reference_end,
        )
        differences = nasa_power.compare_periods(reference, selected)

        return {
            "selected": selected,
            "reference": reference,
            "differences": differences,
            "selected_minus_reference": differences,
        }
    except (ValueError, PowerDataError) as e:
        raise HTTPException(status_code=400, detail=str(e))
