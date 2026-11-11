"""Pydantic schemas for the Field Shift API."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    year: int = Field(default=2024, description="Year for environmental baseline")
    ph: float = Field(default=7.5, description="Soil pH (3-10)")
    texture: str = Field(default="clay", description="Soil texture: clay, loam, or sand")
    water_index: int = Field(default=55, description="Relative water index (0-100)")
    previous: Optional[str] = Field(default=None, description="Previous crop name or null")
    season: str = Field(default="winter", description="Target season: winter or summer")


class RecommendRequest(BaseModel):
    year: int = Field(default=2024, description="Year for environmental baseline")
    ph: float = Field(default=7.5, description="Soil pH (3-10)")
    texture: str = Field(default="clay", description="Soil texture: clay, loam, or sand")
    water_index: int = Field(default=55, description="Relative water index (0-100)")
    previous: Optional[str] = Field(default=None, description="Previous crop name or null")
    next_season: Optional[str] = Field(default=None, description="Optional target next season: winter or summer")
    rotation_priority: str = Field(default="balanced", description="Rotation priority: balanced, water, or diversity")


class NasaPowerRequest(BaseModel):
    latitude: float = Field(..., description="Target latitude (-90 to 90)")
    longitude: float = Field(..., description="Target longitude (-180 to 180)")
    year: int = Field(..., description="Calendar year for annual summary")


class WeatherPeriodRequest(BaseModel):
    latitude: float = Field(..., description="Target latitude (-90 to 90)")
    longitude: float = Field(..., description="Target longitude (-180 to 180)")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD")
    end_date: str = Field(..., description="End date in YYYY-MM-DD")


class CompareWeatherRequest(BaseModel):
    latitude: float = Field(..., description="Target latitude (-90 to 90)")
    longitude: float = Field(..., description="Target longitude (-180 to 180)")
    selected_start: str = Field(..., description="Selected period start date in YYYY-MM-DD")
    selected_end: str = Field(..., description="Selected period end date in YYYY-MM-DD")
    reference_start: str = Field(..., description="Reference period start date in YYYY-MM-DD")
    reference_end: str = Field(..., description="Reference period end date in YYYY-MM-DD")


class CropCandidate(BaseModel):
    crop: str
    score: float


class PredictResponse(BaseModel):
    model_type: str
    season: str
    top_crop: CropCandidate
    alternatives: List[CropCandidate]
    tied_top_crops: List[str]


class MessageResponse(BaseModel):
    message: str
