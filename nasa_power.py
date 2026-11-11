"""Annual and seasonal summaries from daily NASA POWER grid data."""

import json
import math
from datetime import date, timedelta
from http.client import HTTPException
from statistics import mean
from urllib.parse import urlencode
from urllib.request import urlopen

from engine import finite_number

ENDPOINT = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = ("T2M", "RH2M", "PRECTOTCORR")


class PowerDataError(RuntimeError):
    """NASA POWER could not provide a usable response."""


def compare_periods(reference, selected):
    """Return selected minus reference for metrics available in both periods."""
    differences = {}
    for key, value in selected["metrics"].items():
        baseline = reference["metrics"].get(key)
        differences[key] = None if value is None or baseline is None else value - baseline
    return differences


def previous_year_date(day):
    """Match the calendar date, using February 28 when February 29 is absent."""
    if day.month == 2 and day.day == 29:
        return day.replace(year=day.year - 1, day=28)
    return day.replace(year=day.year - 1)


def fetch_annual_grid(latitude, longitude, year):
    result = fetch_grid_period(
        latitude, longitude, date(year, 1, 1), date(year, 12, 31),
        rainfall_key="annual_rainfall_mm",
    )
    result.pop("daily_weather")
    return {**result, "year": year}


def fetch_grid_period(latitude, longitude, start, end, *, rainfall_key="rainfall_mm"):
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        raise ValueError("Enter a latitude from −90 to 90 and a longitude from −180 to 180.")

    days = (end - start).days + 1
    if not 1 <= days <= 366:
        raise ValueError("Choose an ordered date range of up to 366 days.")
    query = urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "parameters": ",".join(PARAMETERS),
        "community": "AG",
        "format": "JSON",
        "time-standard": "UTC",
    })
    try:
        with urlopen(f"{ENDPOINT}?{query}", timeout=15) as response:
            payload = json.load(response)
        series = payload["properties"]["parameter"]
        fill_value = finite_number(payload.get("header", {}).get("fill_value"))
        if not isinstance(series, dict) or not any(code in series for code in PARAMETERS):
            raise ValueError("Missing NASA POWER parameters")
    except (OSError, HTTPException, ValueError, KeyError, AttributeError, TypeError) as error:
        raise PowerDataError("Could not retrieve NASA POWER grid data. Try again later.") from error

    metrics = {}
    coverage = {}
    daily_weather = [
        {"day": number, "date": (start + timedelta(days=number - 1)).isoformat()}
        for number in range(1, days + 1)
    ]
    for code in PARAMETERS:
        readings = series.get(code)
        if not isinstance(readings, dict):
            readings = {}
        key = rainfall_key if code == "PRECTOTCORR" else code
        valid = []
        for row in daily_weather:
            value = finite_number(readings.get(row["date"].replace("-", "")))
            if value in (-999, fill_value):
                value = None
            row[key] = value
            if value is not None:
                valid.append(value)
        coverage[key] = len(valid)
        metrics[key] = None
        if len(valid) == days:
            metrics[key] = math.fsum(valid) if code == "PRECTOTCORR" else mean(valid)

    return {
        "source": "NASA POWER daily grid estimates (UTC)",
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "requested_latitude": latitude,
        "requested_longitude": longitude,
        "expected_days": days,
        "valid_days": coverage,
        "metrics": metrics,
        "daily_weather": daily_weather,
    }
