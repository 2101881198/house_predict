from decimal import Decimal

from django.utils import timezone

from houses.services.cleaning import clean_house_record


def test_clean_house_record_normalizes_numbers_text_room_type_and_build_year():
    cleaned = clean_house_record(
        {
            "title": "  济南   历下 核心两室  ",
            "city": " 济南 ",
            "district": " 历下区 ",
            "community": "  泉城 小区 ",
            "total_price": "180万",
            "unit_price": "22500元/平",
            "area": "80㎡",
            "room_type": " 2 室 1 厅 ",
            "floor": " 中楼层 ",
            "direction": " 南 北 ",
            "decoration": " 精装 ",
            "build_year": "建成于2015年",
            "address": " 历下区 经十路 ",
            "longitude": "117.1234567",
            "latitude": "36.6543219",
            "surrounding": " 地铁  学校 ",
            "source_url": " demo://house/jinan-001 ",
            "crawl_time": "2026-06-20T10:30:00+08:00",
        }
    )

    assert cleaned is not None
    assert cleaned["title"] == "济南 历下 核心两室"
    assert cleaned["community"] == "泉城 小区"
    assert cleaned["total_price"] == Decimal("180.00")
    assert cleaned["unit_price"] == Decimal("22500.00")
    assert cleaned["area"] == Decimal("80.00")
    assert cleaned["room_type"] == "2室1厅"
    assert cleaned["build_year"] == 2015
    assert cleaned["longitude"] == Decimal("117.123457")
    assert cleaned["latitude"] == Decimal("36.654322")
    assert cleaned["surrounding"] == "地铁 学校"
    assert cleaned["source_url"] == "demo://house/jinan-001"
    assert timezone.is_aware(cleaned["crawl_time"])


def test_clean_house_record_returns_none_for_invalid_area():
    cleaned = clean_house_record(
        {
            "title": "无效面积",
            "city": "济南",
            "district": "历下区",
            "community": "泉城小区",
            "total_price": "180万",
            "unit_price": "22500元/平",
            "area": "9.9㎡",
            "room_type": "1室1厅",
            "crawl_time": "2026-06-20T10:30:00+08:00",
        }
    )

    assert cleaned is None


def test_clean_house_record_normalizes_blank_source_url_to_none():
    cleaned = clean_house_record(
        {
            "title": "空白来源",
            "city": "青岛",
            "district": "市南区",
            "community": "海景小区",
            "total_price": "260万",
            "unit_price": "32000元/平",
            "area": "81㎡",
            "room_type": "2室1厅",
            "source_url": "   \t  ",
            "crawl_time": "2026-06-20T10:30:00+08:00",
        }
    )

    assert cleaned is not None
    assert cleaned["source_url"] is None
