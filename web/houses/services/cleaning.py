import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.utils import timezone


_NUMBER_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?")
_YEAR_PATTERN = re.compile(r"(19\d{2}|20\d{2})")


def compact_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def compact_room_type(value):
    return re.sub(r"\s+", "", compact_text(value))


def extract_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    match = _NUMBER_PATTERN.search(str(value).replace(",", ""))
    if not match:
        return None
    return float(match.group())


def extract_year(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value if 1900 <= value <= 2099 else None
    match = _YEAR_PATTERN.search(str(value))
    return int(match.group(1)) if match else None


def parse_crawl_time(value):
    if value is None or value == "":
        return timezone.now()
    if isinstance(value, datetime):
        parsed = value
    else:
        text = compact_text(value)
        if not text:
            return timezone.now()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return timezone.now()
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _decimal_from_number(value, places):
    number = extract_float(value)
    if number is None:
        return None
    try:
        decimal_value = Decimal(str(number))
    except InvalidOperation:
        return None
    quantum = Decimal("1").scaleb(-places)
    return decimal_value.quantize(quantum, rounding=ROUND_HALF_UP)


def _optional_decimal(value, places):
    number = extract_float(value)
    if number is None:
        return None
    return _decimal_from_number(value, places)


def _optional_text(record, key):
    return compact_text(record.get(key))


def clean_house_record(record):
    total_price = _decimal_from_number(record.get("total_price"), 2)
    unit_price = _decimal_from_number(record.get("unit_price"), 2)
    area = _decimal_from_number(record.get("area"), 2)

    if total_price is None or unit_price is None or area is None:
        return None
    if total_price <= 0 or area < Decimal("10") or unit_price <= Decimal("1000"):
        return None
    if unit_price > Decimal("200000"):
        return None

    source_url = compact_text(record.get("source_url"))

    return {
        "title": _optional_text(record, "title"),
        "city": _optional_text(record, "city"),
        "district": _optional_text(record, "district"),
        "community": _optional_text(record, "community"),
        "total_price": total_price,
        "unit_price": unit_price,
        "area": area,
        "room_type": compact_room_type(record.get("room_type")),
        "floor": _optional_text(record, "floor"),
        "direction": _optional_text(record, "direction"),
        "decoration": _optional_text(record, "decoration"),
        "build_year": extract_year(record.get("build_year")),
        "address": _optional_text(record, "address"),
        "longitude": _optional_decimal(record.get("longitude"), 6),
        "latitude": _optional_decimal(record.get("latitude"), 6),
        "surrounding": _optional_text(record, "surrounding"),
        "source_url": source_url or None,
        "crawl_time": parse_crawl_time(record.get("crawl_time")),
    }
