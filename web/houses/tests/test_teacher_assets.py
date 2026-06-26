from decimal import Decimal
from pathlib import Path

import pytest
from django.test import Client
from django.utils import timezone

from houses.models import City, District, House


def sample_teacher_row(**overrides):
    row = {
        "city": "济南",
        "region": "历下区",
        "mingcheng": "泉城花园",
        "quyu": "历下区",
        "huxing": "3室2厅1厨1卫",
        "louceng": "中楼层",
        "mianji": "108.5㎡",
        "chaoxiang": "南北",
        "zhuangxiu": "精装",
        "shijian_dt": "2023-05-03",
        "price_num": "220.0",
        "unit_price_num": "20276.0",
        "mianji_num": "108.5",
        "lower_price": "36.65",
        "upper_price": "117.05",
        "dingwei": "高端小区",
    }
    row.update(overrides)
    return row


def test_teacher_csv_row_maps_to_clean_house_record_shape():
    from houses.services.teacher_data import teacher_csv_row_to_house_record

    record = teacher_csv_row_to_house_record(sample_teacher_row())

    assert record == {
        "title": "泉城花园",
        "city": "济南",
        "district": "历下区",
        "community": "泉城花园",
        "total_price": "220.0",
        "unit_price": "20276.0",
        "area": "108.5",
        "room_type": "3室2厅1厨1卫",
        "floor": "中楼层",
        "direction": "南北",
        "decoration": "精装",
        "build_year": "",
        "address": "济南 历下区 泉城花园",
        "longitude": "117.05",
        "latitude": "36.65",
        "surrounding": "高端小区",
        "source_url": "teacher://济南/历下区/泉城花园/2023-05-03/108.5",
        "crawl_time": "2023-05-03T00:00:00+08:00",
    }


def test_teacher_csv_row_uses_price_and_area_fallback_columns():
    from houses.services.teacher_data import teacher_csv_row_to_house_record

    record = teacher_csv_row_to_house_record(
        sample_teacher_row(
            price_num="",
            unit_price_num="",
            mianji_num="",
            price="220.0",
            unit_price="20276",
            mianji="108.5㎡",
        )
    )

    assert record["total_price"] == "220.0"
    assert record["unit_price"] == "20276"
    assert record["area"] == "108.5㎡"


@pytest.mark.django_db
def test_analysis_pages_include_teacher_map_containers_and_metadata():
    city = City.objects.create(name="济南")
    district = District.objects.create(city=city, name="历下区")
    House.objects.create(
        title="Map house",
        city=city,
        district=district,
        total_price=Decimal("220.00"),
        unit_price=Decimal("20276.00"),
        area=Decimal("108.50"),
        room_type="3室2厅",
        longitude=Decimal("117.050000"),
        latitude=Decimal("36.650000"),
        crawl_time=timezone.now(),
    )

    client = Client()
    province_response = client.get("/province/")
    city_response = client.get(f"/cities/{city.id}/")

    assert province_response.status_code == 200
    assert b'province-map-chart' in province_response.content
    assert b'teacher-map-meta' in province_response.content
    assert city_response.status_code == 200
    assert b'city-map-chart' in city_response.content
    assert b'teacher-map-meta' in city_response.content


@pytest.mark.django_db
def test_base_layout_includes_current_time_display(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'id="current-time"' in response.content


@pytest.mark.django_db
def test_dashboard_focuses_on_shandong_province_overview(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "山东省房源总览".encode() in response.content
    for chart_id in [
        b'area-chart',
        b'room-chart',
        b'decoration-chart',
        b'city-price-chart',
    ]:
        assert chart_id in response.content
    assert b'district-chart' not in response.content
    assert b'area-buckets-data' in response.content
    assert b'room-types-data' in response.content
    assert b'decoration-data' in response.content


@pytest.mark.django_db
def test_dashboard_uses_versioned_chart_script_to_avoid_stale_cache(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b'houses/js/charts.js?v=' in response.content
    assert b'houses/css/app.css?v=' in response.content


def test_room_type_charts_use_ranked_horizontal_bars():
    chart_script = Path("web/static/houses/js/charts.js").read_text(encoding="utf-8")

    assert "function formatCompactNumber" in chart_script
    assert "function renderTopHorizontalChart" in chart_script
    assert "label: {show: true" in chart_script
    assert 'renderTopHorizontalChart("room-chart"' in chart_script
    assert 'renderTopHorizontalChart("province-room-chart"' in chart_script
    assert 'renderTopHorizontalChart("city-room-chart"' in chart_script
    assert 'renderPieChart("room-chart"' not in chart_script
    assert 'renderPieChart("province-room-chart"' not in chart_script
    assert 'renderPieChart("city-room-chart"' not in chart_script


def test_price_bucket_charts_use_distribution_bars_with_numbers():
    chart_script = Path("web/static/houses/js/charts.js").read_text(encoding="utf-8")

    assert "function renderDistributionBarChart" in chart_script
    assert "function formatPercent" in chart_script
    assert 'renderDistributionBarChart("price-chart"' in chart_script
    assert 'renderDistributionBarChart("province-price-chart"' in chart_script
    assert 'renderDistributionBarChart("city-price-chart"' in chart_script
    assert 'renderPieChart("price-chart"' not in chart_script
    assert 'renderPieChart("province-price-chart"' not in chart_script
    assert 'renderPieChart("city-price-chart"' not in chart_script


def test_horizontal_distribution_charts_hide_crowded_x_axis_labels():
    chart_script = Path("web/static/houses/js/charts.js").read_text(encoding="utf-8")

    assert "function hiddenValueAxis" in chart_script
    assert "axisLabel: {show: false}" in chart_script
    assert "axisLine: {show: false}" in chart_script
    assert "axisTick: {show: false}" in chart_script


def test_chart_script_renders_city_price_trends():
    chart_script = Path("web/static/houses/js/charts.js").read_text(encoding="utf-8")

    assert "function renderMultiLineChart" in chart_script
    assert 'renderMultiLineChart("city-comparison-trend-chart"' in chart_script
    assert '"city-trend-chart"' in chart_script


@pytest.mark.django_db
def test_dashboard_exposes_visible_hierarchy_navigation(client):
    city = City.objects.create(name="济南")
    District.objects.create(city=city, name="历下区")

    response = client.get("/")

    assert response.status_code == 200
    assert "城市对比".encode() in response.content
    assert "山东省房源".encode() in response.content
    assert "进入地级市分析".encode() not in response.content
    assert b"analysis-sidebar" in response.content
    assert b"sidebar-city-link" in response.content
    assert f'/cities/{city.id}/'.encode() in response.content


@pytest.mark.django_db
def test_dashboard_and_city_pages_include_city_price_trend_charts(client):
    city = City.objects.create(name="Trend City")
    district = District.objects.create(city=city, name="Trend District")
    House.objects.create(
        title="Trend chart house",
        city=city,
        district=district,
        total_price=Decimal("180.00"),
        unit_price=Decimal("20000.00"),
        area=Decimal("90.00"),
        room_type="3 bed",
        crawl_time=timezone.now(),
    )

    dashboard_response = client.get("/")
    city_response = client.get(f"/cities/{city.id}/")

    assert dashboard_response.status_code == 200
    assert b'city-comparison-trend-chart' in dashboard_response.content
    assert b'city_price_trends' in dashboard_response.content
    assert city_response.status_code == 200
    assert b'city-trend-chart' in city_response.content
    assert b'"trend"' in city_response.content


@pytest.mark.django_db
def test_city_page_includes_city_level_summary_and_decoration_chart(client):
    city = City.objects.create(name="济南")
    district = District.objects.create(city=city, name="历下区")
    House.objects.create(
        title="City chart house",
        city=city,
        district=district,
        total_price=Decimal("180.00"),
        unit_price=Decimal("20000.00"),
        area=Decimal("90.00"),
        room_type="3室2厅",
        decoration="精装",
        crawl_time=timezone.now(),
    )

    response = client.get(f"/cities/{city.id}/")

    assert response.status_code == 200
    assert "济南市房源分析".encode() in response.content
    assert b'city-decoration-chart' in response.content
    assert b'city-decoration-data' in response.content
