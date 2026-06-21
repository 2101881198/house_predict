import json
from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt

from houses.models import City, CrawlTask, House, PredictResult
from houses.services.analysis import (
    build_city_stats,
    build_overview,
    build_price_buckets,
    build_province_stats,
)
from houses.services.prediction import predict_price


SORT_FIELDS = {
    "total_price",
    "-total_price",
    "unit_price",
    "-unit_price",
    "area",
    "-area",
    "-crawl_time",
}


def ok(data, message="success"):
    return JsonResponse(
        {"code": 200, "message": message, "data": data},
        json_dumps_params={"ensure_ascii": False},
    )


def _number(value):
    if value is None:
        return None
    return float(value)


def _decimal(value):
    try:
        if value in ("", None):
            return None
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _positive_int(value, default, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    if number < 1:
        return default
    if maximum is not None:
        return min(number, maximum)
    return number


def _json_body(request):
    try:
        if not request.body:
            return {}
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _house_dict(house):
    return {
        "id": house.id,
        "title": house.title,
        "city": house.city.name,
        "district": house.district.name,
        "community": house.community,
        "total_price": _number(house.total_price),
        "unit_price": _number(house.unit_price),
        "area": _number(house.area),
        "room_type": house.room_type,
        "floor": house.floor,
        "direction": house.direction,
        "decoration": house.decoration,
        "build_year": house.build_year,
        "address": house.address,
        "longitude": _number(house.longitude),
        "latitude": _number(house.latitude),
        "surrounding": house.surrounding,
        "crawl_time": house.crawl_time.isoformat() if house.crawl_time else "",
    }


def _filter_by_lookup(queryset, field, value):
    if not value:
        return queryset
    if str(value).isdigit():
        return queryset.filter(**{f"{field}_id": int(value)})
    return queryset.filter(**{f"{field}__name": value})


def _filtered_houses(params):
    queryset = House.objects.select_related("city", "district")
    queryset = _filter_by_lookup(queryset, "city", params.get("city"))
    queryset = _filter_by_lookup(queryset, "district", params.get("district"))

    room_type = params.get("room_type")
    if room_type:
        queryset = queryset.filter(room_type=room_type)

    decoration = params.get("decoration")
    if decoration:
        queryset = queryset.filter(decoration=decoration)

    min_price = _decimal(params.get("min_price"))
    if min_price is not None:
        queryset = queryset.filter(total_price__gte=min_price)

    max_price = _decimal(params.get("max_price"))
    if max_price is not None:
        queryset = queryset.filter(total_price__lte=max_price)

    min_area = _decimal(params.get("min_area"))
    if min_area is not None:
        queryset = queryset.filter(area__gte=min_area)

    max_area = _decimal(params.get("max_area"))
    if max_area is not None:
        queryset = queryset.filter(area__lte=max_area)

    sort = params.get("sort") or "-crawl_time"
    if sort not in SORT_FIELDS:
        sort = "-crawl_time"
    return queryset.order_by(sort, "-id")


def _cities_with_districts():
    return City.objects.prefetch_related("districts").order_by("name")


def _room_types():
    return (
        House.objects.exclude(room_type="")
        .values_list("room_type", flat=True)
        .distinct()
        .order_by("room_type")
    )


def dashboard(request):
    return render(
        request,
        "houses/dashboard.html",
        {
            "overview": build_overview(),
            "price_buckets": build_price_buckets(),
        },
    )


def province(request):
    return render(request, "houses/province.html", {"stats": build_province_stats()})


def city_detail(request, city_id):
    get_object_or_404(City, id=city_id)
    return render(request, "houses/city.html", {"stats": build_city_stats(city_id)})


def house_list(request):
    houses = _filtered_houses(request.GET)
    page_size = _positive_int(request.GET.get("page_size"), 10, maximum=50)
    page_number = _positive_int(request.GET.get("page"), 1)
    page_obj = Paginator(houses, page_size).get_page(page_number)
    query_params = request.GET.copy()
    query_params.pop("page", None)
    return render(
        request,
        "houses/house_list.html",
        {
            "page_obj": page_obj,
            "cities": _cities_with_districts(),
            "room_types": _room_types(),
            "querystring": query_params.urlencode(),
        },
    )


def house_detail(request, house_id):
    house = get_object_or_404(
        House.objects.select_related("city", "district"), id=house_id
    )
    similar_houses = (
        House.objects.select_related("city", "district")
        .filter(district=house.district)
        .exclude(id=house.id)
        .order_by("-crawl_time", "-id")[:6]
    )
    district_avg_unit_price = House.objects.filter(district=house.district).aggregate(
        value=Avg("unit_price")
    )["value"]
    return render(
        request,
        "houses/house_detail.html",
        {
            "house": house,
            "similar_houses": similar_houses,
            "district_avg_unit_price": _number(district_avg_unit_price),
        },
    )


def predict_page(request):
    return render(request, "houses/predict.html", {"cities": _cities_with_districts()})


def api_houses(request):
    houses = _filtered_houses(request.GET)
    page_size = _positive_int(request.GET.get("page_size"), 10, maximum=100)
    page_number = _positive_int(request.GET.get("page"), 1)
    paginator = Paginator(houses, page_size)
    page_obj = paginator.get_page(page_number)
    return ok(
        {
            "total": paginator.count,
            "page": page_obj.number,
            "page_size": page_size,
            "items": [_house_dict(house) for house in page_obj.object_list],
        }
    )


def api_house_detail(request, house_id):
    house = get_object_or_404(
        House.objects.select_related("city", "district"), id=house_id
    )
    return ok(_house_dict(house))


def api_overview(request):
    return ok(build_overview())


def api_province(request):
    return ok(build_province_stats())


def api_city(request):
    city_id = _positive_int(request.GET.get("city_id"), None)
    if city_id is None:
        return JsonResponse(
            {"code": 400, "message": "city_id 参数无效", "data": None},
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )
    try:
        data = build_city_stats(city_id)
    except City.DoesNotExist:
        return JsonResponse(
            {"code": 400, "message": "city_id 参数无效", "data": None},
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )
    return ok(data)


@csrf_exempt
def api_predict_price(request):
    if request.method != "POST":
        return JsonResponse(
            {"code": 405, "message": "仅支持 POST", "data": None},
            status=405,
            json_dumps_params={"ensure_ascii": False},
        )
    features = _json_body(request)
    result = predict_price(features)
    PredictResult.objects.create(
        input_features=features,
        predicted_price=Decimal(str(result.get("predicted_price", 0))),
        predicted_unit_price=Decimal(str(result.get("predicted_unit_price", 0))),
        model_name=result.get("model_name", ""),
    )
    return ok(result)


def _crawl_task_dict(task):
    return {
        "id": task.id,
        "task_name": task.task_name,
        "target_city": task.target_city,
        "target_district": task.target_district,
        "page_count": task.page_count,
        "status": task.status,
        "success_count": task.success_count,
        "fail_count": task.fail_count,
        "started_at": task.started_at.isoformat() if task.started_at else "",
        "finished_at": task.finished_at.isoformat() if task.finished_at else "",
        "message": task.message,
        "created_at": task.created_at.isoformat() if task.created_at else "",
    }


@csrf_exempt
def api_crawl_tasks(request):
    if request.method == "GET":
        tasks = CrawlTask.objects.order_by("-created_at")[:100]
        return ok({"items": [_crawl_task_dict(task) for task in tasks]})

    if request.method != "POST":
        return JsonResponse(
            {"code": 405, "message": "仅支持 GET/POST", "data": None},
            status=405,
            json_dumps_params={"ensure_ascii": False},
        )

    data = _json_body(request)
    task = CrawlTask.objects.create(
        task_name=str(data.get("task_name") or "房源采集任务"),
        target_city=str(data.get("target_city") or ""),
        target_district=str(data.get("target_district") or ""),
        page_count=_positive_int(data.get("page_count"), 1),
        status=str(data.get("status") or CrawlTask.Status.PENDING),
    )
    return ok(_crawl_task_dict(task), message="created")
