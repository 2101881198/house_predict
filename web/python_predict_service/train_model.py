import os
from pathlib import Path

import joblib
import pandas as pd
import pymysql
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


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
CATEGORICAL_FEATURES = ["city", "district", "room_type", "floor", "direction", "decoration"]
NUMERIC_FEATURES = ["area", "build_year"]
DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "models" / "price_model.joblib"


def connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "house_predict"),
        charset="utf8mb4",
    )


def load_training_data() -> pd.DataFrame:
    sql = """
        select
            c.name as city,
            d.name as district,
            h.area,
            h.room_type,
            h.floor,
            h.direction,
            h.decoration,
            coalesce(h.build_year, 2010) as build_year,
            h.total_price
        from houses_house h
        join houses_city c on c.id = h.city_id
        join houses_district d on d.id = h.district_id
        where h.total_price > 0 and h.area > 10
    """
    with connection() as conn:
        return pd.read_sql(sql, conn)


def train() -> dict[str, float | int | str | bool]:
    dataframe = load_training_data()
    if len(dataframe) < 12:
        return {"trained": False, "reason": "有效训练数据不足 12 条", "sample_count": len(dataframe)}

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                RandomForestRegressor(
                    n_estimators=int(os.getenv("RF_N_ESTIMATORS", "120")),
                    random_state=42,
                    min_samples_leaf=1,
                ),
            ),
        ]
    )

    train_rows, test_rows = train_test_split(dataframe, test_size=0.25, random_state=42)
    model.fit(train_rows[FEATURES], train_rows["total_price"])
    predictions = model.predict(test_rows[FEATURES])

    model_path = Path(os.getenv("PRICE_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    mse = mean_squared_error(test_rows["total_price"], predictions)
    return {
        "trained": True,
        "model_path": str(model_path),
        "mae": round(float(mean_absolute_error(test_rows["total_price"], predictions)), 2),
        "mse": round(float(mse), 2),
        "rmse": round(float(mse**0.5), 2),
        "r2": round(float(r2_score(test_rows["total_price"], predictions)), 4),
        "sample_count": len(dataframe),
    }


if __name__ == "__main__":
    print(train())
