import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import engine

router = APIRouter(tags=["environment"])


@router.get("/api/environment/all")
@router.get("/environment/all", include_in_schema=False)
def get_all_environment():
    try:
        years = engine.available_years()
        return [engine.load_environment(year) for year in years]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/environment/{year}")
@router.get("/environment/{year}", include_in_schema=False)
def get_environment_by_year(year: int):
    try:
        return engine.load_environment(year)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
