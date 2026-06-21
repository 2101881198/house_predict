import json
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from houses.models import City, District, House


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
