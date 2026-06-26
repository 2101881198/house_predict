# 智慧房源探索平台

这是一个基于 Django + MySQL 的智慧房源探索平台课程项目原型，覆盖房源数据导入、清洗、存储、统计分析、价格预测和可视化展示等功能。

## 主要功能

- 使用 MySQL 存储城市、区域、房源、爬取任务、分析结果和预测记录。
- 支持导入老师提供的 `house_clean.csv` 房源数据，也内置山东省示例房源数据。
- 支持房源数据清洗，包括字段标准化、无效记录过滤和来源 URL 去重。
- 提供首页看板、省级地图分析、城市区县地图分析、房源列表、房源详情和价格预测页面。
- 提供 Django Admin 后台，用于管理基础数据、房源、爬取任务、分析结果和预测记录。
- 提供公开 API，用于房源查询、统计分析和价格预测。

## 环境要求

- 已安装 Python。
- 已安装并启动 MySQL。
- `mysql` 命令已加入系统 `PATH`。
- 数据库用户需要具备创建或使用项目数据库的权限。如果不是 `root` 用户，需要提前配置好 MySQL 授权。

## 安装与运行

在项目根目录执行以下命令：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

然后编辑 `.env` 文件，填写你的 MySQL 用户名、密码、主机、端口和数据库名。

创建数据库：

```powershell
Get-Content scripts/sql/create_database.sql | mysql -u root -p
```

如果你使用的是 `cmd.exe`，也可以这样执行：

```cmd
mysql -u root -p < scripts\sql\create_database.sql
```

初始化 Django 项目：

```powershell
cd web
python manage.py makemigrations
python manage.py migrate
python manage.py import_house_csv
python manage.py generate_analysis
python manage.py train_price_model
python manage.py createsuperuser
python manage.py runserver
```

如果没有 `house_clean.csv`，可以改用内置演示数据：

```powershell
python manage.py seed_demo_data
```

如果想先快速测试导入流程，可以只导入前 100 条：

```powershell
python manage.py import_house_csv --limit 100
```

服务启动后，在浏览器打开：

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## 页面入口

- 首页看板：`/`
- 省级分析：`/province/`
- 城市分析：`/cities/<城市ID>/`
- 房源列表：`/houses/`
- 房源详情：`/houses/<房源ID>/`
- 价格预测：`/predict/`
- 后台管理：`/admin/`

## 示例爬虫

项目提供了课程演示用的爬虫流程：

```powershell
cd web
python manage.py run_demo_crawler --city 济南 --pages 1
```

当前版本不会抓取真实网站，而是创建爬取任务记录，并导入项目内置的山东省示例房源数据，便于课程验收和功能演示。

## 常用 API

- 房源列表：`/api/houses/`
- 房源详情：`/api/houses/<房源ID>/`
- 总览统计：`/api/statistics/overview/`
- 省级统计：`/api/statistics/province/`
- 城市统计：`/api/statistics/city/`
- 价格预测：`/api/predict/price/`
- 爬取任务管理：`/api/admin/crawl-tasks/`

其中爬取任务管理接口和 Django Admin 需要登录管理员账号。

## 验证命令

在 `web` 目录执行：

```powershell
python manage.py check
pytest houses/tests -q
```

## Windows 安装 mysqlclient 失败怎么办

如果执行 `pip install -r requirements.txt` 时安装 `mysqlclient` 失败，建议优先使用带有兼容预编译 wheel 的 Python 版本。

如果仍然失败，可以安装 Microsoft C++ Build Tools，并安装匹配的 MySQL 或 MariaDB 客户端开发库；也可以安装与你的 Python 版本和 Windows 架构匹配的 `mysqlclient` wheel。
