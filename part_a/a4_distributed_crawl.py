"""
A.4 使用分布式爬虫爬取网站所有房源信息
===========================================
任务目标：
  基于 A.3 生成的所有房源链接，使用 Scrapy-Redis 分布式爬虫框架，
  在 3 台节点上并行爬取每套房源的详细数据（全部 21 个字段）。

架构：Scrapy 项目 + Scrapy-Redis 分布式
  详见: part_a/house_scrapy/ 项目目录

快速使用：
  # 1. 推送 URL 到 Redis
  python part_a/push_urls_to_redis.py

  # 2. 在各节点启动爬虫
  cd part_a/house_scrapy
  scrapy crawl house_spider

  # 3. 启动 Redis→MySQL 同步（独立进程）
  python part_a/redis_to_mysql.py

节点部署：
  node1(主): Redis + MySQL + 爬虫 + 同步脚本
  node2(从): Redis + 爬虫
  node3(从): Redis + 爬虫

URL 格式（代理服务器）：
  详情页: http://node4:8000/details/?line=/qingdao/licang/103127976551.html

使用方法：
  # 单机模式（不需要 Redis）
  python part_a/a4_distributed_crawl.py --standalone

  # 分布式模式（需要 Redis）
  1. python part_a/a4_distributed_crawl.py --push-urls   # 推送 URL 到 Redis
  2. scrapy runspider part_a/a4_distributed_crawl.py     # 启动爬虫（可多机并行）
"""

import os
import sys
import json
import time
import csv
import re
import io
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except (AttributeError, OSError):
        pass

import scrapy
from scrapy.crawler import CrawlerProcess

try:
    from scrapy_redis.spiders import RedisSpider
    HAS_SCRAPY_REDIS = True
except ImportError:
    HAS_SCRAPY_REDIS = False
    print("[提示] scrapy-redis 未安装，仅支持单机模式")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    HEADERS, REQUEST_DELAY, REQUEST_TIMEOUT,
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    RAW_DIR, SCRAPY_SETTINGS, SERVER_HOST, DETAIL_URL,
    SHANDONG_CITIES, PINYIN_TO_CITY,
)


# ============================================================
#  Scrapy Item — 全部 33 个字段
# ============================================================
class HouseItem(scrapy.Item):
    """房源数据 Item，与 A.1 字段完全对齐"""
    # 元信息
    url = scrapy.Field()
    title = scrapy.Field()
    crawl_time = scrapy.Field()

    # 基础信息
    total_price_wan = scrapy.Field()
    unit_price_yuan = scrapy.Field()
    community = scrapy.Field()
    city = scrapy.Field()
    district = scrapy.Field()
    biz_circle = scrapy.Field()

    # 房屋属性
    layout = scrapy.Field()
    layout_structure = scrapy.Field()
    area_sqm = scrapy.Field()
    orientation = scrapy.Field()
    floor = scrapy.Field()
    building_structure = scrapy.Field()
    building_type = scrapy.Field()
    decoration = scrapy.Field()
    build_year = scrapy.Field()

    # 交易信息
    elevator_ratio = scrapy.Field()
    has_elevator = scrapy.Field()
    heating = scrapy.Field()
    listing_time = scrapy.Field()
    transaction_ownership = scrapy.Field()
    property_ownership = scrapy.Field()
    property_rights = scrapy.Field()
    mortgage_info = scrapy.Field()
    usage = scrapy.Field()
    deed_year = scrapy.Field()
    last_trade = scrapy.Field()

    # 配套介绍
    key_selling_points = scrapy.Field()
    community_intro = scrapy.Field()
    layout_intro = scrapy.Field()
    transportation = scrapy.Field()

    # 地理坐标
    longitude = scrapy.Field()
    latitude = scrapy.Field()


# ============================================================
#  Scrapy Spider
# ============================================================
class LianjiaDistributedSpider(RedisSpider if HAS_SCRAPY_REDIS else scrapy.Spider):
    """
    分布式爬虫 Spider。

    分布式模式：继承 RedisSpider，从 Redis 队列 pop URL
    单机模式：从 A.3 生成的 URL 文件读取
    """
    name = "lianjia_house_distributed"
    redis_key = "lianjia:start_urls"
    allowed_domains = ["node4"]

    custom_settings = {
        **SCRAPY_SETTINGS,
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 16,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "ITEM_PIPELINES": {
            "__main__.LianjiaHousePipeline": 300,
        },
        "SCHEDULER": "scrapy_redis.scheduler.Scheduler" if HAS_SCRAPY_REDIS else "scrapy.core.scheduler.Scheduler",
        "DUPEFILTER_CLASS": "scrapy_redis.dupefilter.RFPDupeFilter" if HAS_SCRAPY_REDIS else "scrapy.dupefilters.RFPDupeFilter",
        "SCHEDULER_PERSIST": True,
        "REDIS_HOST": REDIS_HOST,
        "REDIS_PORT": REDIS_PORT,
        "REDIS_DB": REDIS_DB,
    }

    def __init__(self, standalone=False, url_file=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.standalone = standalone
        self.url_file = url_file

    def start_requests(self):
        """单机模式从文件读 URL，分布式模式由 Redis 提供"""
        if self.standalone or not HAS_SCRAPY_REDIS:
            urls = self._load_urls()
            for url in urls:
                yield scrapy.Request(url, callback=self.parse)
        else:
            yield from super().start_requests()

    def _load_urls(self):
        """加载 A.3 生成的 URL"""
        url_file = self.url_file or os.path.join(RAW_DIR, "a3_listing_urls.txt")
        if not os.path.exists(url_file):
            json_file = os.path.join(RAW_DIR, "a3_all_listing_links.json")
            if os.path.exists(json_file):
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                urls = []
                for d in data:
                    urls.extend(d.get("listing_urls", []))
                return urls
            raise FileNotFoundError(f"URL 文件不存在: {url_file}")
        with open(url_file, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    def parse(self, response):
        """
        解析房源详情页（全部字段）。

        使用 XPath 定位节点 + 正则表达式清洗文本。
        链家页面通过代理服务器返回，DOM 结构与原链家相同。
        """
        item = HouseItem()
        item["url"] = response.url
        item["crawl_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ---- XPath 辅助函数 ----
        def xp(path, default=""):
            r = response.xpath(path).get()
            return r.strip() if r else default

        # ---- 城市/区域从 URL 提取 ----
        # URL 格式: http://node4:8000/details/?line=/qingdao/licang/xxx.html
        line_match = re.search(r'line=/(\w+)/(\w+)/(\d+)\.html', response.url)
        if line_match:
            city_pinyin = line_match.group(1)
            district_pinyin = line_match.group(2)
            item["city"] = PINYIN_TO_CITY.get(city_pinyin, city_pinyin)
            item["district"] = district_pinyin

        # ========================
        #  基础信息
        # ========================
        item["title"] = xp('//h1[@class="main"]/text()') or xp('//title/text()')
        item["total_price_wan"] = xp('//span[@class="total"]/text()')
        item["unit_price_yuan"] = xp('//span[@class="unitPriceValue"]/text()')
        item["community"] = xp('//div[@class="communityName"]/a[1]/text()')

        area_nodes = response.xpath('//div[@class="areaName"]//a/text()').getall()
        if len(area_nodes) > 1:
            item["biz_circle"] = area_nodes[1].strip()

        # ========================
        #  房屋属性（base 区块）
        # ========================
        for li in response.xpath('//div[@class="base"]//li'):
            text = "".join(li.xpath(".//text()").getall()).strip()
            t = re.sub(r'\s+', ' ', text)

            if "房屋户型" in t:
                item["layout"] = re.sub(r'房屋户型\s*', '', t).strip(" ：:。")
            elif "户型结构" in t:
                item["layout_structure"] = re.sub(r'户型结构\s*', '', t).strip(" ：:。")
            elif "所在楼层" in t:
                item["floor"] = re.sub(r'所在楼层\s*', '', t).strip(" ：:。")
            elif "建筑面积" in t:
                item["area_sqm"] = re.sub(r'建筑面积\s*', '', t).strip(" ：:。")
            elif "房屋朝向" in t:
                item["orientation"] = re.sub(r'房屋朝向\s*', '', t).strip(" ：:。")
            elif "建筑结构" in t:
                item["building_structure"] = re.sub(r'建筑结构\s*', '', t).strip(" ：:。")
            elif "建筑类型" in t:
                item["building_type"] = re.sub(r'建筑类型\s*', '', t).strip(" ：:。")
            elif "装修情况" in t:
                item["decoration"] = re.sub(r'装修情况\s*', '', t).strip(" ：:。")
            elif "建筑年代" in t or "年代" in t:
                item["build_year"] = re.sub(r'建筑年代|年代\s*', '', t).strip(" ：:。")
            elif "梯户比例" in t:
                item["elevator_ratio"] = re.sub(r'梯户比例\s*', '', t).strip(" ：:。")
            elif "供暖方式" in t:
                item["heating"] = re.sub(r'供暖方式\s*', '', t).strip(" ：:。")
            elif "配备电梯" in t:
                item["has_elevator"] = re.sub(r'配备电梯\s*', '', t).strip(" ：:。")
            elif "产权年限" in t and "产权所属" not in t:
                item["property_rights"] = re.sub(r'产权年限\s*', '', t).strip(" ：:。")

        # ========================
        #  交易属性（transaction 区块）
        # ========================
        for li in response.xpath('//div[@class="transaction"]//li'):
            text = "".join(li.xpath(".//text()").getall()).strip()
            t = re.sub(r'\s+', ' ', text)

            if "挂牌时间" in t:
                item["listing_time"] = re.sub(r'挂牌时间\s*', '', t).strip(" ：:。")
            elif "交易权属" in t:
                item["transaction_ownership"] = re.sub(r'交易权属\s*', '', t).strip(" ：:。")
            elif "产权所属" in t:
                item["property_ownership"] = re.sub(r'产权所属\s*', '', t).strip(" ：:。")
            elif "抵押信息" in t:
                item["mortgage_info"] = re.sub(r'抵押信息\s*', '', t).strip(" ：:。")
            elif "房屋用途" in t:
                item["usage"] = re.sub(r'房屋用途\s*', '', t).strip(" ：:。")
            elif "房本年限" in t:
                item["deed_year"] = re.sub(r'房本年限\s*', '', t).strip(" ：:。")
            elif "上次交易" in t:
                item["last_trade"] = re.sub(r'上次交易\s*', '', t).strip(" ：:。")
            elif "产权年限" in t and not item.get("property_rights"):
                item["property_rights"] = re.sub(r'产权年限\s*', '', t).strip(" ：:。")

        # ========================
        #  配套介绍（introContent 区块）
        # ========================
        for li in response.xpath('//div[contains(@class, "introContent")]//li'):
            label = "".join(li.xpath('./span[@class="label"]/text()').getall()).strip()
            content = "".join(li.xpath('.//text()').getall()).strip()
            content = re.sub(r'<[^>]+>', '', content)

            if "核心卖点" in label:
                item["key_selling_points"] = re.sub(r'核心卖点\s*[：:]*\s*', '', content)
            elif "小区介绍" in label:
                item["community_intro"] = re.sub(r'小区介绍\s*[：:]*\s*', '', content)
            elif "户型介绍" in label:
                item["layout_intro"] = re.sub(r'户型介绍\s*[：:]*\s*', '', content)
            elif "交通出行" in label:
                item["transportation"] = re.sub(r'交通出行\s*[：:]*\s*', '', content)

        # 备选：正则分段提取
        intro_full = "".join(
            response.xpath('//div[contains(@class, "introContent")]//text()').getall()
        ).strip()
        for keyword, field in [
            ("核心卖点", "key_selling_points"),
            ("小区介绍", "community_intro"),
            ("户型介绍", "layout_intro"),
            ("交通出行", "transportation"),
        ]:
            if not item.get(field) and keyword in intro_full:
                pattern = re.escape(keyword) + r'\s*[：:]*\s*(.+?)(?=核心卖点|小区介绍|户型介绍|交通出行|$)'
                m = re.search(pattern, intro_full, re.DOTALL)
                if m:
                    item[field] = re.sub(r'\s+', ' ', m.group(1)).strip()[:500]

        # ========================
        #  地理坐标
        # ========================
        item["longitude"] = xp('//meta[@itemprop="longitude"]/@content')
        item["latitude"] = xp('//meta[@itemprop="latitude"]/@content')

        # 正则备选：从 JS 代码提取
        if not item["longitude"]:
            m = re.search(r'"longitude":\s*([\d.]+)', response.text)
            if m:
                item["longitude"] = m.group(1)
        if not item["latitude"]:
            m = re.search(r'"latitude":\s*([\d.]+)', response.text)
            if m:
                item["latitude"] = m.group(1)

        yield item


# ============================================================
#  Pipeline — 保存到 CSV
# ============================================================
class LianjiaHousePipeline:
    """将 Item 保存到 CSV 文件"""

    def __init__(self):
        self.file = None
        self.writer = None
        self.output_path = os.path.join(RAW_DIR, "a4_house_details.csv")
        self.file_exists = os.path.exists(self.output_path)

    def open_spider(self, spider):
        self.file = open(self.output_path, "a", newline="", encoding="utf-8-sig")
        fieldnames = list(HouseItem.fields.keys())
        self.writer = csv.DictWriter(self.file, fieldnames=fieldnames)
        if not self.file_exists:
            self.writer.writeheader()
        self.file.flush()

    def close_spider(self, spider):
        if self.file:
            self.file.close()

    def process_item(self, item, spider):
        if self.writer:
            self.writer.writerow(dict(item))
            self.file.flush()
        return item


# ============================================================
#  推送 URL 到 Redis
# ============================================================
def push_urls_to_redis():
    """将 A.3 生成的 URL 列表推入 Redis，供分布式爬虫消费"""
    try:
        import redis
    except ImportError:
        print("[FAIL] redis 库未安装，请运行: pip install redis")
        return

    r = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
        password=REDIS_PASSWORD, decode_responses=True,
    )

    url_file = os.path.join(RAW_DIR, "a3_listing_urls.txt")
    if not os.path.exists(url_file):
        print(f"[FAIL] URL 文件不存在: {url_file}")
        print("  请先运行 A.3: python part_a/a3_all_listing_links.py")
        return

    with open(url_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    key = "lianjia:start_urls"
    for url in urls:
        r.lpush(key, url)

    print(f"[OK] 已将 {len(urls)} 个 URL 推入 Redis: {key}")
    print(f"  现在可以启动爬虫: scrapy runspider part_a/a4_distributed_crawl.py")


# ============================================================
#  主入口
# ============================================================
def main():
    import sys
    standalone = "--standalone" in sys.argv
    push_mode = "--push-urls" in sys.argv

    if push_mode:
        print("=" * 65)
        print("A.4 推送 URL 到 Redis 队列")
        print("=" * 65)
        push_urls_to_redis()
        return

    print("=" * 65)
    if standalone or not HAS_SCRAPY_REDIS:
        print("A.4 单机模式 — 爬取所有房源信息")
    else:
        print("A.4 分布式爬虫模式")
    print("=" * 65)

    if standalone or not HAS_SCRAPY_REDIS:
        process = CrawlerProcess(settings={
            **SCRAPY_SETTINGS,
            "DOWNLOAD_DELAY": 0.5,
            "CONCURRENT_REQUESTS": 16,
            "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
            "ITEM_PIPELINES": {
                "__main__.LianjiaHousePipeline": 300,
            },
        })
        process.crawl(LianjiaDistributedSpider, standalone=True)
        process.start()
        print(f"\n[完成] 数据已保存到: {RAW_DIR}/a4_house_details.csv")
    else:
        print("""
分布式使用说明:
  1. 确保 Redis 服务已启动（{host}:{port}）
  2. 推送 URL 到 Redis:
     python part_a/a4_distributed_crawl.py --push-urls
  3. 启动爬虫（可在多台机器上同时运行）:
     scrapy runspider part_a/a4_distributed_crawl.py

单机模式（不需要 Redis）:
  python part_a/a4_distributed_crawl.py --standalone
        """.format(host=REDIS_HOST, port=REDIS_PORT))


if __name__ == "__main__":
    main()
