import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import isfinite

from django.utils import timezone


_NUMBER_PATTERN = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
_YEAR_PATTERN = re.compile(r"(19\d{2}|20\d{2})")


def compact_text(value):
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def compact_room_type(value):
    return re.sub(r"\s+", "", compact_text(value))


def parse_decimal_value(value):
    if value is None:
        return None
    if isinstance(value, bool):
        text = str(int(value))
    elif isinstance(value, float):
        if not isfinite(value):
            return None
        text = str(value)
    elif isinstance(value, (int, Decimal)):
        text = str(value)
    else:
        match = _NUMBER_PATTERN.search(str(value).replace(",", ""))
        if not match:
            return None
        text = match.group()
    try:
        decimal_value = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    try:
        return decimal_value if decimal_value.is_finite() else None
    except InvalidOperation:
        return None


def extract_float(value):
    decimal_value = parse_decimal_value(value)
    if decimal_value is None:
        return None
    try:
        return float(decimal_value)
    except (OverflowError, ValueError):
        return None


def has_explicit_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(compact_text(value))
    return True


def quantize_decimal(decimal_value, places):
    try:
        if decimal_value is None or not decimal_value.is_finite():
            return None
    except InvalidOperation:
        return None
    quantum = Decimal("1").scaleb(-places)
    try:
        return decimal_value.quantize(quantum, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None


def decimal_lte(left, right):
    try:
        return left <= right
    except InvalidOperation:
        return True


def decimal_lt(left, right):
    try:
        return left < right
    except InvalidOperation:
        return True


def decimal_gt(left, right):
    try:
        return left > right
    except InvalidOperation:
        return True


def extract_year(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value if 1900 <= value <= 2099 else None
    match = _YEAR_PATTERN.search(str(value))
    if not match:
        return None
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
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def _decimal_from_number(value, places):
    return quantize_decimal(parse_decimal_value(value), places)


def _optional_decimal(value, places):
    if not has_explicit_value(value):
        return None
    return quantize_decimal(parse_decimal_value(value), places)


def _optional_text(record, key):
    return compact_text(record.get(key))


def clean_house_record(record):
    total_price = _decimal_from_number(record.get("total_price"), 2)
    unit_price = _decimal_from_number(record.get("unit_price"), 2)
    area = _decimal_from_number(record.get("area"), 2)
    longitude = _optional_decimal(record.get("longitude"), 6)
    latitude = _optional_decimal(record.get("latitude"), 6)
    crawl_time = parse_crawl_time(record.get("crawl_time"))

    if total_price is None or unit_price is None or area is None:
        return None
    if has_explicit_value(record.get("longitude")) and longitude is None:
        return None
    if has_explicit_value(record.get("latitude")) and latitude is None:
        return None
    if crawl_time is None:
        return None
    if (
        decimal_lte(total_price, Decimal("0"))
        or decimal_lt(area, Decimal("10"))
        or decimal_lte(unit_price, Decimal("1000"))
    ):
        return None
    if decimal_gt(unit_price, Decimal("200000")):
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
        "longitude": longitude,
        "latitude": latitude,
        "surrounding": _optional_text(record, "surrounding"),
        "source_url": source_url or None,
        "crawl_time": crawl_time,
    }
