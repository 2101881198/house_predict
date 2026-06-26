import json
from datetime import UTC
from decimal import Decimal

import pytest
from django.core.management import call_command
from django.utils import timezone

from houses.models import AnalysisResult, City, District, House
from houses.services.analysis import (
    _build_price_trend,
    build_city_stats,
    build_decoration_distribution,
    build_overview,
    build_area_buckets,
    build_price_buckets,
    build_province_stats,
    build_room_type_distribution,
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
def test_dashboard_analysis_outputs_include_richer_visualization_data():
    first_city = City.objects.create(name="First City")
    first_district = District.objects.create(city=first_city, name="First District")
    second_city = City.objects.create(name="Second City")
    second_district = District.objects.create(city=second_city, name="Second District")
    House.objects.create(
        title="First visual house",
        city=first_city,
        district=first_district,
        total_price=Decimal("100.00"),
        unit_price=Decimal("10000.00"),
        area=Decimal("80.00"),
        room_type="2 bed",
        decoration="精装",
        crawl_time=timezone.now(),
    )
    House.objects.create(
        title="Second visual house",
        city=second_city,
        district=second_district,
        total_price=Decimal("300.00"),
        unit_price=Decimal("30000.00"),
        area=Decimal("130.00"),
        room_type="3 bed",
        decoration="毛坯",
        crawl_time=timezone.now(),
    )

    overview = build_overview()

    assert overview["city_price_rankings"] == [
        {
            "city": "Second City",
            "count": 1,
            "avg_total_price": 300.0,
            "avg_unit_price": 30000.0,
        },
        {
            "city": "First City",
            "count": 1,
            "avg_total_price": 100.0,
            "avg_unit_price": 10000.0,
        },
    ]
    assert sum(row["count"] for row in build_area_buckets()) == 2
    assert build_decoration_distribution() == [
        {"decoration": "毛坯", "count": 1},
        {"decoration": "精装", "count": 1},
    ]


def test_build_price_trend_groups_by_local_quarter():
    first_time = timezone.datetime(2023, 5, 3, 10, 30, tzinfo=UTC)
    second_time = timezone.datetime(2023, 6, 4, 2, 0, tzinfo=UTC)
    third_time = timezone.datetime(2023, 8, 4, 2, 0, tzinfo=UTC)

    trend = _build_price_trend(
        [
            {"crawl_time": first_time, "total_price": Decimal("100.00")},
            {"crawl_time": first_time, "total_price": Decimal("200.00")},
            {"crawl_time": second_time, "total_price": Decimal("300.00")},
            {"crawl_time": third_time, "total_price": Decimal("500.00")},
        ]
    )

    assert trend == [
        {"date": "2023 Q2", "avg_total_price": 200.0, "count": 3},
        {"date": "2023 Q3", "avg_total_price": 500.0, "count": 1},
    ]


@pytest.mark.django_db
def test_build_overview_includes_top_city_price_trends():
    first_city = City.objects.create(name="First City")
    first_district = District.objects.create(city=first_city, name="First District")
    second_city = City.objects.create(name="Second City")
    second_district = District.objects.create(city=second_city, name="Second District")
    first_time = timezone.datetime(2023, 5, 3, 10, 30, tzinfo=UTC)
    second_time = timezone.datetime(2023, 5, 4, 10, 30, tzinfo=UTC)

    House.objects.create(
        title="First city day one",
        city=first_city,
        district=first_district,
        total_price=Decimal("100.00"),
        unit_price=Decimal("10000.00"),
        area=Decimal("80.00"),
        room_type="2 bed",
        crawl_time=first_time,
    )
    House.objects.create(
        title="First city day two",
        city=first_city,
        district=first_district,
        total_price=Decimal("200.00"),
        unit_price=Decimal("20000.00"),
        area=Decimal("90.00"),
        room_type="3 bed",
        crawl_time=second_time,
    )
    House.objects.create(
        title="Second city day one",
        city=second_city,
        district=second_district,
        total_price=Decimal("300.00"),
        unit_price=Decimal("30000.00"),
        area=Decimal("100.00"),
        room_type="3 bed",
        crawl_time=first_time,
    )

    overview = build_overview()

    assert overview["city_price_trends"] == [
        {
            "city": "First City",
            "trend": [
                {"date": "2023 Q2", "avg_total_price": 150.0, "count": 2},
            ],
        },
        {
            "city": "Second City",
            "trend": [
                {"date": "2023 Q2", "avg_total_price": 300.0, "count": 1},
            ],
        },
    ]


@pytest.mark.django_db
def test_build_city_stats_includes_city_price_trend():
    city = City.objects.create(name="Trend City")
    district = District.objects.create(city=city, name="Trend District")
    first_time = timezone.datetime(2023, 5, 3, 10, 30, tzinfo=UTC)
    second_time = timezone.datetime(2023, 5, 4, 10, 30, tzinfo=UTC)

    House.objects.create(
        title="Trend day one",
        city=city,
        district=district,
        total_price=Decimal("120.00"),
        unit_price=Decimal("12000.00"),
        area=Decimal("80.00"),
        room_type="2 bed",
        crawl_time=first_time,
    )
    House.objects.create(
        title="Trend day two",
        city=city,
        district=district,
        total_price=Decimal("180.00"),
        unit_price=Decimal("18000.00"),
        area=Decimal("90.00"),
        room_type="3 bed",
        crawl_time=second_time,
    )

    stats = build_city_stats(city.id)

    assert stats["trend"] == [
        {"date": "2023 Q2", "avg_total_price": 150.0, "count": 2},
    ]


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
def test_build_price_buckets_counts_exact_boundaries():
    city = City.objects.create(name="Boundary City")
    district = District.objects.create(city=city, name="Boundary District")
    for price in ["99.99", "100.00", "150.00", "200.00", "300.00"]:
        House.objects.create(
            title=f"Boundary house {price}",
            city=city,
            district=district,
            total_price=Decimal(price),
            unit_price=Decimal("12000.00"),
            area=Decimal("80.00"),
            room_type="2 bed",
            crawl_time=timezone.now(),
        )

    buckets = {item["label"]: item["count"] for item in build_price_buckets()}

    assert buckets == {
        "100万以下": 1,
        "100-150万": 1,
        "150-200万": 1,
        "200-300万": 1,
        "300万以上": 1,
    }


@pytest.mark.django_db
def test_empty_analysis_outputs_are_json_friendly():
    overview = build_overview()
    province_stats = build_province_stats()
    price_buckets = build_price_buckets()

    assert overview["total_houses"] == 0
    assert overview["city_distribution"] == []
    assert overview["hot_districts"] == []
    assert overview["trend"] == []
    assert overview["map_points"] == []
    assert province_stats == {"cities": []}
    assert all(item["count"] == 0 for item in price_buckets)

    json.dumps(overview, ensure_ascii=False)
    json.dumps(province_stats, ensure_ascii=False)
    json.dumps({"items": price_buckets}, ensure_ascii=False)
    json.dumps({"items": build_room_type_distribution()}, ensure_ascii=False)


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


@pytest.mark.django_db
def test_generate_analysis_creates_global_and_city_rows_and_collapses_duplicates():
    first_city = City.objects.create(name="First City")
    first_district = District.objects.create(city=first_city, name="First District")
    second_city = City.objects.create(name="Second City")
    District.objects.create(city=second_city, name="Second District")
    House.objects.create(
        title="Command house",
        city=first_city,
        district=first_district,
        total_price=Decimal("120.00"),
        unit_price=Decimal("12000.00"),
        area=Decimal("80.00"),
        room_type="2 bed",
        crawl_time=timezone.now(),
    )
    AnalysisResult.objects.create(
        analysis_type="overview",
        city=None,
        district=None,
        result_json={"stale": "first"},
        generated_at=timezone.now(),
    )
    AnalysisResult.objects.create(
        analysis_type="overview",
        city=None,
        district=None,
        result_json={"stale": "duplicate"},
        generated_at=timezone.now(),
    )
    AnalysisResult.objects.create(
        analysis_type="city",
        city=first_city,
        district=None,
        result_json={"stale": "city first"},
        generated_at=timezone.now(),
    )
    AnalysisResult.objects.create(
        analysis_type="city",
        city=first_city,
        district=None,
        result_json={"stale": "city duplicate"},
        generated_at=timezone.now(),
    )

    call_command("generate_analysis")

    assert AnalysisResult.objects.filter(
        analysis_type="overview", city=None, district=None
    ).count() == 1
    assert AnalysisResult.objects.filter(
        analysis_type="city", city=first_city, district=None
    ).count() == 1
    for analysis_type in ["overview", "province", "price_buckets", "room_types"]:
        assert AnalysisResult.objects.filter(
            analysis_type=analysis_type, city=None, district=None
        ).count() == 1
    assert AnalysisResult.objects.filter(analysis_type="city").count() == 2

    first_city_result = AnalysisResult.objects.get(
        analysis_type="city", city=first_city, district=None
    )
    second_city_result = AnalysisResult.objects.get(
        analysis_type="city", city=second_city, district=None
    )
    assert first_city_result.result_json["city"] == {
        "id": first_city.id,
        "name": "First City",
    }
    assert second_city_result.result_json["city"] == {
        "id": second_city.id,
        "name": "Second City",
    }
