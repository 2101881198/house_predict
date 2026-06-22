from django.db.models import Avg, Count, Max, Min, Q
from django.db.models.functions import TruncDate

from houses.models import City, House


def _round(value, digits=2):
    if value is None:
        return 0.0
    return round(float(value), digits)


def build_overview():
    totals = House.objects.aggregate(
        total_houses=Count("id"),
        avg_total_price=Avg("total_price"),
        avg_unit_price=Avg("unit_price"),
    )

    city_distribution = [
        {
            "name": row["city__name"],
            "count": row["count"],
            "avg_unit_price": _round(row["avg_unit_price"]),
        }
        for row in House.objects.values("city__name")
        .annotate(count=Count("id"), avg_unit_price=Avg("unit_price"))
        .order_by("-count", "city__name")
    ]

    hot_districts = [
        {
            "city": row["city__name"],
            "district": row["district__name"],
            "count": row["count"],
            "avg_unit_price": _round(row["avg_unit_price"]),
        }
        for row in House.objects.values("city__name", "district__name")
        .annotate(count=Count("id"), avg_unit_price=Avg("unit_price"))
        .order_by("-count", "city__name", "district__name")[:8]
    ]

    trend = [
        {
            "date": row["date"].isoformat() if row["date"] else "",
            "avg_total_price": _round(row["avg_total_price"]),
            "count": row["count"],
        }
        for row in House.objects.annotate(date=TruncDate("crawl_time"))
        .values("date")
        .annotate(avg_total_price=Avg("total_price"), count=Count("id"))
        .order_by("date")
    ]

    map_points = [
        {
            "title": house.title,
            "city": house.city.name,
            "district": house.district.name,
            "longitude": float(house.longitude),
            "latitude": float(house.latitude),
            "total_price": float(house.total_price),
        }
        for house in House.objects.filter(longitude__isnull=False, latitude__isnull=False)
        .select_related("city", "district")
        .order_by("-crawl_time", "-id")[:200]
    ]

    return {
        "total_houses": totals["total_houses"],
        "city_count": City.objects.count(),
        "avg_total_price": _round(totals["avg_total_price"]),
        "avg_unit_price": _round(totals["avg_unit_price"]),
        "city_distribution": city_distribution,
        "hot_districts": hot_districts,
        "trend": trend,
        "map_points": map_points,
    }


def build_province_stats():
    cities = [
        {
            "city": row["city__name"],
            "count": row["count"],
            "avg_total_price": _round(row["avg_total_price"]),
            "avg_unit_price": _round(row["avg_unit_price"]),
            "max_total_price": _round(row["max_total_price"]),
            "min_total_price": _round(row["min_total_price"]),
        }
        for row in House.objects.values("city", "city__name")
        .annotate(
            count=Count("id"),
            avg_total_price=Avg("total_price"),
            avg_unit_price=Avg("unit_price"),
            max_total_price=Max("total_price"),
            min_total_price=Min("total_price"),
        )
        .order_by("-count", "city__name")
    ]
    return {"cities": cities}


def build_city_stats(city_id):
    city = City.objects.get(id=city_id)
    districts = [
        {
            "id": row["district"],
            "name": row["district__name"],
            "count": row["count"],
            "avg_total_price": _round(row["avg_total_price"]),
            "avg_unit_price": _round(row["avg_unit_price"]),
        }
        for row in House.objects.filter(city=city)
        .values("district", "district__name")
        .annotate(
            count=Count("id"),
            avg_total_price=Avg("total_price"),
            avg_unit_price=Avg("unit_price"),
        )
        .order_by("-count", "district__name")
    ]
    return {"city": {"id": city.id, "name": city.name}, "districts": districts}


def build_price_buckets():
    bucket_specs = [
        ("100万以下", Q(total_price__lt=100)),
        ("100-150万", Q(total_price__gte=100, total_price__lt=150)),
        ("150-200万", Q(total_price__gte=150, total_price__lt=200)),
        ("200-300万", Q(total_price__gte=200, total_price__lt=300)),
        ("300万以上", Q(total_price__gte=300)),
    ]
    aggregate_fields = {
        f"bucket_{index}": Count("id", filter=query)
        for index, (_, query) in enumerate(bucket_specs)
    }
    counts = House.objects.aggregate(**aggregate_fields)
    return [
        {"label": label, "count": counts[f"bucket_{index}"]}
        for index, (label, _) in enumerate(bucket_specs)
    ]


def build_room_type_distribution():
    return [
        {"room_type": row["room_type"], "count": row["count"]}
        for row in House.objects.values("room_type")
        .annotate(count=Count("id"))
        .order_by("-count", "room_type")
    ]


def _scoped_houses(city_id=None):
    queryset = House.objects.all()
    if city_id:
        queryset = queryset.filter(city_id=city_id)
    return queryset


def build_price_buckets(city_id=None):
    queryset = _scoped_houses(city_id)
    bucket_specs = [
        ("100万以下", Q(total_price__lt=100)),
        ("100-150万", Q(total_price__gte=100, total_price__lt=150)),
        ("150-200万", Q(total_price__gte=150, total_price__lt=200)),
        ("200-300万", Q(total_price__gte=200, total_price__lt=300)),
        ("300万以上", Q(total_price__gte=300)),
    ]
    aggregate_fields = {
        f"bucket_{index}": Count("id", filter=query)
        for index, (_, query) in enumerate(bucket_specs)
    }
    counts = queryset.aggregate(**aggregate_fields)
    return [
        {"label": label, "count": counts[f"bucket_{index}"]}
        for index, (label, _) in enumerate(bucket_specs)
    ]


def build_area_buckets(city_id=None):
    queryset = _scoped_houses(city_id)
    bucket_specs = [
        ("60㎡以下", Q(area__lt=60)),
        ("60-90㎡", Q(area__gte=60, area__lt=90)),
        ("90-120㎡", Q(area__gte=90, area__lt=120)),
        ("120-150㎡", Q(area__gte=120, area__lt=150)),
        ("150㎡以上", Q(area__gte=150)),
    ]
    aggregate_fields = {
        f"bucket_{index}": Count("id", filter=query)
        for index, (_, query) in enumerate(bucket_specs)
    }
    counts = queryset.aggregate(**aggregate_fields)
    return [
        {"label": label, "count": counts[f"bucket_{index}"]}
        for index, (label, _) in enumerate(bucket_specs)
    ]


def build_room_type_distribution(city_id=None):
    queryset = _scoped_houses(city_id)
    return [
        {"room_type": row["room_type"], "count": row["count"]}
        for row in queryset.values("room_type")
        .annotate(count=Count("id"))
        .order_by("-count", "room_type")
    ]
