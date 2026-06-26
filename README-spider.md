# 二手房房源爬取、分析与房价预测

基于 Python 的链家二手房数据爬取与房价分析预测系统。

## 项目结构

```
lesson_liu/
├── config.py                     # 全局配置（请求头、城市映射、路径）
├── requirements.txt              # Python 依赖
├── part_a/                       # A 部分：爬虫
│   ├── a1_single_listing.py      # A.1 单套房源爬取 (Request+XPath)
│   ├── a2_city_links.py          # A.2 各城市各地区链接爬取
│   ├── a3_all_listing_links.py   # A.3 所有房源链接整理
│   └── a4_distributed_crawl.py   # A.4 分布式爬虫 (Scrapy-Redis)
├── part_b/                       # B 部分：分析与预测
│   ├── b1_data_cleaning.py       # B.1 数据清洗
│   ├── b2_shandong_analysis.py   # B.2 山东省各城市分析
│   ├── b3_jinan_analysis.py      # B.3 济南市房源分析
│   └── b4_price_prediction.py    # B.4 房价预测模型
└── data/
    ├── raw/                      # 原始爬取数据
    ├── processed/                # 清洗后数据
    ├── figures/                  # 分析图表
    └── models/                   # 训练好的模型
```

## 环境配置

```bash
# 激活 conda 环境
conda activate house_scraper

# 或重新创建
conda create -n house_scraper python=3.10 -y
conda activate house_scraper
pip install -r requirements.txt
```

## Part A：爬取二手房信息

### A.1 单套房源爬取

```bash
python part_a/a1_single_listing.py
```

使用 `requests` 获取页面，`lxml` + XPath 解析房源详情：
- 标题、总价、单价
- 户型、面积、朝向、楼层、装修
- 小区名称、区域、商圈
- 经纬度坐标

### A.2 城市 & 区域链接

```bash
python part_a/a2_city_links.py
```

- 从链家城市列表页获取山东省各城市子域名
- 爬取每个城市下的行政区链接
- 结果保存到 `data/raw/a2_shandong_district_links.json`

### A.3 所有房源链接

```bash
# 测试模式（每个区只爬3页）
python part_a/a3_all_listing_links.py --test

# 全量爬取
python part_a/a3_all_listing_links.py
```

遍历所有行政区列表页，提取所有房源详情 URL。

### A.4 分布式爬虫

```bash
# 单机模式
python part_a/a4_distributed_crawl.py --standalone

# 分布式模式（需 Redis）
python part_a/a4_distributed_crawl.py --push-urls    # 推送URL到Redis
scrapy runspider part_a/a4_distributed_crawl.py       # 启动爬虫
```

基于 Scrapy-Redis 的分布式爬虫：
- Master 节点运行 Redis，维护 URL 队列
- Slave 节点运行 Spider，从 Redis 取任务
- 支持多机并行爬取
- 结果自动去重

## Part B：数据分析与预测

### B.1 数据清洗

```bash
python part_b/b1_data_cleaning.py
```

- 缺失值处理（中位数/众数填充）
- 数值字段解析（去除单位）
- 异常值过滤（面积 20-500㎡、总价 10-5000万）
- 特征衍生（房龄、log变换）

### B.2 山东省分析

```bash
python part_b/b2_shandong_analysis.py
```

- 各城市房源数量分布
- 各城市均价、总价对比
- 面积、房龄分布
- 可视化：柱状图、箱线图、热力图

### B.3 济南市分析

```bash
python part_b/b3_jinan_analysis.py
```

- 济南各区房源分析
- 价格影响因素（面积、房龄、朝向、装修、楼层）
- 热门小区排行
- 空间分布可视化

### B.4 房价预测模型

```bash
python part_b/b4_price_prediction.py
```

训练并对比多个模型：
- 线性回归 / Ridge / Lasso
- 随机森林
- 梯度提升 (GBDT)
- XGBoost

评估指标：R²、MAE、RMSE、MAPE、交叉验证

## 技术栈

| 功能 | 技术 |
|------|------|
| HTTP 请求 | requests |
| 页面解析 | lxml (XPath) |
| 分布式爬虫 | Scrapy + Scrapy-Redis |
| 数据清洗 | pandas, numpy |
| 可视化 | matplotlib, seaborn |
| 机器学习 | scikit-learn, XGBoost |

## 注意事项

1. **遵守 robots.txt**：请在实际使用时检查目标网站的爬虫协议
2. **请求延迟**：config.py 中 `REQUEST_DELAY=2`，避免请求过快被封 IP
3. **Cookie**：如遇反爬，请在 `config.py` 的 `HEADERS` 中添加 Cookie
4. **分布式爬虫**：需要先安装并启动 Redis 服务
5. **数据格式**：链家网站结构可能更新，如 XPath 失效请根据新页面调整
