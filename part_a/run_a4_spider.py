"""
A.4 爬虫启动脚本 — 独立 Spider，不依赖 Redis
用法: python3 run_a4_spider.py [数量]
     python3 run_a4_spider.py          # 全量
     python3 run_a4_spider.py 100      # 只爬100条
"""
import sys, os, re, time

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import scrapy
from scrapy.crawler import CrawlerProcess

# URL 文件
URL_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "a3_listing_urls.txt")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "a4_house_details.csv")

MAX_ITEMS = int(sys.argv[1]) if len(sys.argv) > 1 else None


class A4HouseSpider(scrapy.Spider):
    """A.4 全量爬取 spider — 解析全部21个字段"""
    name = "a4_house"

    custom_settings = {
        "DOWNLOAD_DELAY": 0.3,
        "CONCURRENT_REQUESTS": 8,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
        "COOKIES_ENABLED": False,
        "RETRY_TIMES": 2,
        "DOWNLOAD_TIMEOUT": 15,
    }

    def start_requests(self):
        with open(URL_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
        if MAX_ITEMS:
            urls = urls[:MAX_ITEMS]
        self.logger.info(f"A.4 开始爬取: {len(urls)} 条 URL")
        for i, url in enumerate(urls):
            if i > 0 and i % 1000 == 0:
                self.logger.info(f"  已入队: {i}/{len(urls)}")
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        """解析房源详情页全部字段"""
        def xp(path, default=""):
            r = response.xpath(path).get()
            return r.strip() if r else default

        # 用正则清洗文本
        def clean(text):
            if not text:
                return ""
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip(" ：:。·\t\n\r")

        # 城市/区/ID 从 URL 提取
        m = re.search(r'line=/(\w+)/(\w+)/(\d+)\.html', response.url)
        city_py = m.group(1) if m else ""
        district_py = m.group(2) if m else ""
        house_id = m.group(3) if m else ""

        # ---- 基础信息 ----
        title = xp('//h1[@class="main"]/text()') or xp('//title/text()')
        total_price = xp('//span[@class="total"]/text()')
        unit_price = xp('//span[@class="unitPriceValue"]/text()')
        community = xp('//div[@class="communityName"]/a[1]/text()')

        area_nodes = response.xpath('//div[@class="areaName"]//a/text()').getall()
        if area_nodes:
            area_name = area_nodes[0].strip() if len(area_nodes) > 0 else ""
            biz_circle = area_nodes[1].strip() if len(area_nodes) > 1 else ""
        else:
            area_name = ""
            biz_circle = ""

        # ---- 房屋属性 ----
        base_data = {}
        for li in response.xpath('//div[@class="base"]//li'):
            text = clean("".join(li.xpath(".//text()").getall()))
            for keyword, key in [
                ("房屋户型", "house_layout"),
                ("户型结构", "layout_structure"),
                ("所在楼层", "floor"),
                ("建筑面积", "area"),
                ("房屋朝向", "orientation"),
                ("建筑结构", "building_structure"),
                ("建筑类型", "building_type"),
                ("装修情况", "decoration"),
                ("建筑年代", "build_year"),
                ("梯户比例", "elevator_ratio"),
                ("供暖方式", "heating"),
                ("配备电梯", "has_elevator"),
                ("产权年限", "property_rights"),
            ]:
                if keyword in text and key not in base_data:
                    base_data[key] = clean(re.sub(keyword + r'\s*', '', text))

        # ---- 交易属性 ----
        tx_data = {}
        for li in response.xpath('//div[@class="transaction"]//li'):
            text = clean("".join(li.xpath(".//text()").getall()))
            for keyword, key in [
                ("挂牌时间", "listing_time"),
                ("交易权属", "transaction_ownership"),
                ("产权所属", "property_ownership"),
                ("抵押信息", "mortgage_info"),
                ("房屋用途", "usage"),
                ("房本年限", "deed_year"),
                ("上次交易", "last_trade"),
                ("产权年限", "property_rights"),  # 可能在 transaction 中
            ]:
                if keyword in text and key not in tx_data:
                    tx_data[key] = clean(re.sub(keyword + r'\s*', '', text))

        # ---- 介绍 ----
        intro_data = {}
        for li in response.xpath('//div[contains(@class, "introContent")]//li'):
            label = clean("".join(li.xpath('./span[@class="label"]/text()').getall()))
            content = clean("".join(li.xpath('.//text()').getall()))
            for keyword, key in [
                ("核心卖点", "key_selling_points"),
                ("小区介绍", "community_intro"),
                ("户型介绍", "layout_intro"),
                ("交通出行", "transportation"),
            ]:
                if keyword in label:
                    intro_data[key] = clean(re.sub(keyword + r'\s*[：:]*\s*', '', content))

        # ---- 坐标 ----
        lon = xp('//meta[@itemprop="longitude"]/@content')
        lat = xp('//meta[@itemprop="latitude"]/@content')
        if not lon:
            m_lon = re.search(r'"longitude":\s*([\d.]+)', response.text)
            lon = m_lon.group(1) if m_lon else ""
        if not lat:
            m_lat = re.search(r'"latitude":\s*([\d.]+)', response.text)
            lat = m_lat.group(1) if m_lat else ""

        yield {
            "url": response.url,
            "city": city_py,
            "district": district_py,
            "house_id": house_id,
            "title": clean(title),
            "total_price_wan": total_price,
            "unit_price_yuan": unit_price,
            "community": community,
            "area_name": area_name,
            "biz_circle": biz_circle,
            **base_data, **tx_data, **intro_data,
            "longitude": lon,
            "latitude": lat,
            "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        }


def main():
    print("=" * 60)
    print("A.4 爬取所有房源信息")
    print(f"URL 文件: {URL_FILE}")
    with open(URL_FILE, "r") as f:
        total = sum(1 for _ in f)
    limit = min(MAX_ITEMS, total) if MAX_ITEMS else total
    print(f"待爬取: {limit} 条 (共 {total} 条)")
    print(f"输出: {OUTPUT_FILE}")
    print("=" * 60)

    settings = {
        "LOG_LEVEL": "INFO",
        "ROBOTSTXT_OBEY": False,
        "DOWNLOAD_DELAY": 0.3,
        "CONCURRENT_REQUESTS": 8,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 8,
        "RETRY_TIMES": 2,
        "DOWNLOAD_TIMEOUT": 15,
        "COOKIES_ENABLED": False,
        "FEEDS": {
            OUTPUT_FILE: {"format": "csv", "encoding": "utf-8-sig", "overwrite": True},
        },
    }

    process = CrawlerProcess(settings)
    process.crawl(A4HouseSpider)
    process.start()

    # 统计结果
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8-sig") as f:
            lines = sum(1 for _ in f) - 1  # 减去 header
        print(f"\n[完成] A.4 爬取结束: {lines} 条数据")
        print(f"输出文件: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
