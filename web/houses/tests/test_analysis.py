from decimal import Decimal

import pytest
from django.utils import timezone

from houses.models import City, District, House
from houses.services.analysis import (
    build_overview,
    build_price_buckets,
    build_province_stats,
)


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


@pytest.mark.django_db
def test_build_overview_city_count_counts_city_rows_without_houses():
    city = City.objects.create(name="City With Houses")
    district = District.objects.create(city=city, name="Test District")
    City.objects.create(name="Empty City")
    House.objects.create(
        title="Counted house",
        city=city,
        district=district,
        total_price=Decimal("120.00"),
        unit_price=Decimal("12000.00"),
        area=Decimal("80.00"),
        room_type="2 bed",
        crawl_time=timezone.now(),
    )

    overview = build_overview()

    assert overview["city_count"] == 2


@pytest.mark.django_db
def test_build_price_buckets_returns_label_count_items():
    city = City.objects.create(name="Test City")
    district = District.objects.create(city=city, name="Test District")
    House.objects.create(
        title="Bucket house",
        city=city,
        district=district,
        total_price=Decimal("120.00"),
        unit_price=Decimal("12000.00"),
        area=Decimal("80.00"),
        room_type="2 bed",
        crawl_time=timezone.now(),
    )

    buckets = build_price_buckets()

    assert isinstance(buckets, list)
    assert buckets[0].keys() == {"label", "count"}
    assert sum(item["count"] for item in buckets) == 1


@pytest.mark.django_db
def test_build_province_stats_uses_city_key_for_city_name():
    city = City.objects.create(name="Test City")
    district = District.objects.create(city=city, name="Test District")
    House.objects.create(
        title="Province house",
        city=city,
        district=district,
        total_price=Decimal("120.00"),
        unit_price=Decimal("12000.00"),
        area=Decimal("80.00"),
        room_type="2 bed",
        crawl_time=timezone.now(),
    )

    stats = build_province_stats()

    assert stats["cities"][0].keys() == {
        "city",
        "count",
        "avg_total_price",
        "avg_unit_price",
        "max_total_price",
        "min_total_price",
    }
    assert stats["cities"][0]["city"] == "Test City"
    assert "name" not in stats["cities"][0]
