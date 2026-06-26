import json
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from houses.models import City, CrawlTask, District, House, PredictResult


@pytest.mark.django_db
def test_houses_api_returns_paginated_items(client):
    city = City.objects.create(name="济南")
    district = District.objects.create(city=city, name="历下")
    House.objects.create(
        title="历下核心两室",
        city=city,
        district=district,
        community="泉城花园",
        total_price=Decimal("210.00"),
        unit_price=Decimal("30000.00"),
        area=Decimal("70.00"),
        room_type="两室一厅",
        floor="中楼层",
        direction="南北",
        decoration="精装",
        build_year=2015,
        crawl_time=timezone.now(),
    )

    response = client.get(reverse("houses:api_houses"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["total"] == 1
    assert payload["data"]["items"][0]["title"] == "历下核心两室"


@pytest.mark.django_db
def test_predict_api_returns_price(client, settings, tmp_path):
    settings.MODEL_DIR = tmp_path / "missing-models"

    response = client.post(
        reverse("houses:api_predict_price"),
        data=json.dumps({"area": 90}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert "predicted_price" in response.json()["data"]


@pytest.mark.django_db
def test_predict_api_returns_chart_comparison_data(client, settings, tmp_path):
    settings.MODEL_DIR = tmp_path / "missing-models"
    city = City.objects.create(name="济南")
    district = District.objects.create(city=city, name="历下")
    House.objects.create(
        title="历下参考房源",
        city=city,
        district=district,
        community="泉城花园",
        total_price=Decimal("200.00"),
        unit_price=Decimal("20000.00"),
        area=Decimal("100.00"),
        room_type="两室一厅",
        floor="中楼层",
        direction="南北",
        decoration="精装",
        build_year=2015,
        crawl_time=timezone.now(),
    )

    response = client.post(
        reverse("houses:api_predict_price"),
        data=json.dumps({"city": "济南", "district": "历下", "area": 100}),
        content_type="application/json",
    )

    assert response.status_code == 200
    comparison = response.json()["data"]["comparison"]
    assert comparison[0] == {"label": "预测总价", "value": 200.0}
    assert {"label": "区域均价估算", "value": 200.0} in comparison
    assert {"label": "城市均价估算", "value": 200.0} in comparison


@pytest.mark.django_db
def test_predict_page_shows_recent_prediction_records(client):
    PredictResult.objects.create(
        input_features={"city": "济南", "area": 90},
        predicted_price=Decimal("180.00"),
        predicted_unit_price=Decimal("20000.00"),
        model_name="规则估算",
    )

    response = client.get(reverse("houses:predict"))

    assert response.status_code == 200
    assert "最近预测记录".encode() in response.content
    assert b"180.00" in response.content


@pytest.mark.django_db
def test_houses_api_rejects_post(client):
    response = client.post(reverse("houses:api_houses"))

    assert response.status_code == 405


@pytest.mark.django_db
@pytest.mark.parametrize("querystring", ["", "?city_id=abc"])
def test_city_api_requires_valid_city_id(client, querystring):
    response = client.get(f"{reverse('houses:api_city')}{querystring}")

    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == 400


@pytest.mark.django_db
def test_predict_api_rejects_malformed_json_without_creating_result(
    client, settings, tmp_path
):
    settings.MODEL_DIR = tmp_path / "missing-models"

    response = client.post(
        reverse("houses:api_predict_price"),
        data="{bad json",
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["code"] == 400
    assert PredictResult.objects.count() == 0


@pytest.mark.django_db
def test_houses_api_rejects_nan_numeric_filter(client):
    response = client.get(reverse("houses:api_houses"), {"min_price": "NaN"})

    assert response.status_code == 400
    assert response.json()["code"] == 400


@pytest.mark.django_db
def test_crawl_tasks_requires_staff_auth(client):
    response = client.get(reverse("houses:api_crawl_tasks"))

    assert response.status_code == 403
    assert response.json()["code"] == 403


@pytest.mark.django_db
def test_staff_can_create_crawl_task_with_capped_page_count(client):
    user = get_user_model().objects.create_user(
        username="staff", password="secret", is_staff=True
    )
    client.force_login(user)

    response = client.post(
        reverse("houses:api_crawl_tasks"),
        data=json.dumps(
            {
                "task_name": "crawl",
                "target_city": "Jinan",
                "page_count": 999,
                "status": CrawlTask.Status.PENDING,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload["data"]) == {"id", "status"}
    assert payload["data"]["status"] == CrawlTask.Status.PENDING
    task = CrawlTask.objects.get()
    assert payload["data"]["id"] == task.id
    assert task.task_name == "crawl"
    assert task.page_count == 100
