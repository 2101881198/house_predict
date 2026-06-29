import math
import os
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field


FEATURES = [
    "city",
    "district",
    "area",
    "room_type",
    "floor",
    "direction",
    "decoration",
    "build_year",
]

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "price_model.joblib"
MODEL_PATH = Path(os.getenv("PRICE_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
DEFAULT_AREA = 90.0
DEFAULT_UNIT_PRICE = float(os.getenv("DEFAULT_UNIT_PRICE", "10000"))

app = FastAPI(title="House Price Python Prediction Service")
_model: Any | None = None
_model_error: str | None = None


class PredictRequest(BaseModel):
    city: str | None = ""
    district: str | None = ""
    area: float | None = DEFAULT_AREA
    room_type: str | None = Field(default="", alias="roomType")
    floor: str | None = ""
    direction: str | None = ""
    decoration: str | None = ""
    build_year: int | None = Field(default=2010, alias="buildYear")

    model_config = {
        "populate_by_name": True,
        "extra": "ignore",
    }


def load_model() -> Any | None:
    global _model, _model_error
    if _model is not None:
        return _model
    if not MODEL_PATH.exists():
        _model_error = f"model file not found: {MODEL_PATH}"
        return None
    try:
        _model = joblib.load(MODEL_PATH)
        _model_error = None
        return _model
    except Exception as exc:  # noqa: BLE001 - returned as health info
        _model_error = f"failed to load model: {exc}"
        return None


def normalize_area(value: float | None) -> float:
    try:
        area = float(value if value is not None else DEFAULT_AREA)
    except (TypeError, ValueError):
        return DEFAULT_AREA
    if not math.isfinite(area) or area < 10 or area > 1000:
        return DEFAULT_AREA
    return area


def normalize_features(request: PredictRequest) -> dict[str, Any]:
    return {
        "city": request.city or "",
        "district": request.district or "",
        "area": normalize_area(request.area),
        "room_type": request.room_type or "",
        "floor": request.floor or "",
        "direction": request.direction or "",
        "decoration": request.decoration or "",
        "build_year": int(request.build_year or 2010),
    }


def rule_response(features: dict[str, Any], note: str) -> dict[str, Any]:
    area = normalize_area(features.get("area"))
    predicted_price = round(DEFAULT_UNIT_PRICE * area / 10000, 2)
    return {
        "predicted_price": predicted_price,
        "predicted_unit_price": round(DEFAULT_UNIT_PRICE, 2),
        "model_name": "Python规则估算",
        "note": note,
        "comparison": [
            {"label": "预测总价", "value": predicted_price},
        ],
    }


@app.get("/health")
def health() -> dict[str, Any]:
    model = load_model()
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_path": str(MODEL_PATH),
        "model_error": _model_error,
    }


@app.post("/predict")
def predict(request: PredictRequest) -> dict[str, Any]:
    features = normalize_features(request)
    model = load_model()
    if model is None:
        return rule_response(
            features,
            f"Python预测服务未加载模型，使用默认单价估算；{_model_error}",
        )

    dataframe = pd.DataFrame([features], columns=FEATURES)
    try:
        predicted_value = float(model.predict(dataframe)[0])
    except Exception as exc:  # noqa: BLE001 - fallback keeps API available
        return rule_response(features, f"Python模型预测失败，使用默认单价估算；{exc}")

    if not math.isfinite(predicted_value):
        return rule_response(features, "Python模型返回非有限数值，使用默认单价估算")

    predicted_price = round(predicted_value, 2)
    area = normalize_area(features.get("area"))
    predicted_unit_price = round(predicted_price * 10000 / area, 2)
    return {
        "predicted_price": predicted_price,
        "predicted_unit_price": predicted_unit_price,
        "model_name": "Python随机森林回归",
        "note": "使用独立 Python 预测服务返回结果",
        "comparison": [
            {"label": "预测总价", "value": predicted_price},
        ],
    }
