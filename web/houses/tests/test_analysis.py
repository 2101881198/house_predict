from decimal import Decimal

import pytest
from django.utils import timezone

from houses.models import City, District, House
from houses.services.analysis import build_overview


@pytest.mark.django_db
def test_build_overview_returns_core_metrics():
    city = City.objects.create(name="Test City")
    district = District.objects.create(city=city, name="Test District")

    House.objects.create(
        title="First house",
        city=city,
        district=district,
        total_price=Decimal("100.00"),
        unit_price=Decimal("10000.00"),
        area=Decimal("80.00"),
        room_type="2 bed",
        crawl_time=timezone.now(),
    )
    House.objects.create(
        title="Second house",
        city=city,
        district=district,
        total_price=Decimal("200.00"),
        unit_price=Decimal("20000.00"),
        area=Decimal("100.00"),
        room_type="3 bed",
        crawl_time=timezone.now(),
    )

    overview = build_overview()

    assert overview["total_houses"] == 2
    assert overview["city_count"] == 1
    assert overview["avg_total_price"] == 150.0
    assert overview["avg_unit_price"] == 15000.0
