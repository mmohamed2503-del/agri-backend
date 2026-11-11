from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import datastore as ds

router = APIRouter(prefix="/api/grid", tags=["grid layers"])


def _layer(name: str):
    try:
        return ds.grid(name), ds.GRID_LAYERS[name]["vars"]
    except KeyError:
        raise HTTPException(404, f"Unknown layer '{name}'. Available: {list(ds.GRID_LAYERS)}")
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))


def _cell(df, lat, lon):
    if (lat is None) != (lon is None):
        raise HTTPException(400, "Provide both lat and lon, or neither")
    if lat is None:
        return df
    # nearest grid cell
    cells = df[["lat", "lon"]].drop_duplicates()
    d = (cells.lat - lat) ** 2 + (cells.lon - lon) ** 2
    near = cells.loc[d.idxmin()]
    return df[(df.lat == near.lat) & (df.lon == near.lon)]


@router.get("/layers")
def layers():
    out = []
    for name, meta in ds.GRID_LAYERS.items():
        df, _ = _layer(name)
        out.append({"layer": name, "description": meta["desc"], "variables": meta["vars"],
                    "from": str(df.date.min().date()), "to": str(df.date.max().date()),
                    "cells": int(df[["lat", "lon"]].drop_duplicates().shape[0])})
    return out


@router.get("/{layer}/monthly")
def monthly(layer: str, year: Optional[int] = None,
            lat: Optional[float] = Query(None, ge=-90, le=90), lon: Optional[float] = Query(None, ge=-180, le=180)):
    """Monthly mean of each variable (nearest cell if lat/lon given, else mean of all cells)."""
    df, vars_ = _layer(layer)
    df = _cell(df, lat, lon)
    if year:
        df = df[df.year == year]
    if df.empty:
        raise HTTPException(404, "No data for this selection")
    g = df.groupby(["year", "month"])[vars_].mean().round(4).reset_index()
    return {"layer": layer, "count": len(g), "rows": ds.clean(g)}


@router.get("/{layer}/yearly")
def yearly(layer: str, lat: Optional[float] = Query(None, ge=-90, le=90), lon: Optional[float] = Query(None, ge=-180, le=180)):
    df, vars_ = _layer(layer)
    df = _cell(df, lat, lon)
    g = df.groupby("year")[vars_].mean().round(4).reset_index()
    return {"layer": layer, "count": len(g), "rows": ds.clean(g)}


@router.get("/{layer}/map")
def map_points(layer: str, year: int, month: Optional[int] = Query(None, ge=1, le=12)):
    """One value per grid cell (mean over the year or month) - for map visualisation."""
    df, vars_ = _layer(layer)
    df = df[df.year == year]
    if month:
        df = df[df.month == month]
    if df.empty:
        raise HTTPException(404, "No data for this selection")
    g = df.groupby(["lat", "lon"])[vars_].mean().round(4).reset_index()
    return {"layer": layer, "year": year, "month": month, "count": len(g), "points": ds.clean(g)}
