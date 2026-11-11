from fastapi import APIRouter, HTTPException

import datastore as ds
import engine

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{year}")
def dashboard(year: int):
    """Everything the front-end needs for one year, in a single call."""
    try:
        env = engine.load_environment(year)
    except ValueError as e:
        raise HTTPException(404, str(e))
    try:
        monthly = ds.climate_monthly()
        monthly = monthly[monthly.date.dt.year == year]
        veg = ds.vegetation_16day()
        veg = veg[veg.date.dt.year == year]
        crops = ds.crops()
        crops = crops[crops.Year == year]
    except FileNotFoundError as e:
        raise HTTPException(503, str(e))
    return {
        "year": year,
        "annual_environment": env,
        "climate_monthly": ds.clean(monthly),
        "vegetation_16day": ds.clean(veg),
        "soil": ds.clean(ds.soil_by_depth()),
        "crop_yields": ds.clean(crops[["Item", "crop_ar", "Area harvested", "Production", "yield_t_per_ha"]]),
    }
