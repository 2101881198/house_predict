import csv
from pathlib import Path


CITY_MAP_FILES = {
    # 城市名 -> 对应的区县地图 JSON 文件，城市分析页会用它加载地图。
    "济南": "jinan.json",
    "青岛": "qingdao.json",
    "淄博": "zibo.json",
    "烟台": "yantai.json",
    "潍坊": "weifang.json",
    "济宁": "jining.json",
    "泰安": "taian.json",
    "威海": "weihai.json",
    "临沂": "linyi.json",
    "菏泽": "heze.json",
}


def _first_value(row, *keys):
    # CSV 里同一个含义可能有多个列名，这里按优先级取第一个有值的列。
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _normalize_district(value):
    text = str(value or "").strip()
    return text or "未知区域"


def _listing_time(value):
    text = str(value or "").strip()
    if not text:
        return ""
    return f"{text}T00:00:00+08:00"


def teacher_csv_row_to_house_record(row):
    # 把老师提供的 CSV 行转换成项目内部统一的房源字段名。
    city = _first_value(row, "city")
    district = _normalize_district(_first_value(row, "region", "quyu"))
    title = _first_value(row, "mingcheng") or f"{city}{district}房源"
    area = _first_value(row, "mianji_num", "mianji")
    listed_date = _first_value(row, "shijian_dt", "shijian")

    return {
        "title": title,
        "city": city,
        "district": district,
        "community": title,
        "total_price": _first_value(row, "price_num", "price"),
        "unit_price": _first_value(row, "unit_price_num", "unit_price"),
        "area": area,
        "room_type": _first_value(row, "huxing"),
        "floor": _first_value(row, "louceng"),
        "direction": _first_value(row, "chaoxiang"),
        "decoration": _first_value(row, "zhuangxiu"),
        "build_year": "",
        "address": " ".join(part for part in [city, district, title] if part),
        "longitude": _first_value(row, "upper_price"),
        "latitude": _first_value(row, "lower_price"),
        "surrounding": _first_value(row, "dingwei", "yongtu"),
        "source_url": f"teacher://{city}/{district}/{title}/{listed_date}/{area}",
        "crawl_time": _listing_time(listed_date),
    }


def iter_teacher_house_records(path):
    # 逐行读取 CSV，并把每一行转换成内部房源记录。
    with Path(path).open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            yield teacher_csv_row_to_house_record(row)
