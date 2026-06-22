import json
from decimal import Decimal, InvalidOperation
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods

from houses.models import City, CrawlTask, House, PredictResult
from houses.services.analysis import (
    build_area_buckets,
    build_city_stats,
    build_overview,
    build_price_buckets,
    build_province_stats,
    build_room_type_distribution,
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


def error_response(code, message, status):
    return JsonResponse(
        {"code": code, "message": message, "data": None},
        status=status,
        json_dumps_params={"ensure_ascii": False},
    )


def bad_request(message):
    return error_response(400, message, 400)


def forbidden(message="Forbidden"):
    return error_response(403, message, 403)


class BadRequest(ValueError):
    pass


def _number(value):
    if value is None:
        return None
    return float(value)


def _decimal(value, field_name="value", strict=False):
    try:
        if value in ("", None):
            return None
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        if strict:
            raise BadRequest(f"{field_name} parameter is invalid")
        return None
    if not parsed.is_finite():
        if strict:
            raise BadRequest(f"{field_name} parameter is invalid")
        return None
    return parsed


def _positive_int(value, default, maximum=None, field_name="value", strict=False):
    try:
        if value in ("", None):
            return default
        number = int(value)
    except (TypeError, ValueError):
        if strict:
            raise BadRequest(f"{field_name} parameter is invalid")
        return default
    if number < 1:
        if strict:
            raise BadRequest(f"{field_name} parameter is invalid")
        return default
    if maximum is not None:
        return min(number, maximum)
    return number


def _json_body(request):
    try:
        if not request.body:
            return {}, None
        data = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, bad_request("Malformed JSON body")
    if not isinstance(data, dict):
        return None, bad_request("JSON body must be an object")
    return data, None


def _quantized_result_decimal(value, field_name):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise BadRequest(f"{field_name} is invalid")
    if not parsed.is_finite():
        raise BadRequest(f"{field_name} is invalid")
    try:
        return parsed.quantize(Decimal("0.01"))
    except InvalidOperation:
        raise BadRequest(f"{field_name} is invalid")


def _clean_text(data, field_name, default, max_length):
    value = data.get(field_name, default)
    if value in ("", None):
        value = default
    value = str(value)
    if len(value) > max_length:
        raise BadRequest(f"{field_name} is too long")
    return value


def staff_required_json(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return forbidden()
        return view_func(request, *args, **kwargs)

    return wrapper


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


def _filtered_houses(params, strict=False):
    queryset = House.objects.select_related("city", "district")
    queryset = _filter_by_lookup(queryset, "city", params.get("city"))
    queryset = _filter_by_lookup(queryset, "district", params.get("district"))

    room_type = params.get("room_type")
    if room_type:
        queryset = queryset.filter(room_type=room_type)

    decoration = params.get("decoration")
    if decoration:
        queryset = queryset.filter(decoration=decoration)

    min_price = _decimal(params.get("min_price"), "min_price", strict=strict)
    if min_price is not None:
        queryset = queryset.filter(total_price__gte=min_price)

    max_price = _decimal(params.get("max_price"), "max_price", strict=strict)
    if max_price is not None:
        queryset = queryset.filter(total_price__lte=max_price)

    min_area = _decimal(params.get("min_area"), "min_area", strict=strict)
    if min_area is not None:
        queryset = queryset.filter(area__gte=min_area)

    max_area = _decimal(params.get("max_area"), "max_area", strict=strict)
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
    return render(
        request,
        "houses/province.html",
        {
            "stats": build_province_stats(),
            "price_buckets": build_price_buckets(),
            "area_buckets": build_area_buckets(),
            "room_types": build_room_type_distribution(),
        },
    )


def city_detail(request, city_id):
    get_object_or_404(City, id=city_id)
    return render(
        request,
        "houses/city.html",
        {
            "stats": build_city_stats(city_id),
            "price_buckets": build_price_buckets(city_id),
            "area_buckets": build_area_buckets(city_id),
            "room_types": build_room_type_distribution(city_id),
        },
    )


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


@require_GET
def api_houses(request):
    try:
        houses = _filtered_houses(request.GET, strict=True)
    except BadRequest as exc:
        return bad_request(str(exc))
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


@require_GET
def api_house_detail(request, house_id):
    house = get_object_or_404(
        House.objects.select_related("city", "district"), id=house_id
    )
    return ok(_house_dict(house))


@require_GET
def api_overview(request):
    return ok(build_overview())


@require_GET
def api_province(request):
    return ok(build_province_stats())


@require_GET
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
    features, json_error = _json_body(request)
    if json_error is not None:
        return json_error
    result = predict_price(features)
    try:
        predicted_price = _quantized_result_decimal(
            result.get("predicted_price"), "predicted_price"
        )
        predicted_unit_price = _quantized_result_decimal(
            result.get("predicted_unit_price"), "predicted_unit_price"
        )
    except BadRequest as exc:
        return bad_request(str(exc))
    PredictResult.objects.create(
        input_features=features,
        predicted_price=predicted_price,
        predicted_unit_price=predicted_unit_price,
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


@staff_required_json
@login_required
@require_http_methods(["GET", "POST"])
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

    data, json_error = _json_body(request)
    if json_error is not None:
        return json_error
    try:
        _clean_text(data, "task_name", "house crawl task", 100)
        _clean_text(data, "target_city", "", 50)
        _clean_text(data, "target_district", "", 50)
        status = str(data.get("status") or CrawlTask.Status.PENDING)
        if status not in CrawlTask.Status.values:
            raise BadRequest("status is invalid")
        page_count = _positive_int(
            data.get("page_count"),
            1,
            maximum=100,
            field_name="page_count",
            strict=True,
        )
    except BadRequest as exc:
        return bad_request(str(exc))
    task = CrawlTask.objects.create(
        task_name=str(data.get("task_name") or "房源采集任务"),
        target_city=str(data.get("target_city") or ""),
        target_district=str(data.get("target_district") or ""),
        page_count=page_count,
        status=status,
    )
    return ok({"id": task.id, "status": task.status})
