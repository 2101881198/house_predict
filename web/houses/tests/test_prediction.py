from decimal import Decimal

import pytest
from django.utils import timezone

from houses.models import City, District, House
from houses.services.prediction import predict_price


@pytest.mark.django_db
def test_predict_price_uses_district_average_fallback_when_model_missing(settings, tmp_path):
    city = City.objects.create(name="济南")
    district = District.objects.create(city=city, name="历下区")
    House.objects.create(
        title="历下核心两室",
        city=city,
        district=district,
        total_price=Decimal("200.00"),
        unit_price=Decimal("20000.00"),
        area=Decimal("100.00"),
        room_type="2室1厅",
        floor="中楼层",
        direction="南北",
        decoration="精装",
        build_year=2015,
        crawl_time=timezone.now(),
    )
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
