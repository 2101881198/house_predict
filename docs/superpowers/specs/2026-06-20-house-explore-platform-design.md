# 智慧房源探索平台实现设计

## 背景与目标

本项目基于用户提供的《智慧房源探索平台需求分析文档》和《智慧房源探索平台项目分析与设计文档》实现。当前仓库为空项目，第一版目标是交付一个严格使用 MySQL 的课程验收型完整原型，能够跑通房源数据导入、清洗、存储、统计分析、价格预测、Web 展示和后台管理流程。

第一版不依赖真实网站爬虫和 Redis。系统内置山东省示例房源数据，提供采集任务结构和示例采集器，后续可扩展为真实 Scrapy 或 Scrapy-Redis 采集。

## 实现范围

第一版实现以下能力：

1. 使用 Django 构建 Web 平台和 JSON API。
2. 使用 MySQL 存储城市、区域、房源、采集任务、分析结果和预测记录。
3. 提供建库 SQL、环境配置示例和运行说明。
4. 提供示例房源数据导入命令。
5. 提供数据清洗、去重、异常过滤和格式标准化逻辑。
6. 提供城市、区域、价格、面积、户型等维度统计分析。
7. 使用 Scikit-learn 训练房价预测模型，数据不足时提供规则化估算兜底。
8. 使用 Django 模板和 ECharts 展示首页大屏、省级分析、城市分析、房源列表、房源详情和房价预测页面。
9. 使用 Django Admin 管理基础数据、房源、采集任务、分析结果和预测记录。

第一版明确不实现：

1. 不强制依赖 Redis。
2. 不抓取真实网站数据。
3. 不直接接入百度地图 API，先使用房源经纬度散点和区域分布图模拟地图展示。
4. 不承诺预测结果具备真实交易决策价值。

## 总体架构

项目采用 Django 单体架构，按职责拆分为 Web、数据处理、预测和采集模块。

```text
house_predict/
├── crawler/                 # 示例采集器和采集任务扩展位置
├── data_process/            # 清洗、导入、统计分析逻辑
├── predictor/               # 模型训练、评估、预测逻辑
├── web/                     # Django 项目
│   ├── houses/              # 核心业务应用
│   ├── templates/           # 页面模板
│   ├── static/              # CSS、JS、图表资源
│   └── manage.py
├── scripts/
│   └── sql/                 # MySQL 建库脚本
├── docs/                    # 项目文档
└── requirements.txt
```

数据流如下：

1. 管理员创建或运行示例采集任务。
2. 示例数据进入清洗模块。
3. 清洗模块完成标准化、去重和异常过滤。
4. Django ORM 将规范化数据写入 MySQL。
5. 分析模块从 MySQL 读取房源数据并生成统计结果。
6. 预测模块读取房源数据训练模型并保存模型文件或评估结果。
7. 页面和 API 读取房源、统计和预测数据进行展示。

## 数据模型

### City

保存城市信息：

- `name`：城市名称。
- `province`：所属省份，第一版主要为山东省。
- `created_at`：创建时间。

### District

保存区域信息：

- `city`：所属城市。
- `name`：区域名称。
- `created_at`：创建时间。

### House

保存房源核心字段：

- `title`：房源标题。
- `city`：所属城市。
- `district`：所属区域。
- `community`：小区名称。
- `total_price`：总价，单位万元。
- `unit_price`：单价，单位元/平方米。
- `area`：建筑面积，单位平方米。
- `room_type`：户型。
- `floor`：楼层。
- `direction`：朝向。
- `decoration`：装修情况。
- `build_year`：建造年份。
- `address`：详细地址。
- `longitude`：经度。
- `latitude`：纬度。
- `surrounding`：周边配套文本或 JSON。
- `source_url`：来源链接，用于去重。
- `crawl_time`：采集时间。

常用筛选字段建立索引：城市、区域、总价、单价、面积、户型、装修、采集时间。

### CrawlTask

保存采集任务：

- `task_name`
- `target_city`
- `target_district`
- `page_count`
- `status`
- `success_count`
- `fail_count`
- `started_at`
- `finished_at`
- `message`

### AnalysisResult

保存预计算分析结果：

- `city`
- `district`
- `analysis_type`
- `result_json`
- `generated_at`

### PredictResult

保存预测记录：

- `house`
- `input_features`
- `predicted_price`
- `predicted_unit_price`
- `model_name`
- `predict_time`

## 页面设计

### 首页大屏 `/`

展示整体市场概览：

- 房源总量。
- 覆盖城市数量。
- 平均总价。
- 平均单价。
- 城市房源数量柱状图。
- 价格趋势折线图。
- 热门区域排行。
- 房源经纬度散点分布。

### 山东省房源情况 `/province/`

展示山东主要城市对比：

- 城市房源数量。
- 城市平均总价。
- 城市平均单价。
- 城市最高价和最低价。
- 城市价格区间分布。

### 城市房源情况 `/cities/<city_id>/`

展示指定城市的区域分析：

- 区域房源数量。
- 区域均价。
- 区域热度。
- 区域价格分布。
- 进入房源列表的入口。

### 地区房源列表 `/houses/`

支持分页、筛选和排序：

- 城市。
- 区域。
- 最低/最高总价。
- 最小/最大面积。
- 户型。
- 装修。
- 排序字段。

### 房源详情 `/houses/<house_id>/`

展示单个房源：

- 标题、价格、面积、户型等核心信息。
- 小区、楼层、朝向、装修、建造年份。
- 地址和坐标。
- 周边配套。
- 同区域均价参考。
- 相似房源推荐。

### 房价预测 `/predict/`

用户输入房源特征后获取参考价格：

- 城市。
- 区域。
- 面积。
- 户型。
- 楼层。
- 朝向。
- 装修。
- 建造年份。

返回预测总价、参考单价、模型名称和说明。

## API 设计

所有接口返回统一 JSON：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

核心接口：

- `GET /api/houses/`：分页查询房源。
- `GET /api/houses/<id>/`：查询房源详情。
- `GET /api/statistics/overview/`：首页统计。
- `GET /api/statistics/province/`：省级统计。
- `GET /api/statistics/city/?city_id=...`：城市统计。
- `POST /api/predict/price/`：预测房价。
- `GET /api/admin/crawl-tasks/`：查看采集任务。
- `POST /api/admin/crawl-tasks/`：创建示例采集任务。

## 数据处理设计

清洗规则：

1. 总价统一为万元。
2. 单价统一为元/平方米。
3. 面积统一为平方米。
4. 建造年份提取为整数年份。
5. 文本字段去除多余空白。
6. `source_url` 存在时按来源链接去重。
7. `source_url` 不存在时按标题、小区、面积、总价组合去重。
8. 过滤总价小于等于 0、面积小于 10 平方米、单价明显异常的数据。

分析维度：

1. 城市房源数量、平均总价、平均单价。
2. 区域房源数量、平均单价、热度排行。
3. 总价区间分布。
4. 面积区间分布。
5. 户型数量分布。
6. 采集时间趋势。

## 预测设计

第一版使用随机森林回归作为主模型，线性回归作为对比或备用模型。输入特征包括：

- 城市。
- 区域。
- 面积。
- 户型。
- 楼层。
- 朝向。
- 装修。
- 建造年份。

训练流程：

1. 从 MySQL 读取有效房源数据。
2. 过滤价格、面积缺失或异常数据。
3. 类别特征使用 OneHotEncoder。
4. 数值特征直接输入或标准化。
5. 划分训练集和测试集。
6. 训练随机森林回归模型。
7. 输出 MAE、MSE、RMSE 和 R2。
8. 保存模型文件和评估结果。

当有效训练数据不足时，预测接口使用同区域均价、同城市均价和面积估算兜底，并在结果中标明模型名称为规则估算。

## 管理与安全

1. Django Admin 管理城市、区域、房源、采集任务、分析结果和预测记录。
2. 管理接口要求登录或管理员权限。
3. 查询参数进行类型和范围校验。
4. 数据库连接信息通过环境变量或本地配置文件读取，不暴露到前端。
5. 真实爬虫扩展时必须遵守 robots 协议并控制请求频率。

## 验证计划

需要通过以下验证：

1. `python manage.py check`
2. `python manage.py makemigrations`
3. `python manage.py migrate`
4. `python manage.py seed_demo_data`
5. `python manage.py generate_analysis`
6. `python manage.py train_price_model`
7. 访问首页、省级分析、城市分析、房源列表、房源详情和预测页面。
8. 测试房源列表、详情、统计和预测 API。
9. 至少覆盖清洗逻辑、统计逻辑和预测兜底逻辑的自动化测试。

## 交付物

最终交付：

1. 完整 Django 项目源码。
2. MySQL 建库脚本。
3. `.env.example` 配置样例。
4. 示例房源数据。
5. 清洗、分析、预测命令。
6. 前端页面和 JSON API。
7. Django Admin 后台。
8. README 运行文档。
9. 测试用例和验证记录。

## 后续扩展

后续可以扩展：

1. 接入真实 Scrapy 爬虫。
2. 接入 Redis 和 Scrapy-Redis。
3. 接入百度地图 API。
4. 增加租房数据。
5. 增加收藏、房源对比和数据导出。
6. 增加定时采集和自动训练模型。
