from collections import defaultdict

from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone

from houses.models import City, House


def _round(value, digits=2):
    # 数据库聚合结果可能是 None；图表接口里统一用 0.0，避免前端报错。
    if value is None:
        return 0.0
    return round(float(value), digits)


def _build_price_trend(rows):
    # 按季度分组，计算每 3 个月的平均总价，让长时间跨度趋势图更清晰。
    grouped = defaultdict(lambda: {"total": 0, "count": 0})

    for row in rows:
        crawl_time = row["crawl_time"]
        if crawl_time is None:
            continue
        if timezone.is_aware(crawl_time):
            crawl_time = timezone.localtime(crawl_time)
        quarter = ((crawl_time.month - 1) // 3) + 1
        date_key = f"{crawl_time.year} Q{quarter}"
        grouped[date_key]["total"] += row["total_price"]
        grouped[date_key]["count"] += 1

    return [
        {
            "date": date_key,
            "avg_total_price": _round(values["total"] / values["count"]),
            "count": values["count"],
        }
        for date_key, values in sorted(grouped.items())
    ]


def _build_city_price_trends(limit=5):
    city_rows = (
        House.objects.values("city", "city__name")
        .annotate(count=Count("id"))
        .order_by("-count", "city__name")[:limit]
    )

    return [
        {
            "city": row["city__name"],
            "trend": _build_price_trend(
                House.objects.filter(city_id=row["city"]).values(
                    "crawl_time", "total_price"
                )
            ),
        }
        for row in city_rows
    ]


def build_overview():
    # 首页总览数据：总房源数、城市数、均价、城市分布、热门区县和地图点。
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

    city_price_rankings = [
        {
            "city": row["city__name"],
            "count": row["count"],
            "avg_total_price": _round(row["avg_total_price"]),
            "avg_unit_price": _round(row["avg_unit_price"]),
        }
        for row in House.objects.values("city__name")
        .annotate(
            count=Count("id"),
            avg_total_price=Avg("total_price"),
            avg_unit_price=Avg("unit_price"),
        )
        .order_by("-avg_unit_price", "-count", "city__name")[:10]
    ]

    trend = _build_price_trend(House.objects.values("crawl_time", "total_price"))
    city_price_trends = _build_city_price_trends()

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
        "city_price_rankings": city_price_rankings,
        "trend": trend,
        "city_price_trends": city_price_trends,
        "map_points": map_points,
    }


def build_province_stats():
    # 省级统计：按城市汇总房源数量、平均价、最高价、最低价。
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
    # 城市统计：按区县汇总某个城市内的房源数量和均价。
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


def build_city_stats(city_id):
    city = City.objects.get(id=city_id)
    queryset = House.objects.filter(city=city)
    totals = queryset.aggregate(
        total_houses=Count("id"),
        avg_total_price=Avg("total_price"),
        avg_unit_price=Avg("unit_price"),
    )
    districts = [
        {
            "id": row["district"],
            "name": row["district__name"],
            "count": row["count"],
            "avg_total_price": _round(row["avg_total_price"]),
            "avg_unit_price": _round(row["avg_unit_price"]),
        }
        for row in queryset.values("district", "district__name")
        .annotate(
            count=Count("id"),
            avg_total_price=Avg("total_price"),
            avg_unit_price=Avg("unit_price"),
        )
        .order_by("-count", "district__name")
    ]
    return {
        "city": {"id": city.id, "name": city.name},
        "summary": {
            "total_houses": totals["total_houses"],
            "district_count": queryset.values("district").distinct().count(),
            "avg_total_price": _round(totals["avg_total_price"]),
            "avg_unit_price": _round(totals["avg_unit_price"]),
        },
        "districts": districts,
        "trend": _build_price_trend(queryset.values("crawl_time", "total_price")),
    }


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
    # 统计图表可看全省，也可只看某个城市；这里统一处理范围。
    queryset = House.objects.all()
    if city_id:
        queryset = queryset.filter(city_id=city_id)
    return queryset


def build_price_buckets(city_id=None):
    # 总价区间分布：统计不同价格段里有多少套房源。
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
    # 面积区间分布：统计不同面积段里有多少套房源。
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
    # 户型分布：统计两室一厅、三室一厅等户型数量。
    queryset = _scoped_houses(city_id)
    return [
        {"room_type": row["room_type"], "count": row["count"]}
        for row in queryset.values("room_type")
        .annotate(count=Count("id"))
        .order_by("-count", "room_type")
    ]


def build_decoration_distribution(city_id=None):
    queryset = _scoped_houses(city_id).exclude(decoration="")
    return [
        {"decoration": row["decoration"], "count": row["count"]}
        for row in queryset.values("decoration")
        .annotate(count=Count("id"))
        .order_by("-count", "decoration")
    ]
