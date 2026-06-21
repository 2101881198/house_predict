import logging
import math
from collections.abc import Mapping
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings
from django.db.models import Avg
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from houses.models import House


logger = logging.getLogger(__name__)

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
MODEL_FILE = "price_model.joblib"
DEFAULT_AREA = 90.0
MIN_AREA = 10.0
MAX_AREA = 1000.0

CATEGORICAL_FEATURES = [
    "city",
    "district",
    "room_type",
    "floor",
    "direction",
    "decoration",
]
NUMERIC_FEATURES = ["area", "build_year"]


def _model_path():
    return Path(settings.MODEL_DIR) / MODEL_FILE


def _coerce_finite_float(value, default):
    try:
        if value in ("", None):
            return float(default)
        coerced = float(value)
    except (TypeError, ValueError, OverflowError):
        return float(default)
    if not math.isfinite(coerced):
        return float(default)
    return coerced


def _coerce_area(value):
    area = _coerce_finite_float(value, DEFAULT_AREA)
    if area < MIN_AREA or area > MAX_AREA:
        return DEFAULT_AREA
    return area


def _coerce_build_year(value):
    build_year = _coerce_finite_float(value, 2010)
    return int(build_year)


def _normalize_features(features):
    if not isinstance(features, Mapping):
        features = {}
    return {
        "city": str(features.get("city") or ""),
        "district": str(features.get("district") or ""),
        "area": _coerce_area(features.get("area")),
        "room_type": str(features.get("room_type") or ""),
        "floor": str(features.get("floor") or ""),
        "direction": str(features.get("direction") or ""),
        "decoration": str(features.get("decoration") or ""),
        "build_year": _coerce_build_year(features.get("build_year")),
    }


def _house_dataframe():
    rows = []
    houses = (
        House.objects.filter(total_price__gt=0, area__gt=10)
        .select_related("city", "district")
        .order_by("id")
    )
    for house in houses:
        rows.append(
            {
                "city": house.city.name,
                "district": house.district.name,
                "area": float(house.area),
                "room_type": house.room_type,
                "floor": house.floor,
                "direction": house.direction,
                "decoration": house.decoration,
                "build_year": house.build_year or 2010,
                "total_price": float(house.total_price),
            }
        )
    return pd.DataFrame(rows, columns=[*FEATURES, "total_price"])


def train_price_model():
    dataframe = _house_dataframe()
    if len(dataframe) < 12:
        return {"trained": False, "reason": "有效训练数据不足 12 条"}

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=120,
                    random_state=42,
                    min_samples_leaf=1,
                ),
            ),
        ]
    )

    train, test = train_test_split(dataframe, test_size=0.25, random_state=42)
    model.fit(train[FEATURES], train["total_price"])
    predictions = model.predict(test[FEATURES])

    model_path = _model_path()
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    mse = mean_squared_error(test["total_price"], predictions)
    return {
        "trained": True,
        "model_name": "随机森林回归",
        "mae": round(float(mean_absolute_error(test["total_price"], predictions)), 2),
        "mse": round(float(mse), 2),
        "rmse": round(float(mse**0.5), 2),
        "r2": round(float(r2_score(test["total_price"], predictions)), 4),
        "sample_count": len(dataframe),
    }


def _average_unit_price(features):
    queryset = House.objects.filter(unit_price__gt=0)
    city_name = features.get("city")
    district_name = features.get("district")

    if city_name:
        city_queryset = queryset.filter(city__name=city_name)
        if city_queryset.exists():
            if district_name:
                district_queryset = city_queryset.filter(district__name=district_name)
                district_average = district_queryset.aggregate(value=Avg("unit_price"))[
                    "value"
                ]
                if district_average is not None:
                    unit_price = _coerce_finite_float(district_average, 10000)
                    if unit_price > 0:
                        return unit_price

            city_average = city_queryset.aggregate(value=Avg("unit_price"))["value"]
            if city_average is not None:
                unit_price = _coerce_finite_float(city_average, 10000)
                if unit_price > 0:
                    return unit_price

    all_average = queryset.aggregate(value=Avg("unit_price"))["value"]
    if all_average is not None:
        unit_price = _coerce_finite_float(all_average, 10000)
        if unit_price > 0:
            return unit_price
    return 10000.0


def _rule_predict(features, note="模型文件不存在，使用区域均价估算"):
    normalized = _normalize_features(features)
    area = normalized["area"]
    unit_price = _average_unit_price(normalized)
    predicted_price = round(unit_price * area / 10000, 2)
    return {
        "predicted_price": predicted_price,
        "predicted_unit_price": round(unit_price, 2),
        "model_name": "规则估算",
        "note": note,
    }


def predict_price(features):
    normalized = _normalize_features(features)
    model_path = _model_path()
    if not model_path.exists():
        return _rule_predict(normalized)

    try:
        model = joblib.load(model_path)
    except Exception:
        logger.exception("Failed to load trained price model from %s", model_path)
        return _rule_predict(
            normalized,
            note="已训练模型不可用 (trained model unavailable)，使用规则估算",
        )

    dataframe = pd.DataFrame([normalized], columns=FEATURES)
    try:
        predicted_value = float(model.predict(dataframe)[0])
    except Exception:
        logger.exception("Failed to predict price with trained model %s", model_path)
        return _rule_predict(
            normalized,
            note="已训练模型不可用 (trained model unavailable)，使用规则估算",
        )
    if not math.isfinite(predicted_value):
        logger.error(
            "Trained price model returned a non-finite prediction: %s",
            predicted_value,
        )
        return _rule_predict(
            normalized,
            note="已训练模型不可用 (trained model unavailable)，使用规则估算",
        )

    predicted_price = round(predicted_value, 2)
    area = normalized["area"]
    predicted_unit_price = round(predicted_price * 10000 / area, 2)
    return {
        "predicted_price": predicted_price,
        "predicted_unit_price": predicted_unit_price,
        "model_name": "随机森林回归",
        "note": "使用已训练随机森林模型预测",
    }
