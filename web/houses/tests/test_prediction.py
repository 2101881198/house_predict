import math
from decimal import Decimal

import pytest
from django.utils import timezone

from houses.models import City, District, House
from houses.services.prediction import predict_price


def _create_house(city, district, unit_price="20000.00", area="100.00"):
    area_decimal = Decimal(area)
    unit_price_decimal = Decimal(unit_price)
    total_price = unit_price_decimal * area_decimal / Decimal("10000")
    return House.objects.create(
        title="测试房源",
        city=city,
        district=district,
        total_price=total_price,
        unit_price=unit_price_decimal,
        area=area_decimal,
        room_type="2室1厅",
        floor="中楼层",
        direction="南北",
        decoration="精装",
        build_year=2015,
        crawl_time=timezone.now(),
    )


@pytest.mark.django_db
def test_predict_price_uses_district_average_fallback_when_model_missing(settings, tmp_path):
    city = City.objects.create(name="济南")
    district = District.objects.create(city=city, name="历下区")
    _create_house(city, district)
    settings.MODEL_DIR = tmp_path / "missing-models"

    result = predict_price(
        {
            "city": "济南",
            "district": "历下区",
            "area": 80,
            "room_type": "2室1厅",
            "floor": "中楼层",
            "direction": "南北",
            "decoration": "精装",
            "build_year": 2015,
        }
    )

    assert result["model_name"] == "规则估算"
    assert result["predicted_price"] == 160.0
    assert result["predicted_unit_price"] == 20000.0


@pytest.mark.django_db
@pytest.mark.parametrize("features", [None, []])
def test_predict_price_empty_features_use_default_rule_estimate(
    settings, tmp_path, features
):
    settings.MODEL_DIR = tmp_path / "missing-models"

    result = predict_price(features)

    assert result["model_name"] == "规则估算"
    assert result["predicted_price"] == 90.0
    assert result["predicted_unit_price"] == 10000.0


@pytest.mark.django_db
@pytest.mark.parametrize("area", ["inf", "nan", "abc"])
@pytest.mark.parametrize("build_year", ["inf", "nan", "abc"])
def test_predict_price_invalid_numeric_inputs_use_finite_defaults(
    settings, tmp_path, area, build_year
):
    settings.MODEL_DIR = tmp_path / "missing-models"

    result = predict_price({"area": area, "build_year": build_year})

    assert result["model_name"] == "规则估算"
    assert result["predicted_price"] == 90.0
    assert result["predicted_unit_price"] == 10000.0
    assert math.isfinite(result["predicted_price"])
    assert math.isfinite(result["predicted_unit_price"])


@pytest.mark.django_db
def test_predict_price_corrupt_model_file_falls_back_to_rule_estimate(
    settings, tmp_path
):
    settings.MODEL_DIR = tmp_path
    (tmp_path / "price_model.joblib").write_text("not a joblib model", encoding="utf-8")

    result = predict_price({"area": 90})

    assert result["model_name"] == "规则估算"
    assert result["predicted_price"] == 90.0
    assert "model unavailable" in result["note"].lower()


@pytest.mark.django_db
def test_predict_price_uses_city_average_when_district_mismatches(settings, tmp_path):
    city = City.objects.create(name="青岛")
    district = District.objects.create(city=city, name="市南区")
    _create_house(city, district, unit_price="15000.00")
    settings.MODEL_DIR = tmp_path / "missing-models"

    result = predict_price({"city": "青岛", "district": "不存在区", "area": 100})

    assert result["model_name"] == "规则估算"
    assert result["predicted_price"] == 150.0
    assert result["predicted_unit_price"] == 15000.0
