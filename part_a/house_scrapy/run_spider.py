"""
简化版 — 直接用 CrawlerProcess 启动爬虫，绕过 RedisSpider 初始化
"""
import sys, os, time, re, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy import signals

# 读取 URL 列表
url_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "..", "..", "data", "raw", "a3_listing_urls.txt")
with open(url_file, "r") as f:
    urls = [line.strip() for line in f if line.strip()]

print(f"加载了 {len(urls)} 个 URL")

# 简化版 Spider（不继承 RedisSpider）
class SimpleHouseSpider(scrapy.Spider):
    name = "simple_house"
    start_urls = urls[:10]  # 先测试10条

    custom_settings = {
        "DOWNLOAD_DELAY": 0.5,
        "CONCURRENT_REQUESTS": 4,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "INFO",
        "FEEDS": {
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "..", "..", "data", "raw", "a4_test_output.csv"): {
                "format": "csv",
                "encoding": "utf-8-sig",
            }
        },
    }

    def parse(self, response):
        def xp(path):
            r = response.xpath(path).get()
            return r.strip() if r else ""

        yield {
            "url": response.url,
            "title": xp('//h1[@class="main"]/text()') or xp('//title/text()'),
            "total_price": xp('//span[@class="total"]/text()'),
            "unit_price": xp('//span[@class="unitPriceValue"]/text()'),
            "community": xp('//div[@class="communityName"]/a[1]/text()'),
            "district": ",".join(response.xpath('//div[@class="areaName"]//a/text()').getall()),
            "layout": xp('//div[@class="base"]//li[contains(.,"房屋户型")]//text()'),
            "area": xp('//div[@class="base"]//li[contains(.,"建筑面积")]//text()'),
        }

# 启动
process = CrawlerProcess({
    "LOG_LEVEL": "INFO",
    "ROBOTSTXT_OBEY": False,
    "DOWNLOAD_DELAY": 0.5,
    "CONCURRENT_REQUESTS": 4,
    "FEEDS": {
        "data/test_output.csv": {"format": "csv", "encoding": "utf-8-sig"},
    },
})
process.crawl(SimpleHouseSpider)
process.start()
print("爬取完成!")
