# Web 调试流程说明

这份文档用于手动调试 `web` 目录下的 Django 项目。它的重点不是重新介绍功能，而是帮你知道：一个浏览器请求从哪里进来、会执行哪个函数、会查哪些表、应该在哪里打断点。

## 1. 项目类型

这个 `web` 目录是一个 Django 项目，不是 Spring Boot 项目。

核心目录如下：

```text
web/
  manage.py                         Django 命令入口
  house_platform/
    settings.py                     项目配置：数据库、模板、静态文件、应用注册
    urls.py                         项目总路由
    wsgi.py                         部署入口
  houses/
    urls.py                         houses 应用路由
    views.py                        页面和 API 的请求处理函数
    models.py                       数据库表模型
    services/
      cleaning.py                   数据清洗
      analysis.py                   统计分析
      prediction.py                 房价预测和模型训练
    management/commands/            自定义 manage.py 命令
  templates/houses/                 HTML 模板
  static/houses/                    CSS、JS、地图 JSON 等静态资源
```

## 2. 启动前准备

建议在项目根目录 `/Users/a1-6/Desktop/coding/house_predict` 操作：

```bash
cd /Users/a1-6/Desktop/coding/house_predict
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

然后检查 `.env` 里的 MySQL 配置。Django 会在 `web/house_platform/settings.py` 读取这些变量：

```text
MYSQL_DATABASE
MYSQL_USER
MYSQL_PASSWORD
MYSQL_HOST
MYSQL_PORT
DJANGO_DEBUG
DJANGO_ALLOWED_HOSTS
```

如果本机 MySQL 没有数据库，先创建数据库。README 里提供的是 Windows 命令；macOS/Linux 可以参考：

```bash
mysql -u root -p < scripts/sql/create_database.sql
```

## 3. 初始化数据库和演示数据

进入 `web` 目录：

```bash
cd /Users/a1-6/Desktop/coding/house_predict/web
python manage.py check
python manage.py migrate
```

如果有老师给的 `house_clean.csv`，导入真实课程数据：

```bash
python manage.py import_house_csv
```

如果没有 `house_clean.csv`，先导入内置演示数据：

```bash
python manage.py seed_demo_data
```

训练房价预测模型：

```bash
python manage.py train_price_model
```

启动服务：

```bash
python manage.py runserver
```

浏览器打开：

```text
http://127.0.0.1:8000/
```

## 4. Django 请求是怎么进来的

一次请求的大致链路是：

```text
浏览器/HTTP 客户端
  -> web/house_platform/urls.py
  -> web/houses/urls.py
  -> web/houses/views.py 中的函数
  -> models.py 查询数据库，或 services/ 中的业务函数
  -> render(...) 返回 HTML，或 JsonResponse 返回 JSON
```

项目总路由在 `house_platform/urls.py`：

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("houses.urls")),
]
```

这表示：

- `/admin/` 交给 Django Admin。
- 其他从根路径开始的请求交给 `houses/urls.py`。

应用路由在 `houses/urls.py`。例如：

```python
path("api/houses/", views.api_houses, name="api_houses")
```

意思是：

```text
GET /api/houses/  -> 执行 views.py 里的 api_houses(request)
```

## 5. URL 和函数对应关系

页面请求：

| URL | 处理函数 | 模板 | 用途 |
| --- | --- | --- | --- |
| `/` | `dashboard` | `dashboard.html` | 首页看板 |
| `/province/` | `province` | `province.html` | 省级统计分析 |
| `/cities/<city_id>/` | `city_detail` | `city.html` | 城市详情分析 |
| `/houses/` | `house_list` | `house_list.html` | 房源列表 |
| `/houses/<house_id>/` | `house_detail` | `house_detail.html` | 房源详情 |
| `/predict/` | `predict_page` | `predict.html` | 房价预测页面 |

API 请求：

| URL | 方法 | 处理函数 | 用途 |
| --- | --- | --- | --- |
| `/api/houses/` | GET | `api_houses` | 查询房源列表 JSON |
| `/api/houses/<house_id>/` | GET | `api_house_detail` | 查询单套房源 JSON |
| `/api/statistics/overview/` | GET | `api_overview` | 首页总览统计 |
| `/api/statistics/province/` | GET | `api_province` | 省级城市统计 |
| `/api/statistics/city/?city_id=1` | GET | `api_city` | 某城市区县统计 |
| `/api/predict/price/` | POST | `api_predict_price` | 房价预测 |
| `/api/admin/crawl-tasks/` | GET/POST | `api_crawl_tasks` | 爬取任务管理，需要管理员登录 |

## 6. 推荐断点位置

如果你用 PyCharm、VS Code 或 Cursor 调试，可以从这些地方打断点。

### 6.1 房源列表页面

访问：

```text
http://127.0.0.1:8000/houses/
```

推荐断点：

```text
houses/views.py
  house_list
  _filtered_houses
  _filter_by_lookup
```

流程：

```text
house_list(request)
  -> _filtered_houses(request.GET)
  -> Paginator(...)
  -> render("houses/house_list.html", ...)
```

可以试这些 URL：

```text
http://127.0.0.1:8000/houses/?page=1&page_size=10
http://127.0.0.1:8000/houses/?city=济南
http://127.0.0.1:8000/houses/?min_price=100&max_price=200
http://127.0.0.1:8000/houses/?sort=-total_price
```

### 6.2 房源列表 API

访问：

```bash
curl "http://127.0.0.1:8000/api/houses/?page=1&page_size=5"
```

推荐断点：

```text
houses/views.py
  api_houses
  _filtered_houses
  _house_dict
```

流程：

```text
api_houses(request)
  -> _filtered_houses(request.GET, strict=True)
  -> Paginator(...)
  -> _house_dict(house)
  -> ok(...)
  -> JsonResponse
```

### 6.3 首页统计

访问：

```text
http://127.0.0.1:8000/
```

推荐断点：

```text
houses/views.py
  dashboard

houses/services/analysis.py
  build_overview
  build_price_buckets
  build_area_buckets
  build_room_type_distribution
  build_decoration_distribution
```

流程：

```text
dashboard(request)
  -> build_overview()
  -> build_price_buckets()
  -> build_area_buckets()
  -> build_room_type_distribution()
  -> render("houses/dashboard.html", ...)
```

注意：`analysis.py` 里有两个同名的 `build_city_stats`，Python 只会保留后面那个定义。调试城市统计时，断点要打在文件后面那个 `build_city_stats`。

### 6.4 城市统计 API

先查有哪些城市：

```bash
python manage.py shell
```

进入 shell 后执行：

```python
from houses.models import City
list(City.objects.values("id", "name"))
```

然后访问：

```bash
curl "http://127.0.0.1:8000/api/statistics/city/?city_id=1"
```

推荐断点：

```text
houses/views.py
  api_city

houses/services/analysis.py
  build_city_stats
```

### 6.5 房价预测页面和 API

页面：

```text
http://127.0.0.1:8000/predict/
```

API：

```bash
curl -X POST "http://127.0.0.1:8000/api/predict/price/" \
  -H "Content-Type: application/json" \
  -d '{
    "city": "济南",
    "district": "历下区",
    "area": 95,
    "room_type": "三室一厅",
    "floor": "中楼层",
    "direction": "南",
    "decoration": "精装",
    "build_year": 2015
  }'
```

推荐断点：

```text
houses/views.py
  api_predict_price
  _json_body

houses/services/prediction.py
  predict_price
  _normalize_features
  _model_path
  _rule_predict
  _average_unit_price
```

流程：

```text
api_predict_price(request)
  -> _json_body(request)
  -> predict_price(features)
     -> _normalize_features(features)
     -> 如果 web/models/price_model.joblib 存在，加载模型预测
     -> 如果模型不存在或加载失败，使用 _rule_predict 规则估算
  -> PredictResult.objects.create(...)
  -> ok(result)
```

如果你还没有执行过 `python manage.py train_price_model`，预测接口不会报错，而是走规则估算：

```text
平均单价 * 面积 / 10000 = 预测总价，单位是万元
```

### 6.6 数据导入流程

导入老师 CSV：

```bash
python manage.py import_house_csv --limit 100
```

推荐断点：

```text
houses/management/commands/import_house_csv.py
  handle

houses/services/teacher_data.py
  iter_teacher_house_records

houses/services/cleaning.py
  clean_house_record

houses/management/commands/seed_demo_data.py
  build_house_lookup
```

流程：

```text
读取 CSV
  -> 转换成统一字段
  -> clean_house_record 清洗
  -> City.objects.get_or_create
  -> District.objects.get_or_create
  -> House.objects.update_or_create
```

导入内置演示数据：

```bash
python manage.py seed_demo_data
```

推荐断点：

```text
houses/management/commands/seed_demo_data.py
  handle
  build_house_lookup
```

### 6.7 爬虫演示流程

这个项目里的演示爬虫不会真的请求外部网站，而是创建一条爬取任务记录，并导入内置演示房源。

运行：

```bash
python manage.py run_demo_crawler --city 济南 --pages 1
```

推荐断点：

```text
houses/management/commands/run_demo_crawler.py
  handle

houses/management/commands/seed_demo_data.py
  handle
```

流程：

```text
创建 CrawlTask，状态 running
  -> call_command("seed_demo_data")
  -> 统计导入前后 House 数量
  -> 更新 CrawlTask，状态 success 或 failed
```

## 7. 数据库表怎么对应代码

表定义在 `houses/models.py`：

| 模型 | 作用 |
| --- | --- |
| `City` | 城市，例如济南、青岛 |
| `District` | 区县，属于某个城市 |
| `House` | 房源主表 |
| `CrawlTask` | 爬取任务记录 |
| `AnalysisResult` | 统计分析结果记录 |
| `PredictResult` | 每次预测的输入和结果 |

在 Django shell 里可以这样检查数据：

```bash
python manage.py shell
```

```python
from houses.models import City, District, House, PredictResult, CrawlTask

City.objects.count()
House.objects.count()
House.objects.select_related("city", "district").values("id", "title", "city__name", "district__name")[:5]
PredictResult.objects.order_by("-predict_time").values("id", "predicted_price", "model_name")[:5]
CrawlTask.objects.order_by("-created_at").values("id", "task_name", "status")[:5]
```

## 8. 为什么不像 Spring Boot 那样在函数上写请求注解

Spring Boot 常见写法是：

```java
@GetMapping("/api/houses")
public ResponseEntity<?> listHouses() {
    ...
}
```

也就是“URL 映射”和“处理函数”写在同一个地方，靠注解绑定。

这个项目用的是 Django。Django 默认采用“集中路由表”的方式：

```python
# houses/urls.py
path("api/houses/", views.api_houses, name="api_houses")
```

然后处理函数单独写在 `views.py`：

```python
# houses/views.py
@require_GET
def api_houses(request):
    ...
```

所以 Django 里要找接口对应函数，一般这样找：

```text
先看 house_platform/urls.py
  -> include("houses.urls")
再看 houses/urls.py
  -> path("api/houses/", views.api_houses, ...)
最后看 houses/views.py
  -> def api_houses(request)
```

你看到的 `@require_GET`、`@csrf_exempt`、`@login_required` 这些不是 URL 注解，而是请求限制或权限控制：

| 装饰器 | 作用 |
| --- | --- |
| `@require_GET` | 只允许 GET 请求 |
| `@require_http_methods(["GET", "POST"])` | 只允许指定方法 |
| `@csrf_exempt` | 跳过 CSRF 校验 |
| `@login_required` | 必须登录 |
| `@staff_required_json` | 自定义管理员权限检查，失败返回 JSON |

可以这样理解：

```text
Spring Boot:
  @GetMapping 负责 URL 映射

Django:
  urls.py 的 path(...) 负责 URL 映射
  views.py 上的装饰器负责方法限制、登录权限、CSRF 等额外规则
```

## 9. 常用调试命令

检查配置和模型：

```bash
python manage.py check
```

执行测试：

```bash
pytest houses/tests -q
```

查看所有 URL 路由，可以在 Django shell 里执行：

```python
from django.urls import get_resolver

for pattern in get_resolver().url_patterns:
    print(pattern)
```

由于 `houses.urls` 是 include 进去的，想看更详细的应用路由，直接看：

```text
web/houses/urls.py
```

## 10. 常见问题

### 10.1 页面打开后没有数据

先检查数据库有没有房源：

```bash
python manage.py shell
```

```python
from houses.models import House
House.objects.count()
```

如果是 0，执行：

```bash
python manage.py seed_demo_data
```

或：

```bash
python manage.py import_house_csv
```

### 10.2 预测接口返回规则估算

这通常说明模型文件不存在或不可用。执行：

```bash
python manage.py train_price_model
```

模型文件位置：

```text
web/models/price_model.joblib
```

### 10.3 MySQL 连接失败

检查 `.env` 和 `settings.py` 对应关系：

```text
MYSQL_DATABASE -> DATABASES["default"]["NAME"]
MYSQL_USER     -> DATABASES["default"]["USER"]
MYSQL_PASSWORD -> DATABASES["default"]["PASSWORD"]
MYSQL_HOST     -> DATABASES["default"]["HOST"]
MYSQL_PORT     -> DATABASES["default"]["PORT"]
```

也可以先用命令确认 MySQL 能连上：

```bash
mysql -u root -p
```

### 10.4 API 返回 403

`/api/admin/crawl-tasks/` 需要登录并且用户是 staff。普通公开 API 不需要登录。

可以创建管理员：

```bash
python manage.py createsuperuser
```

然后打开：

```text
http://127.0.0.1:8000/admin/
```

### 10.5 断点没有命中

优先确认三件事：

1. URL 是否真的对应你打断点的函数。
2. 请求方法是否正确，比如预测接口必须是 POST。
3. 是否打在了未使用的旧函数上，比如 `analysis.py` 中前一个 `build_city_stats` 会被后一个同名定义覆盖。

最稳的查找方式是：

```text
浏览器 URL
  -> houses/urls.py 找 path(...)
  -> path(...) 右侧找 views.xxx
  -> views.py 找 def xxx(...)
```
