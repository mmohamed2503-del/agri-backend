from typing import Optional

from fastapi import APIRouter, HTTPException, Query

import datastore as ds

router = APIRouter(prefix="/api/data", tags=["data"])

CLIMATE_VARS = ["T2M", "T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M",
                "ALLSKY_SFC_SW_DWN", "WS2M", "GWETTOP", "GWETROOT"]


def _guard(fn):
    try:
        return fn()
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/summary")
def summary():
    """Overview of every dataset served by the API."""
    def build():
        d, m, v, c = ds.climate_daily(), ds.climate_monthly(), ds.vegetation_16day(), ds.crops()
        return {
            "climate_daily": {"rows": len(d), "from": str(d.date.min().date()), "to": str(d.date.max().date()), "variables": CLIMATE_VARS},
            "climate_monthly": {"rows": len(m)},
            "vegetation_16day": {"rows": len(v), "variables": ["EVI", "NDVI"]},
            "soil": {"depths": ds.soil_by_depth()["depth"].tolist()},
            "crops": {"count": int(c["Item"].nunique()), "years": [int(c.Year.min()), int(c.Year.max())]},
        }
    return _guard(build)


@router.get("/climate/daily")
def climate_daily(
    start: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="YYYY-MM-DD"),
    variables: Optional[str] = Query(None, description="comma separated, e.g. T2M,RH2M"),
    limit: int = Query(1000, ge=1, le=4000),
):
    def build():
        df = ds.climate_daily()
        try:
            if start:
                df = df[df.date >= start]
            if end:
                df = df[df.date <= end]
        except Exception:
            raise HTTPException(400, "Invalid date format, use YYYY-MM-DD")
        cols = ["date"]
        if variables:
            req = [v.strip() for v in variables.split(",") if v.strip()]
            bad = [v for v in req if v not in CLIMATE_VARS]
            if bad:
                raise HTTPException(400, f"Unknown variables: {bad}. Available: {CLIMATE_VARS}")
            cols += req
        else:
            cols += CLIMATE_VARS
        df = df[cols].head(limit)
        return {"count": len(df), "rows": ds.clean(df)}
    return _guard(build)


@router.get("/climate/monthly")
def climate_monthly(year: Optional[int] = Query(None, ge=1900, le=2100)):
    def build():
        df = ds.climate_monthly()
        if year:
            df = df[df.date.dt.year == year]
        return {"count": len(df), "rows": ds.clean(df)}
    return _guard(build)


@router.get("/vegetation")
def vegetation(year: Optional[int] = Query(None, ge=1900, le=2100)):
    """EVI / NDVI every 16 days."""
    def build():
        df = ds.vegetation_16day()
        if year:
            df = df[df.date.dt.year == year]
        return {"count": len(df), "rows": ds.clean(df)}
    return _guard(build)


@router.get("/soil")
def soil():
    """Mean soil properties per depth layer."""
    return _guard(lambda: {"rows": ds.clean(ds.soil_by_depth())})


@router.get("/crops")
def crop_list():
    def build():
        df = ds.crops()
        out = df[["Item", "crop_ar"]].drop_duplicates().sort_values("Item")
        return {"count": len(out), "crops": ds.clean(out.rename(columns={"Item": "crop"}))}
    return _guard(build)


@router.get("/crops/yield")
def crop_yield(crop: Optional[str] = Query(None, description="English name, e.g. Wheat")):
    """Egypt-wide area / production / yield per year (not Delta-specific)."""
    def build():
        df = ds.crops()
        if crop:
            df = df[df["Item"].str.lower() == crop.lower()]
            if df.empty:
                raise HTTPException(404, f"No crop named '{crop}'")
        df = df.sort_values(["Item", "Year"])
        return {"count": len(df), "rows": ds.clean(df)}
    return _guard(build)
