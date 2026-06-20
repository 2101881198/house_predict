from decimal import Decimal

import pytest
from django.utils import timezone

from houses.models import City, District, House


@pytest.mark.django_db
def test_house_str_uses_city_and_title():
    city = City.objects.create(name="济南")
    district = District.objects.create(city=city, name="历下")
    house = House.objects.create(
        title="历下核心两室",
        city=city,
        district=district,
        total_price=Decimal("210.00"),
        unit_price=Decimal("30000.00"),
        area=Decimal("70.00"),
        room_type="两室",
        crawl_time=timezone.now(),
    )

    assert str(house) == "济南 历下核心两室"
