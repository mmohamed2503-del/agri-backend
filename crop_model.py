"""Inference for the rule-trained next-cycle crop ranking model."""

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

from engine import CROPS, load_environment

MODEL_PATH = Path(__file__).parent / "outputs" / "crop_model.json"
TEXTURES = ("clay", "loam", "sand")


def feature_matrix(temperature, ph, texture, water, same_family):
    temperature, ph, water, same_family = (
        np.atleast_1d(value).astype(float) for value in (temperature, ph, water, same_family)
    )
    texture = np.atleast_1d(texture)
    base = np.column_stack((
        np.ones(len(ph)),
        (temperature - 21) / 5,
        (ph - 3) / 7,
        np.maximum(0, ph[:, None] - np.arange(3.5, 10, 0.5)) / 7,
        np.maximum(0, ph - 7.8) / 7,
        water / 100,
        np.maximum(0, water[:, None] - np.arange(5, 100, 5)) / 100,
        texture == "loam",
        texture == "sand",
    ))
    return np.column_stack((base, base * same_family[:, None]))


@lru_cache(maxsize=1)
def load_model():
    model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    if model["format_version"] != 1:
        raise ValueError("Unsupported crop model format.")
    return model["coefficients"]


def predict_next_crop(year, ph, texture, water_index, previous, season):
    """Return the leading crop and two alternatives for the requested season."""
    if season not in ("winter", "summer"):
        raise ValueError("season must be winter or summer.")
    if texture not in TEXTURES or not 3 <= ph <= 10 or not 0 <= water_index <= 100:
        raise ValueError("Use clay, loam or sand, pH 3–10 and a water index of 0–100.")
    if previous is not None and previous not in CROPS:
        raise ValueError("previous must be a supported crop name or null.")
    temperature = load_environment(year).get("T2M")
    if temperature is None:
        raise ValueError("Regional mean temperature is unavailable for this year.")

    candidates = []
    coefficients = load_model()
    previous_family = CROPS[previous]["family"] if previous else None
    for crop, profile in CROPS.items():
        if profile["season"] == season:
            features = feature_matrix(temperature, ph, texture, water_index, previous_family == profile["family"])
            score = float(np.clip((features @ coefficients[crop])[0], 0, 100))
            candidates.append({"crop": crop, "score": round(score, 1)})
    candidates.sort(key=lambda item: item["score"], reverse=True)
    top = candidates[0]
    return {
        "model_type": "trained_rule_surrogate",
        "season": season,
        "top_crop": top,
        "alternatives": candidates[1:3],
        "tied_top_crops": [item["crop"] for item in candidates if item["score"] == top["score"]],
    }
