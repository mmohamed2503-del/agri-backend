import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import crop_model
import engine
from schemas import PredictRequest, RecommendRequest

router = APIRouter(tags=["crops"])


@router.post("/api/predict")
@router.post("/predict", include_in_schema=False)
def predict_crop(request: PredictRequest):
    try:
        return crop_model.predict_next_crop(
            year=request.year,
            ph=request.ph,
            texture=request.texture,
            water_index=request.water_index,
            previous=request.previous,
            season=request.season,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/recommend")
@router.post("/recommend", include_in_schema=False)
def recommend_crops(request: RecommendRequest):
    try:
        return engine.run(
            year=request.year,
            ph=request.ph,
            texture=request.texture,
            water_index=request.water_index,
            previous=request.previous,
            next_season=request.next_season,
            rotation_priority=request.rotation_priority,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/crops")
@router.get("/crops", include_in_schema=False)
def get_crops():
    return engine.CROPS


@router.get("/api/years")
@router.get("/years", include_in_schema=False)
def get_years():
    try:
        return engine.available_years()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
