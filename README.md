# 智慧房源探索平台

智慧房源探索平台是一个面向课程项目验收的 Django + MySQL 房源数据分析原型。第一版聚焦跑通房源数据导入、清洗、存储、统计分析、价格预测、页面展示和后台管理流程。

## 功能特性

- MySQL 存储城市、区县、房源、采集任务、分析结果和预测记录。
- 内置山东省示例房源数据，可通过命令快速导入演示数据。
- 数据清洗支持字段标准化、异常过滤和基于来源链接的去重。
- 提供首页大屏、省级分析、城市分析、房源列表、房源详情和房价预测页面，并使用图表展示统计结果。
- 房价预测优先使用训练模型；当训练数据不足或模型不可用时，使用规则估算兜底。
- Django Admin 支持管理基础数据、房源、采集任务、分析结果和预测记录。

## 初始化与运行

先复制环境配置文件，并编辑 `.env` 中的 MySQL 用户名、密码、主机和数据库名，尤其要确认 MySQL 密码正确。

在 PowerShell 中执行：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
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

启动后访问 [http://127.0.0.1:8000/](http://127.0.0.1:8000/) 查看平台页面。

## 示例采集器

可以运行课程项目演示采集流程：

```powershell
python manage.py run_demo_crawler --city 济南 --pages 1
```

第一版示例采集器不会抓取真实网站，只会创建采集任务记录，并导入项目内置的山东省房源示例数据。

## 验证命令

```powershell
python manage.py check
pytest houses/tests -q
```

## API 与后台说明

房源查询、统计分析、预测等普通 API 可直接访问；采集任务相关管理 API 和 Django Admin 需要登录，并要求用户具备 staff 权限。
