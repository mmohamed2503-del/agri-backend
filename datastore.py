"""Loads the cleaned datasets once and serves them as JSON-safe structures."""
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"


def clean(df: pd.DataFrame) -> list:
    """DataFrame -> list of dicts with NaN/inf -> None and dates -> ISO strings."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime("%Y-%m-%d")
    df = df.replace([np.inf, -np.inf], np.nan).astype(object)
    df = df.where(df.notna(), None)
    return df.to_dict(orient="records")


@lru_cache(maxsize=None)
def _sheet(file: str, sheet: str) -> pd.DataFrame:
    path = DATA_DIR / file
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {file}")
    return pd.read_excel(path, sheet_name=sheet)


def climate_daily() -> pd.DataFrame:
    df = _sheet("newdelta_dataset_10y.xlsx", "climate_soilwetness_daily").copy()
    df["date"] = pd.to_datetime(df["date"])
    return df


def climate_monthly() -> pd.DataFrame:
    df = _sheet("newdelta_dataset_10y.xlsx", "monthly_merged").copy()
    df["date"] = pd.to_datetime(df["date"])
    return df


def vegetation_16day() -> pd.DataFrame:
    df = _sheet("newdelta_dataset_10y.xlsx", "vegetation_16day").copy()
    df["date"] = pd.to_datetime(df["date"])
    return df


def soil_by_depth() -> pd.DataFrame:
    return _sheet("soil_10y.xlsx", "soil_by_depth")


def crops() -> pd.DataFrame:
    return _sheet("crops_10y.xlsx", "egypt_crops")


# ---------- Grid layers (lat/lon cells) ----------
GRID_LAYERS = {
    "et":      {"file": "et_grid.csv",  "vars": ["et_geos", "et0_fao56"], "desc": "Evapotranspiration"},
    "aerosol": {"file": "aerosols.csv", "vars": ["aod"], "desc": "Dust & aerosol optical depth"},
    "solar":   {"file": "solar.csv",    "vars": ["solar_radiation", "solar_clearsky", "rainfall"], "desc": "Solar radiation + rainfall"},
    "lai":     {"file": "lai.csv",      "vars": ["fpar", "lai"], "desc": "Leaf area & light absorption"},
    "gpp":     {"file": "gpp.csv",      "vars": ["gpp", "psn_net"], "desc": "Primary productivity"},
    "ndmi":    {"file": "ndmi.csv",     "vars": ["ndmi"], "desc": "Vegetation water index"},
}


@lru_cache(maxsize=None)
def grid(layer: str) -> pd.DataFrame:
    if layer not in GRID_LAYERS:
        raise KeyError(layer)
    path = DATA_DIR / GRID_LAYERS[layer]["file"]
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path.name}")
    df = pd.read_csv(path, parse_dates=["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    return df
