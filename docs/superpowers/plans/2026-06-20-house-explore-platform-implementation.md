# House Explore Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Django + MySQL智慧房源探索平台 with demo data, cleaning, analysis, prediction, pages, APIs, admin, and documentation.

**Architecture:** Use a Django single-project application under `web/`, with a focused `houses` app for ORM models, views, APIs, management commands, and tests. Keep reusable data cleaning, analysis, and prediction logic in small service modules so pages, APIs, and commands share the same behavior.

**Tech Stack:** Python 3.10+, Django, MySQL/mysqlclient, pandas, scikit-learn, joblib, ECharts, pytest.

---

## File Structure

- Create `requirements.txt`: Python dependencies.
- Create `.env.example`: MySQL and Django configuration template.
- Create `README.md`: setup, database creation, commands, and run instructions.
- Create `scripts/sql/create_database.sql`: MySQL database bootstrap.
- Create `web/manage.py`: Django entry point.
- Create `web/house_platform/settings.py`: Django settings using environment variables.
- Create `web/house_platform/urls.py`: project URL routing.
- Create `web/houses/models.py`: City, District, House, CrawlTask, AnalysisResult, PredictResult.
- Create `web/houses/admin.py`: Django Admin registration.
- Create `web/houses/services/cleaning.py`: data normalization and validation.
- Create `web/houses/services/analysis.py`: aggregate statistics for dashboard and APIs.
- Create `web/houses/services/prediction.py`: train/load/predict price models with rule fallback.
- Create `web/houses/sample_data.py`: deterministic Shandong demo listings.
- Create `web/houses/management/commands/seed_demo_data.py`: import cleaned demo data.
- Create `web/houses/management/commands/generate_analysis.py`: store precomputed analysis JSON.
- Create `web/houses/management/commands/train_price_model.py`: train and persist price model.
- Create `web/houses/management/commands/run_demo_crawler.py`: create a sample crawl task and seed data.
- Create `web/houses/views.py`: HTML pages and JSON API views.
- Create `web/houses/urls.py`: app URL routing.
- Create `web/templates/houses/*.html`: dashboard, province, city, list, detail, predict pages.
- Create `web/static/houses/css/app.css`: restrained dashboard UI.
- Create `web/static/houses/js/charts.js`: ECharts initialization helpers.
- Create `web/houses/tests/*.py`: tests for cleaning, analysis, prediction fallback, and API smoke behavior.

## Task 1: Project Scaffold And Configuration

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `scripts/sql/create_database.sql`
- Create: `web/manage.py`
- Create: `web/house_platform/__init__.py`
- Create: `web/house_platform/settings.py`
- Create: `web/house_platform/urls.py`
- Create: `web/house_platform/wsgi.py`
- Create: `web/houses/__init__.py`
- Create: `web/houses/apps.py`
- Create: `web/houses/urls.py`
- Create: `web/templates/houses/base.html`
- Create: `web/static/houses/css/app.css`

- [ ] **Step 1: Create dependency and environment files**

Create `requirements.txt`:

```text
Django==5.0.6
mysqlclient==2.2.4
python-dotenv==1.0.1
pandas==2.2.2
numpy==1.26.4
scikit-learn==1.5.0
joblib==1.4.2
pytest==8.2.2
pytest-django==4.8.0
```

Create `.env.example`:

```text
DJANGO_SECRET_KEY=dev-secret-key-change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
MYSQL_DATABASE=house_predict
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
```

Create `scripts/sql/create_database.sql`:

```sql
CREATE DATABASE IF NOT EXISTS house_predict
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
```

- [ ] **Step 2: Create Django entry point and settings**

Create `web/manage.py`:

```python
#!/usr/bin/env python
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "house_platform.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
```

Create `web/house_platform/settings.py`:

```python
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(ROOT_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "houses",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "house_platform.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "house_platform.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("MYSQL_DATABASE", "house_predict"),
        "USER": os.getenv("MYSQL_USER", "root"),
        "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
        "HOST": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("MYSQL_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MODEL_DIR = BASE_DIR / "models"
```

Create `web/house_platform/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("houses.urls")),
]
```

Create `web/house_platform/wsgi.py`:

```python
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "house_platform.settings")
application = get_wsgi_application()
```

- [ ] **Step 3: Create app shell and base template**

Create `web/houses/apps.py`:

```python
from django.apps import AppConfig


class HousesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "houses"
    verbose_name = "房源管理"
```

Create `web/houses/urls.py`:

```python
from django.urls import path

from . import views

app_name = "houses"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
]
```

Create `web/templates/houses/base.html`:

```html
{% load static %}
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}智慧房源探索平台{% endblock %}</title>
  <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
  <link rel="stylesheet" href="{% static 'houses/css/app.css' %}">
</head>
<body>
  <nav class="topbar">
    <a href="{% url 'houses:dashboard' %}" class="brand">智慧房源探索平台</a>
  </nav>
  <main class="page">
    {% block content %}{% endblock %}
  </main>
  {% block scripts %}{% endblock %}
</body>
</html>
```

Create `web/static/houses/css/app.css`:

```css
:root {
  color-scheme: light;
  --bg: #f6f7fb;
  --panel: #ffffff;
  --text: #172033;
  --muted: #687386;
  --line: #dfe4ec;
  --accent: #2563eb;
  --good: #059669;
  --warn: #d97706;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
}

.topbar {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 28px;
  background: #ffffff;
  border-bottom: 1px solid var(--line);
}

.brand {
  color: var(--text);
  font-weight: 700;
  text-decoration: none;
}

.page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px;
}

.grid {
  display: grid;
  gap: 16px;
}

.stats-grid {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 16px;
}

.panel h2,
.panel h3 {
  margin: 0 0 12px;
  font-size: 18px;
}

.metric {
  font-size: 28px;
  font-weight: 760;
}

.muted {
  color: var(--muted);
}

.chart {
  width: 100%;
  height: 320px;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th,
.table td {
  border-bottom: 1px solid var(--line);
  padding: 10px 8px;
  text-align: left;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
  align-items: end;
}

input,
select,
button {
  width: 100%;
  min-height: 38px;
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 8px 10px;
  font: inherit;
}

button,
.button {
  background: var(--accent);
  color: #ffffff;
  border-color: var(--accent);
  cursor: pointer;
  text-align: center;
  text-decoration: none;
}
```

- [ ] **Step 4: Run Django check**

Run:

```powershell
python web/manage.py check
```

Expected: command reaches Django import successfully. It may fail before models exist with `module 'houses.views' has no attribute 'dashboard'`; Task 2 creates the view.

- [ ] **Step 5: Commit scaffold**

Run:

```powershell
git add requirements.txt .env.example scripts/sql/create_database.sql web
git commit -m "chore: scaffold django mysql project"
```

## Task 2: Core Models And Admin

**Files:**
- Create: `web/houses/models.py`
- Create: `web/houses/admin.py`
- Create: `web/houses/views.py`
- Modify: `web/houses/urls.py`
- Test: `web/houses/tests/test_models.py`

- [ ] **Step 1: Write model tests**

Create `web/houses/tests/test_models.py`:

```python
import pytest
from django.utils import timezone

from houses.models import City, District, House


@pytest.mark.django_db
def test_house_string_contains_title_and_city():
    city = City.objects.create(name="济南", province="山东省")
    district = District.objects.create(city=city, name="历下区")
    house = House.objects.create(
        title="历下核心两室",
        city=city,
        district=district,
        community="泉城小区",
        total_price=180,
        unit_price=22500,
        area=80,
        room_type="2室1厅",
        crawl_time=timezone.now(),
    )

    assert str(house) == "济南 历下核心两室"
```

- [ ] **Step 2: Run model test and verify failure**

Run:

```powershell
cd web
pytest houses/tests/test_models.py -q
```

Expected: FAIL because `houses.models.City` is not defined.

- [ ] **Step 3: Implement models**

Create `web/houses/models.py`:

```python
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class City(TimeStampedModel):
    name = models.CharField("城市名称", max_length=50, unique=True)
    province = models.CharField("所属省份", max_length=50, default="山东省")

    class Meta:
        ordering = ["name"]
        verbose_name = "城市"
        verbose_name_plural = "城市"

    def __str__(self):
        return self.name


class District(TimeStampedModel):
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="districts", verbose_name="城市")
    name = models.CharField("区域名称", max_length=50)

    class Meta:
        ordering = ["city__name", "name"]
        unique_together = [("city", "name")]
        verbose_name = "区域"
        verbose_name_plural = "区域"

    def __str__(self):
        return f"{self.city.name} {self.name}"


class House(TimeStampedModel):
    title = models.CharField("房源标题", max_length=200)
    city = models.ForeignKey(City, on_delete=models.PROTECT, related_name="houses", verbose_name="城市")
    district = models.ForeignKey(District, on_delete=models.PROTECT, related_name="houses", verbose_name="区域")
    community = models.CharField("小区名称", max_length=100, blank=True)
    total_price = models.DecimalField("总价(万元)", max_digits=10, decimal_places=2, db_index=True)
    unit_price = models.DecimalField("单价(元/平方米)", max_digits=10, decimal_places=2, db_index=True)
    area = models.DecimalField("面积(平方米)", max_digits=8, decimal_places=2, db_index=True)
    room_type = models.CharField("户型", max_length=50, db_index=True)
    floor = models.CharField("楼层", max_length=50, blank=True)
    direction = models.CharField("朝向", max_length=50, blank=True)
    decoration = models.CharField("装修", max_length=50, blank=True, db_index=True)
    build_year = models.PositiveIntegerField("建造年份", null=True, blank=True)
    address = models.CharField("详细地址", max_length=255, blank=True)
    longitude = models.DecimalField("经度", max_digits=10, decimal_places=6, null=True, blank=True)
    latitude = models.DecimalField("纬度", max_digits=10, decimal_places=6, null=True, blank=True)
    surrounding = models.TextField("周边配套", blank=True)
    source_url = models.CharField("来源链接", max_length=500, unique=True, null=True, blank=True)
    crawl_time = models.DateTimeField("采集时间", db_index=True)

    class Meta:
        ordering = ["-crawl_time", "-id"]
        indexes = [
            models.Index(fields=["city", "district"]),
            models.Index(fields=["total_price", "area"]),
        ]
        verbose_name = "房源"
        verbose_name_plural = "房源"

    def __str__(self):
        return f"{self.city.name} {self.title}"


class CrawlTask(TimeStampedModel):
    STATUS_CHOICES = [
        ("pending", "待运行"),
        ("running", "运行中"),
        ("success", "成功"),
        ("failed", "失败"),
    ]

    task_name = models.CharField("任务名称", max_length=100)
    target_city = models.CharField("目标城市", max_length=50)
    target_district = models.CharField("目标区域", max_length=50, blank=True)
    page_count = models.PositiveIntegerField("采集页数", default=1)
    status = models.CharField("任务状态", max_length=20, choices=STATUS_CHOICES, default="pending")
    success_count = models.PositiveIntegerField("成功数量", default=0)
    fail_count = models.PositiveIntegerField("失败数量", default=0)
    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    finished_at = models.DateTimeField("结束时间", null=True, blank=True)
    message = models.TextField("任务消息", blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "采集任务"
        verbose_name_plural = "采集任务"

    def __str__(self):
        return self.task_name


class AnalysisResult(TimeStampedModel):
    city = models.ForeignKey(City, on_delete=models.CASCADE, null=True, blank=True, related_name="analysis_results")
    district = models.ForeignKey(District, on_delete=models.CASCADE, null=True, blank=True, related_name="analysis_results")
    analysis_type = models.CharField("分析类型", max_length=50, db_index=True)
    result_json = models.JSONField("分析结果")
    generated_at = models.DateTimeField("生成时间", default=timezone.now)

    class Meta:
        ordering = ["-generated_at"]
        verbose_name = "分析结果"
        verbose_name_plural = "分析结果"

    def __str__(self):
        return self.analysis_type


class PredictResult(TimeStampedModel):
    house = models.ForeignKey(House, on_delete=models.SET_NULL, null=True, blank=True, related_name="predict_results")
    input_features = models.JSONField("输入特征")
    predicted_price = models.DecimalField("预测总价(万元)", max_digits=10, decimal_places=2)
    predicted_unit_price = models.DecimalField("预测单价(元/平方米)", max_digits=10, decimal_places=2)
    model_name = models.CharField("模型名称", max_length=100)
    predict_time = models.DateTimeField("预测时间", default=timezone.now)

    class Meta:
        ordering = ["-predict_time"]
        verbose_name = "预测记录"
        verbose_name_plural = "预测记录"

    def __str__(self):
        return f"{self.model_name} {self.predicted_price}万元"
```

- [ ] **Step 4: Register admin**

Create `web/houses/admin.py`:

```python
from django.contrib import admin

from .models import AnalysisResult, City, CrawlTask, District, House, PredictResult


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "province", "created_at")
    search_fields = ("name", "province")


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "created_at")
    list_filter = ("city",)
    search_fields = ("name", "city__name")


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ("title", "city", "district", "total_price", "unit_price", "area", "room_type", "crawl_time")
    list_filter = ("city", "district", "room_type", "decoration")
    search_fields = ("title", "community", "address")
    date_hierarchy = "crawl_time"


@admin.register(CrawlTask)
class CrawlTaskAdmin(admin.ModelAdmin):
    list_display = ("task_name", "target_city", "target_district", "page_count", "status", "success_count", "fail_count")
    list_filter = ("status", "target_city")
    search_fields = ("task_name", "target_city", "target_district")


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("analysis_type", "city", "district", "generated_at")
    list_filter = ("analysis_type", "city")


@admin.register(PredictResult)
class PredictResultAdmin(admin.ModelAdmin):
    list_display = ("model_name", "predicted_price", "predicted_unit_price", "predict_time")
    list_filter = ("model_name",)
```

- [ ] **Step 5: Add temporary dashboard view**

Create `web/houses/views.py`:

```python
from django.shortcuts import render


def dashboard(request):
    return render(request, "houses/dashboard.html", {"overview": {}})
```

Create `web/templates/houses/dashboard.html`:

```html
{% extends "houses/base.html" %}
{% block title %}首页大屏 - 智慧房源探索平台{% endblock %}
{% block content %}
<section class="panel">
  <h1>首页大屏</h1>
  <p class="muted">系统已启动，后续任务将接入统计图表。</p>
</section>
{% endblock %}
```

- [ ] **Step 6: Run migrations and tests**

Run:

```powershell
cd web
python manage.py makemigrations houses
python manage.py migrate
pytest houses/tests/test_models.py -q
```

Expected: migrations apply to MySQL and test passes.

- [ ] **Step 7: Commit models**

Run:

```powershell
git add web/houses web/templates/houses/dashboard.html
git commit -m "feat: add core house data models"
```

## Task 3: Cleaning Service And Demo Data Import

**Files:**
- Create: `web/houses/services/__init__.py`
- Create: `web/houses/services/cleaning.py`
- Create: `web/houses/sample_data.py`
- Create: `web/houses/management/__init__.py`
- Create: `web/houses/management/commands/__init__.py`
- Create: `web/houses/management/commands/seed_demo_data.py`
- Test: `web/houses/tests/test_cleaning.py`

- [ ] **Step 1: Write cleaning tests**

Create `web/houses/tests/test_cleaning.py`:

```python
from houses.services.cleaning import clean_house_record


def test_clean_house_record_normalizes_numbers_and_text():
    record = {
        "title": "  历下 核心两室  ",
        "city": "济南",
        "district": "历下区",
        "community": "泉城小区",
        "total_price": "180万",
        "unit_price": "22500元/平",
        "area": "80.0㎡",
        "room_type": "2 室 1 厅",
        "build_year": "2012年建",
    }

    cleaned = clean_house_record(record)

    assert cleaned["title"] == "历下 核心两室"
    assert cleaned["total_price"] == 180.0
    assert cleaned["unit_price"] == 22500.0
    assert cleaned["area"] == 80.0
    assert cleaned["room_type"] == "2室1厅"
    assert cleaned["build_year"] == 2012


def test_clean_house_record_rejects_invalid_area():
    record = {
        "title": "无效房源",
        "city": "济南",
        "district": "历下区",
        "total_price": "100万",
        "unit_price": "100000元/平",
        "area": "5㎡",
        "room_type": "1室1厅",
    }

    assert clean_house_record(record) is None
```

- [ ] **Step 2: Run cleaning tests and verify failure**

Run:

```powershell
cd web
pytest houses/tests/test_cleaning.py -q
```

Expected: FAIL because `houses.services.cleaning` does not exist.

- [ ] **Step 3: Implement cleaning service**

Create `web/houses/services/cleaning.py`:

```python
import re
from datetime import datetime
from decimal import Decimal

from django.utils import timezone


def compact_text(value):
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text).strip()


def compact_room_type(value):
    return compact_text(value).replace(" ", "")


def extract_float(value):
    if value is None:
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def extract_year(value):
    if value in (None, ""):
        return None
    match = re.search(r"(19|20)\d{2}", str(value))
    return int(match.group(0)) if match else None


def parse_crawl_time(value):
    if not value:
        return timezone.now()
    if isinstance(value, datetime):
        return timezone.make_aware(value) if timezone.is_naive(value) else value
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return timezone.now()
    return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed


def clean_house_record(record):
    total_price = extract_float(record.get("total_price"))
    unit_price = extract_float(record.get("unit_price"))
    area = extract_float(record.get("area"))

    if total_price is None or unit_price is None or area is None:
        return None
    if total_price <= 0 or area < 10 or unit_price <= 1000 or unit_price > 200000:
        return None

    return {
        "title": compact_text(record.get("title")),
        "city": compact_text(record.get("city")),
        "district": compact_text(record.get("district")),
        "community": compact_text(record.get("community")),
        "total_price": Decimal(str(round(total_price, 2))),
        "unit_price": Decimal(str(round(unit_price, 2))),
        "area": Decimal(str(round(area, 2))),
        "room_type": compact_room_type(record.get("room_type")),
        "floor": compact_text(record.get("floor")),
        "direction": compact_text(record.get("direction")),
        "decoration": compact_text(record.get("decoration")),
        "build_year": extract_year(record.get("build_year")),
        "address": compact_text(record.get("address")),
        "longitude": Decimal(str(record["longitude"])) if record.get("longitude") not in (None, "") else None,
        "latitude": Decimal(str(record["latitude"])) if record.get("latitude") not in (None, "") else None,
        "surrounding": compact_text(record.get("surrounding")),
        "source_url": compact_text(record.get("source_url")) or None,
        "crawl_time": parse_crawl_time(record.get("crawl_time")),
    }
```

- [ ] **Step 4: Add deterministic sample data**

Create `web/houses/sample_data.py` with at least 30 records across 济南、青岛、烟台、潍坊、临沂、济宁. Each record must include title, city, district, community, total_price, unit_price, area, room_type, floor, direction, decoration, build_year, address, longitude, latitude, surrounding, source_url, and crawl_time. Use values like:

```python
DEMO_HOUSES = [
    {
        "title": "历下核心两室 精装近地铁",
        "city": "济南",
        "district": "历下区",
        "community": "泉城小区",
        "total_price": "180万",
        "unit_price": "22500元/平",
        "area": "80㎡",
        "room_type": "2室1厅",
        "floor": "中楼层",
        "direction": "南北",
        "decoration": "精装",
        "build_year": "2012年",
        "address": "济南市历下区泉城路",
        "longitude": "117.0365",
        "latitude": "36.6669",
        "surrounding": "学校: 历下实验小学; 医院: 省立医院; 交通: 泉城路站",
        "source_url": "demo://jinan/lixia/001",
        "crawl_time": "2026-06-01T10:00:00",
    },
]
```

- [ ] **Step 5: Implement seed command**

Create `web/houses/management/commands/seed_demo_data.py`:

```python
from django.core.management.base import BaseCommand

from houses.models import City, District, House
from houses.sample_data import DEMO_HOUSES
from houses.services.cleaning import clean_house_record


class Command(BaseCommand):
    help = "Import deterministic demo house data into MySQL."

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for raw in DEMO_HOUSES:
            cleaned = clean_house_record(raw)
            if not cleaned:
                skipped += 1
                continue

            city, _ = City.objects.get_or_create(name=cleaned.pop("city"), defaults={"province": "山东省"})
            district, _ = District.objects.get_or_create(city=city, name=cleaned.pop("district"))

            lookup = {"source_url": cleaned["source_url"]} if cleaned["source_url"] else {
                "title": cleaned["title"],
                "community": cleaned["community"],
                "area": cleaned["area"],
                "total_price": cleaned["total_price"],
            }
            _, was_created = House.objects.update_or_create(
                **lookup,
                defaults={**cleaned, "city": city, "district": district},
            )
            created += int(was_created)

        self.stdout.write(self.style.SUCCESS(f"Imported {created} houses, skipped {skipped} invalid records."))
```

- [ ] **Step 6: Run tests and seed command**

Run:

```powershell
cd web
pytest houses/tests/test_cleaning.py -q
python manage.py seed_demo_data
```

Expected: tests pass and command prints `Imported ... houses`.

- [ ] **Step 7: Commit cleaning and seed data**

Run:

```powershell
git add web/houses/services web/houses/sample_data.py web/houses/management web/houses/tests/test_cleaning.py
git commit -m "feat: add demo data cleaning and import"
```

## Task 4: Analysis Service And Commands

**Files:**
- Create: `web/houses/services/analysis.py`
- Create: `web/houses/management/commands/generate_analysis.py`
- Test: `web/houses/tests/test_analysis.py`

- [ ] **Step 1: Write analysis test**

Create `web/houses/tests/test_analysis.py`:

```python
import pytest
from django.utils import timezone

from houses.models import City, District, House
from houses.services.analysis import build_overview


@pytest.mark.django_db
def test_build_overview_returns_core_metrics():
    city = City.objects.create(name="济南", province="山东省")
    district = District.objects.create(city=city, name="历下区")
    House.objects.create(
        title="A",
        city=city,
        district=district,
        community="C",
        total_price=100,
        unit_price=10000,
        area=100,
        room_type="3室2厅",
        crawl_time=timezone.now(),
    )
    House.objects.create(
        title="B",
        city=city,
        district=district,
        community="C",
        total_price=200,
        unit_price=20000,
        area=100,
        room_type="3室2厅",
        crawl_time=timezone.now(),
    )

    overview = build_overview()

    assert overview["total_houses"] == 2
    assert overview["city_count"] == 1
    assert overview["avg_total_price"] == 150.0
    assert overview["avg_unit_price"] == 15000.0
```

- [ ] **Step 2: Run analysis test and verify failure**

Run:

```powershell
cd web
pytest houses/tests/test_analysis.py -q
```

Expected: FAIL because `build_overview` is not defined.

- [ ] **Step 3: Implement analysis service**

Create `web/houses/services/analysis.py`:

```python
from django.db.models import Avg, Count, Max, Min
from django.db.models.functions import TruncDate

from houses.models import City, District, House


def _round(value, digits=2):
    return round(float(value or 0), digits)


def build_overview():
    aggregate = House.objects.aggregate(
        total_houses=Count("id"),
        avg_total_price=Avg("total_price"),
        avg_unit_price=Avg("unit_price"),
    )
    city_count = City.objects.count()
    city_distribution = list(
        House.objects.values("city__name")
        .annotate(count=Count("id"), avg_unit_price=Avg("unit_price"))
        .order_by("-count")
    )
    hot_districts = list(
        House.objects.values("city__name", "district__name")
        .annotate(count=Count("id"), avg_unit_price=Avg("unit_price"))
        .order_by("-count")[:8]
    )
    trend = list(
        House.objects.annotate(day=TruncDate("crawl_time"))
        .values("day")
        .annotate(avg_total_price=Avg("total_price"), count=Count("id"))
        .order_by("day")
    )
    map_points = list(
        House.objects.exclude(longitude__isnull=True)
        .exclude(latitude__isnull=True)
        .values("title", "city__name", "district__name", "longitude", "latitude", "total_price")[:200]
    )

    return {
        "total_houses": aggregate["total_houses"],
        "city_count": city_count,
        "avg_total_price": _round(aggregate["avg_total_price"]),
        "avg_unit_price": _round(aggregate["avg_unit_price"]),
        "city_distribution": [
            {"name": item["city__name"], "count": item["count"], "avg_unit_price": _round(item["avg_unit_price"])}
            for item in city_distribution
        ],
        "hot_districts": [
            {
                "city": item["city__name"],
                "district": item["district__name"],
                "count": item["count"],
                "avg_unit_price": _round(item["avg_unit_price"]),
            }
            for item in hot_districts
        ],
        "trend": [
            {"date": item["day"].isoformat(), "avg_total_price": _round(item["avg_total_price"]), "count": item["count"]}
            for item in trend
        ],
        "map_points": [
            {
                "title": item["title"],
                "city": item["city__name"],
                "district": item["district__name"],
                "longitude": float(item["longitude"]),
                "latitude": float(item["latitude"]),
                "total_price": float(item["total_price"]),
            }
            for item in map_points
        ],
    }


def build_province_stats():
    return {
        "cities": [
            {
                "city": item["city__name"],
                "count": item["count"],
                "avg_total_price": _round(item["avg_total_price"]),
                "avg_unit_price": _round(item["avg_unit_price"]),
                "max_total_price": _round(item["max_total_price"]),
                "min_total_price": _round(item["min_total_price"]),
            }
            for item in House.objects.values("city__name")
            .annotate(
                count=Count("id"),
                avg_total_price=Avg("total_price"),
                avg_unit_price=Avg("unit_price"),
                max_total_price=Max("total_price"),
                min_total_price=Min("total_price"),
            )
            .order_by("city__name")
        ]
    }


def build_city_stats(city_id):
    city = City.objects.get(id=city_id)
    districts = (
        House.objects.filter(city=city)
        .values("district__id", "district__name")
        .annotate(count=Count("id"), avg_total_price=Avg("total_price"), avg_unit_price=Avg("unit_price"))
        .order_by("-count")
    )
    return {
        "city": {"id": city.id, "name": city.name},
        "districts": [
            {
                "id": item["district__id"],
                "name": item["district__name"],
                "count": item["count"],
                "avg_total_price": _round(item["avg_total_price"]),
                "avg_unit_price": _round(item["avg_unit_price"]),
            }
            for item in districts
        ],
    }


def build_price_buckets():
    buckets = [
        ("100万以下", 0, 100),
        ("100-150万", 100, 150),
        ("150-200万", 150, 200),
        ("200-300万", 200, 300),
        ("300万以上", 300, None),
    ]
    result = []
    for label, low, high in buckets:
        queryset = House.objects.filter(total_price__gte=low)
        if high is not None:
            queryset = queryset.filter(total_price__lt=high)
        result.append({"label": label, "count": queryset.count()})
    return result


def build_room_type_distribution():
    return list(House.objects.values("room_type").annotate(count=Count("id")).order_by("-count"))
```

- [ ] **Step 4: Implement analysis command**

Create `web/houses/management/commands/generate_analysis.py`:

```python
from django.core.management.base import BaseCommand
from django.utils import timezone

from houses.models import AnalysisResult
from houses.services.analysis import build_overview, build_price_buckets, build_province_stats, build_room_type_distribution


class Command(BaseCommand):
    help = "Generate reusable analysis results."

    def handle(self, *args, **options):
        payloads = {
            "overview": build_overview(),
            "province": build_province_stats(),
            "price_buckets": {"items": build_price_buckets()},
            "room_types": {"items": build_room_type_distribution()},
        }
        for analysis_type, result in payloads.items():
            AnalysisResult.objects.update_or_create(
                analysis_type=analysis_type,
                city=None,
                district=None,
                defaults={"result_json": result, "generated_at": timezone.now()},
            )
        self.stdout.write(self.style.SUCCESS(f"Generated {len(payloads)} analysis results."))
```

- [ ] **Step 5: Run tests and command**

Run:

```powershell
cd web
pytest houses/tests/test_analysis.py -q
python manage.py generate_analysis
```

Expected: tests pass and command prints `Generated 4 analysis results.`

- [ ] **Step 6: Commit analysis**

Run:

```powershell
git add web/houses/services/analysis.py web/houses/management/commands/generate_analysis.py web/houses/tests/test_analysis.py
git commit -m "feat: add house market analysis service"
```

## Task 5: Prediction Service And Training Command

**Files:**
- Create: `web/houses/services/prediction.py`
- Create: `web/houses/management/commands/train_price_model.py`
- Test: `web/houses/tests/test_prediction.py`

- [ ] **Step 1: Write prediction fallback test**

Create `web/houses/tests/test_prediction.py`:

```python
import pytest
from django.utils import timezone

from houses.models import City, District, House
from houses.services.prediction import predict_price


@pytest.mark.django_db
def test_predict_price_uses_district_average_fallback_when_model_missing(settings):
    settings.MODEL_DIR = settings.BASE_DIR / "missing-model-dir"
    city = City.objects.create(name="济南", province="山东省")
    district = District.objects.create(city=city, name="历下区")
    House.objects.create(
        title="训练样本",
        city=city,
        district=district,
        community="泉城小区",
        total_price=200,
        unit_price=20000,
        area=100,
        room_type="3室2厅",
        crawl_time=timezone.now(),
    )

    result = predict_price({
        "city": "济南",
        "district": "历下区",
        "area": 80,
        "room_type": "2室1厅",
        "floor": "中楼层",
        "direction": "南北",
        "decoration": "精装",
        "build_year": 2015,
    })

    assert result["model_name"] == "规则估算"
    assert result["predicted_price"] == 160.0
    assert result["predicted_unit_price"] == 20000.0
```

- [ ] **Step 2: Run prediction test and verify failure**

Run:

```powershell
cd web
pytest houses/tests/test_prediction.py -q
```

Expected: FAIL because prediction service does not exist.

- [ ] **Step 3: Implement prediction service**

Create `web/houses/services/prediction.py`:

```python
from pathlib import Path

import joblib
import pandas as pd
from django.conf import settings
from django.db.models import Avg
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from houses.models import City, District, House

FEATURES = ["city", "district", "area", "room_type", "floor", "direction", "decoration", "build_year"]
MODEL_FILE = "price_model.joblib"


def _model_path():
    return Path(settings.MODEL_DIR) / MODEL_FILE


def _house_dataframe():
    rows = []
    for house in House.objects.select_related("city", "district").filter(total_price__gt=0, area__gt=10):
        rows.append({
            "city": house.city.name,
            "district": house.district.name,
            "area": float(house.area),
            "room_type": house.room_type,
            "floor": house.floor,
            "direction": house.direction,
            "decoration": house.decoration,
            "build_year": house.build_year or 2010,
            "total_price": float(house.total_price),
        })
    return pd.DataFrame(rows)


def train_price_model():
    df = _house_dataframe()
    if len(df) < 12:
        return {"trained": False, "reason": "有效训练数据不足 12 条"}

    x = df[FEATURES]
    y = df["total_price"]
    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=42)
    categorical = ["city", "district", "room_type", "floor", "direction", "decoration"]
    numeric = ["area", "build_year"]
    model = Pipeline([
        ("preprocess", ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
            ("num", "passthrough", numeric),
        ])),
        ("regressor", RandomForestRegressor(n_estimators=120, random_state=42, min_samples_leaf=1)),
    ])
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    model_dir = Path(settings.MODEL_DIR)
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, _model_path())
    return {
        "trained": True,
        "model_name": "随机森林回归",
        "mae": round(float(mean_absolute_error(y_test, predictions)), 2),
        "mse": round(float(mean_squared_error(y_test, predictions)), 2),
        "rmse": round(float(mean_squared_error(y_test, predictions) ** 0.5), 2),
        "r2": round(float(r2_score(y_test, predictions)), 4),
        "sample_count": len(df),
    }


def _average_unit_price(features):
    queryset = House.objects.all()
    city_name = features.get("city")
    district_name = features.get("district")
    if city_name:
        queryset = queryset.filter(city__name=city_name)
    if district_name:
        district_queryset = queryset.filter(district__name=district_name)
        if district_queryset.exists():
            queryset = district_queryset
    average = queryset.aggregate(avg=Avg("unit_price"))["avg"]
    if average:
        return float(average)
    return float(House.objects.aggregate(avg=Avg("unit_price"))["avg"] or 10000)


def _rule_predict(features):
    area = float(features.get("area") or 90)
    unit_price = _average_unit_price(features)
    total_price = round(unit_price * area / 10000, 2)
    return {
        "predicted_price": total_price,
        "predicted_unit_price": round(unit_price, 2),
        "model_name": "规则估算",
        "note": "模型文件不存在或样本不足，使用同区域/同城市均价估算。",
    }


def predict_price(features):
    path = _model_path()
    if not path.exists():
        return _rule_predict(features)

    model = joblib.load(path)
    row = pd.DataFrame([{
        "city": features.get("city", ""),
        "district": features.get("district", ""),
        "area": float(features.get("area") or 90),
        "room_type": features.get("room_type", ""),
        "floor": features.get("floor", ""),
        "direction": features.get("direction", ""),
        "decoration": features.get("decoration", ""),
        "build_year": int(features.get("build_year") or 2010),
    }])
    predicted_price = round(float(model.predict(row)[0]), 2)
    area = float(row.iloc[0]["area"])
    return {
        "predicted_price": predicted_price,
        "predicted_unit_price": round(predicted_price * 10000 / area, 2),
        "model_name": "随机森林回归",
        "note": "预测结果仅供课程学习和参考。",
    }
```

- [ ] **Step 4: Implement train command**

Create `web/houses/management/commands/train_price_model.py`:

```python
from django.core.management.base import BaseCommand

from houses.services.prediction import train_price_model


class Command(BaseCommand):
    help = "Train the demo house price prediction model."

    def handle(self, *args, **options):
        result = train_price_model()
        if result.get("trained"):
            self.stdout.write(self.style.SUCCESS(f"Trained model: {result}"))
        else:
            self.stdout.write(self.style.WARNING(result["reason"]))
```

- [ ] **Step 5: Run tests and train command**

Run:

```powershell
cd web
pytest houses/tests/test_prediction.py -q
python manage.py train_price_model
```

Expected: fallback test passes. Training command either saves model or reports insufficient data.

- [ ] **Step 6: Commit prediction**

Run:

```powershell
git add web/houses/services/prediction.py web/houses/management/commands/train_price_model.py web/houses/tests/test_prediction.py
git commit -m "feat: add price prediction service"
```

## Task 6: Pages And APIs

**Files:**
- Modify: `web/houses/views.py`
- Modify: `web/houses/urls.py`
- Create: `web/templates/houses/dashboard.html`
- Create: `web/templates/houses/province.html`
- Create: `web/templates/houses/city.html`
- Create: `web/templates/houses/house_list.html`
- Create: `web/templates/houses/house_detail.html`
- Create: `web/templates/houses/predict.html`
- Create: `web/static/houses/js/charts.js`
- Test: `web/houses/tests/test_api.py`

- [ ] **Step 1: Write API smoke tests**

Create `web/houses/tests/test_api.py`:

```python
import pytest
from django.urls import reverse
from django.utils import timezone

from houses.models import City, District, House


@pytest.mark.django_db
def test_houses_api_returns_paginated_items(client):
    city = City.objects.create(name="济南", province="山东省")
    district = District.objects.create(city=city, name="历下区")
    House.objects.create(
        title="API 房源",
        city=city,
        district=district,
        community="泉城小区",
        total_price=180,
        unit_price=22500,
        area=80,
        room_type="2室1厅",
        crawl_time=timezone.now(),
    )

    response = client.get(reverse("houses:api_houses"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 200
    assert payload["data"]["total"] == 1
    assert payload["data"]["items"][0]["title"] == "API 房源"


@pytest.mark.django_db
def test_predict_api_returns_price(client):
    response = client.post(
        reverse("houses:api_predict_price"),
        data='{"city":"济南","district":"历下区","area":90,"room_type":"3室2厅"}',
        content_type="application/json",
    )

    assert response.status_code == 200
    assert "predicted_price" in response.json()["data"]
```

- [ ] **Step 2: Run API tests and verify failure**

Run:

```powershell
cd web
pytest houses/tests/test_api.py -q
```

Expected: FAIL because API URL names are not configured.

- [ ] **Step 3: Implement views and routes**

Modify `web/houses/urls.py`:

```python
from django.urls import path

from . import views

app_name = "houses"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("province/", views.province, name="province"),
    path("cities/<int:city_id>/", views.city_detail, name="city_detail"),
    path("houses/", views.house_list, name="house_list"),
    path("houses/<int:house_id>/", views.house_detail, name="house_detail"),
    path("predict/", views.predict_page, name="predict"),
    path("api/houses/", views.api_houses, name="api_houses"),
    path("api/houses/<int:house_id>/", views.api_house_detail, name="api_house_detail"),
    path("api/statistics/overview/", views.api_overview, name="api_overview"),
    path("api/statistics/province/", views.api_province, name="api_province"),
    path("api/statistics/city/", views.api_city, name="api_city"),
    path("api/predict/price/", views.api_predict_price, name="api_predict_price"),
    path("api/admin/crawl-tasks/", views.api_crawl_tasks, name="api_crawl_tasks"),
]
```

Modify `web/houses/views.py` to include:

```python
import json
from decimal import Decimal

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import City, CrawlTask, House, PredictResult
from .services.analysis import build_city_stats, build_overview, build_price_buckets, build_province_stats, build_room_type_distribution
from .services.prediction import predict_price


def ok(data, message="success"):
    return JsonResponse({"code": 200, "message": message, "data": data}, json_dumps_params={"ensure_ascii": False})


def _to_float(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _house_dict(house):
    return {
        "id": house.id,
        "title": house.title,
        "city": house.city.name,
        "district": house.district.name,
        "community": house.community,
        "total_price": _to_float(house.total_price),
        "unit_price": _to_float(house.unit_price),
        "area": _to_float(house.area),
        "room_type": house.room_type,
        "floor": house.floor,
        "direction": house.direction,
        "decoration": house.decoration,
        "build_year": house.build_year,
        "address": house.address,
        "longitude": _to_float(house.longitude),
        "latitude": _to_float(house.latitude),
        "surrounding": house.surrounding,
        "crawl_time": house.crawl_time.isoformat(),
    }


def _filtered_houses(request):
    queryset = House.objects.select_related("city", "district")
    if request.GET.get("city"):
        queryset = queryset.filter(city_id=request.GET["city"])
    if request.GET.get("district"):
        queryset = queryset.filter(district_id=request.GET["district"])
    if request.GET.get("room_type"):
        queryset = queryset.filter(room_type=request.GET["room_type"])
    if request.GET.get("decoration"):
        queryset = queryset.filter(decoration=request.GET["decoration"])
    for param, lookup in {
        "min_price": "total_price__gte",
        "max_price": "total_price__lte",
        "min_area": "area__gte",
        "max_area": "area__lte",
    }.items():
        if request.GET.get(param):
            queryset = queryset.filter(**{lookup: request.GET[param]})
    sort = request.GET.get("sort", "-crawl_time")
    allowed_sort = {"total_price", "-total_price", "unit_price", "-unit_price", "area", "-area", "-crawl_time"}
    if sort in allowed_sort:
        queryset = queryset.order_by(sort)
    return queryset


def dashboard(request):
    return render(request, "houses/dashboard.html", {"overview": build_overview(), "price_buckets": build_price_buckets()})


def province(request):
    return render(request, "houses/province.html", {"stats": build_province_stats()})


def city_detail(request, city_id):
    return render(request, "houses/city.html", {"stats": build_city_stats(city_id)})


def house_list(request):
    queryset = _filtered_houses(request)
    paginator = Paginator(queryset, 10)
    page = paginator.get_page(request.GET.get("page", 1))
    return render(request, "houses/house_list.html", {
        "page_obj": page,
        "cities": City.objects.prefetch_related("districts"),
        "room_types": House.objects.values_list("room_type", flat=True).distinct(),
    })


def house_detail(request, house_id):
    house = get_object_or_404(House.objects.select_related("city", "district"), id=house_id)
    avg_unit = House.objects.filter(district=house.district).values_list("unit_price", flat=True)
    similar = House.objects.filter(district=house.district).exclude(id=house.id)[:4]
    return render(request, "houses/house_detail.html", {"house": house, "similar": similar, "district_avg_unit": avg_unit})


def predict_page(request):
    return render(request, "houses/predict.html", {"cities": City.objects.prefetch_related("districts")})


def api_houses(request):
    queryset = _filtered_houses(request)
    page = Paginator(queryset, int(request.GET.get("page_size", 10))).get_page(request.GET.get("page", 1))
    return ok({"total": page.paginator.count, "page": page.number, "page_size": page.paginator.per_page, "items": [_house_dict(h) for h in page]})


def api_house_detail(request, house_id):
    return ok(_house_dict(get_object_or_404(House.objects.select_related("city", "district"), id=house_id)))


def api_overview(request):
    return ok(build_overview())


def api_province(request):
    return ok(build_province_stats())


def api_city(request):
    return ok(build_city_stats(request.GET["city_id"]))


@csrf_exempt
@require_http_methods(["POST"])
def api_predict_price(request):
    payload = json.loads(request.body.decode("utf-8") or "{}")
    result = predict_price(payload)
    PredictResult.objects.create(
        input_features=payload,
        predicted_price=result["predicted_price"],
        predicted_unit_price=result["predicted_unit_price"],
        model_name=result["model_name"],
    )
    return ok(result)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_crawl_tasks(request):
    if request.method == "POST":
        payload = json.loads(request.body.decode("utf-8") or "{}")
        task = CrawlTask.objects.create(
            task_name=payload.get("task_name", "示例采集任务"),
            target_city=payload.get("target_city", "济南"),
            target_district=payload.get("target_district", ""),
            page_count=int(payload.get("page_count", 1)),
        )
        return ok({"id": task.id, "status": task.status})
    return ok({"items": list(CrawlTask.objects.values("id", "task_name", "target_city", "target_district", "page_count", "status"))})
```

- [ ] **Step 4: Implement templates and charts**

Create templates with chart containers and JSON script tags using Django `json_script`. For `dashboard.html`, include:

```html
{% extends "houses/base.html" %}
{% load static %}
{% block title %}首页大屏 - 智慧房源探索平台{% endblock %}
{% block content %}
{{ overview|json_script:"overview-data" }}
{{ price_buckets|json_script:"price-buckets-data" }}
<section class="grid stats-grid">
  <div class="panel"><div class="muted">房源总量</div><div class="metric">{{ overview.total_houses }}</div></div>
  <div class="panel"><div class="muted">覆盖城市</div><div class="metric">{{ overview.city_count }}</div></div>
  <div class="panel"><div class="muted">平均总价</div><div class="metric">{{ overview.avg_total_price }} 万</div></div>
  <div class="panel"><div class="muted">平均单价</div><div class="metric">{{ overview.avg_unit_price }} 元/㎡</div></div>
</section>
<section class="grid" style="grid-template-columns: 1fr 1fr; margin-top:16px;">
  <div class="panel"><h2>城市房源数量</h2><div id="cityChart" class="chart"></div></div>
  <div class="panel"><h2>价格区间分布</h2><div id="priceChart" class="chart"></div></div>
</section>
<section class="panel" style="margin-top:16px;">
  <h2>热门区域</h2>
  <table class="table">
    <tr><th>城市</th><th>区域</th><th>房源数</th><th>均价</th></tr>
    {% for item in overview.hot_districts %}
    <tr><td>{{ item.city }}</td><td>{{ item.district }}</td><td>{{ item.count }}</td><td>{{ item.avg_unit_price }}</td></tr>
    {% endfor %}
  </table>
</section>
{% endblock %}
{% block scripts %}
<script src="{% static 'houses/js/charts.js' %}"></script>
<script>renderDashboardCharts();</script>
{% endblock %}
```

Create `web/static/houses/js/charts.js`:

```javascript
function readJson(id) {
  const el = document.getElementById(id);
  return el ? JSON.parse(el.textContent) : {};
}

function renderDashboardCharts() {
  const overview = readJson("overview-data");
  const buckets = readJson("price-buckets-data");
  const cityChart = echarts.init(document.getElementById("cityChart"));
  cityChart.setOption({
    tooltip: {},
    xAxis: { type: "category", data: (overview.city_distribution || []).map(item => item.name) },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: (overview.city_distribution || []).map(item => item.count), itemStyle: { color: "#2563eb" } }]
  });
  const priceChart = echarts.init(document.getElementById("priceChart"));
  priceChart.setOption({
    tooltip: {},
    xAxis: { type: "category", data: (buckets || []).map(item => item.label) },
    yAxis: { type: "value" },
    series: [{ type: "bar", data: (buckets || []).map(item => item.count), itemStyle: { color: "#059669" } }]
  });
}
```

Create other templates with the same base:

- `province.html`: render `stats.cities` table and ECharts bar chart.
- `city.html`: render `stats.city.name`, `stats.districts` table and links to `/houses/?city=<id>`.
- `house_list.html`: render filter form, table of `page_obj`, pagination links.
- `house_detail.html`: render house fields, surrounding text, similar house links.
- `predict.html`: render input form and JavaScript `fetch("/api/predict/price/")` result panel.

- [ ] **Step 5: Run API tests and Django check**

Run:

```powershell
cd web
pytest houses/tests/test_api.py -q
python manage.py check
```

Expected: tests pass and Django check reports no issues.

- [ ] **Step 6: Commit pages and APIs**

Run:

```powershell
git add web/houses/views.py web/houses/urls.py web/templates/houses web/static/houses web/houses/tests/test_api.py
git commit -m "feat: add house platform pages and api"
```

## Task 7: Demo Crawler Command And Documentation

**Files:**
- Create: `web/houses/management/commands/run_demo_crawler.py`
- Create: `README.md`
- Modify: `docs/superpowers/specs/2026-06-20-house-explore-platform-design.md` if implementation names diverged.

- [ ] **Step 1: Implement demo crawler command**

Create `web/houses/management/commands/run_demo_crawler.py`:

```python
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from houses.models import CrawlTask, House


class Command(BaseCommand):
    help = "Run the course-project demo crawler flow using bundled sample data."

    def add_arguments(self, parser):
        parser.add_argument("--city", default="济南")
        parser.add_argument("--district", default="")
        parser.add_argument("--pages", type=int, default=1)

    def handle(self, *args, **options):
        task = CrawlTask.objects.create(
            task_name=f"示例采集-{options['city']}",
            target_city=options["city"],
            target_district=options["district"],
            page_count=options["pages"],
            status="running",
            started_at=timezone.now(),
        )
        before = House.objects.count()
        call_command("seed_demo_data")
        after = House.objects.count()
        task.status = "success"
        task.success_count = max(after - before, 0)
        task.fail_count = 0
        task.finished_at = timezone.now()
        task.message = "示例采集器已导入内置山东省房源数据。"
        task.save()
        self.stdout.write(self.style.SUCCESS(f"Demo crawler task {task.id} finished with {task.success_count} new houses."))
```

- [ ] **Step 2: Write README**

Create `README.md` with:

```markdown
# 智慧房源探索平台

这是一个基于 Django + MySQL 的课程验收型房源数据分析与可视化原型。

## 功能

- MySQL 存储城市、区域、房源、采集任务、分析结果、预测记录
- 内置山东省示例房源数据
- 数据清洗、去重、异常过滤
- 首页大屏、省级分析、城市分析、房源列表、房源详情、房价预测
- ECharts 图表
- 随机森林房价预测与规则估算兜底
- Django Admin 数据维护

## 初始化

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

编辑 `.env` 中的 MySQL 密码。

```powershell
mysql -u root -p < scripts/sql/create_database.sql
cd web
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo_data
python manage.py generate_analysis
python manage.py train_price_model
python manage.py createsuperuser
python manage.py runserver
```

访问 `http://127.0.0.1:8000/`。

## 示例采集任务

```powershell
cd web
python manage.py run_demo_crawler --city 济南 --pages 1
```

第一版不抓取真实网站，示例采集器用于演示采集任务和数据入库流程。

## 验证

```powershell
cd web
python manage.py check
pytest houses/tests -q
```
```

- [ ] **Step 3: Run demo crawler command**

Run:

```powershell
cd web
python manage.py run_demo_crawler --city 济南 --pages 1
```

Expected: command creates a CrawlTask and prints `Demo crawler task ... finished`.

- [ ] **Step 4: Commit crawler docs**

Run:

```powershell
git add web/houses/management/commands/run_demo_crawler.py README.md docs/superpowers/specs/2026-06-20-house-explore-platform-design.md
git commit -m "docs: add demo crawler and run guide"
```

## Task 8: Final Verification And Polish

**Files:**
- Modify only files needed by verification failures.

- [ ] **Step 1: Run full test suite**

Run:

```powershell
cd web
pytest houses/tests -q
```

Expected: all tests pass.

- [ ] **Step 2: Run Django validation**

Run:

```powershell
cd web
python manage.py check
```

Expected: `System check identified no issues`.

- [ ] **Step 3: Run full setup commands on MySQL**

Run:

```powershell
mysql -u root -p < scripts/sql/create_database.sql
cd web
python manage.py migrate
python manage.py seed_demo_data
python manage.py generate_analysis
python manage.py train_price_model
python manage.py run_demo_crawler --city 济南 --pages 1
```

Expected: each command completes without traceback.

- [ ] **Step 4: Smoke test local server**

Run:

```powershell
cd web
python manage.py runserver 127.0.0.1:8000
```

Open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/province/`
- `http://127.0.0.1:8000/houses/`
- `http://127.0.0.1:8000/predict/`
- `http://127.0.0.1:8000/api/statistics/overview/`

Expected: pages render and JSON endpoints return `code: 200`.

- [ ] **Step 5: Commit final fixes**

If verification required fixes, commit them:

```powershell
git add .
git commit -m "fix: polish platform verification issues"
```

If no files changed, do not create an empty commit.

## Self-Review

- Spec coverage: The plan covers MySQL setup, models, demo data, cleaning, analysis, prediction, pages, APIs, admin, demo crawler, docs, and verification.
- Scope: The plan keeps Redis, real crawling, and Baidu Map integration out of first implementation, matching the approved boundary.
- Placeholder scan: No task contains unresolved placeholder markers. Steps specify concrete files, commands, and expected outcomes.
- Type consistency: Model fields, service return keys, URL names, and tests use the same names across tasks.
