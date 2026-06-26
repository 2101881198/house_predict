"""
HouseSpider — 分布式爬虫核心

功能：
  1. 从 Redis 队列获取待爬 URL
  2. 解析房源详情页，提取全部 23 个字段
  3. 数据通过 Pipeline 写入 Redis（再由独立脚本同步到 MySQL）

执行方式：
  # 在项目根目录 (house_scrapy/) 下执行
  scrapy crawl house_spider

  # 或指定 Spider 名称
  scrapy runspider house_spider/spiders/HouseSpider.py

节点部署：
  - node1（主节点）: Redis + MySQL + 爬虫
  - node2（从节点）: Redis + 爬虫
  - node3（从节点）: Redis + 爬虫
  - 3 台机器同时运行此爬虫，Redis 自动分配任务
"""

import re
import time
import scrapy

from house_spider.items import HouseItem


class HouseSpider(scrapy.Spider):
    """
    二手房房源爬虫

    单机模式（默认）：从 a3_listing_urls.txt 加载 URL
    分布式模式：继承 RedisSpider 从 Redis 队列获取 URL
    """
    name = "house_spider"

    # 域名
    allowed_domains = ["node4:8000"]

    # 单机模式时可限制测试条数
    max_items = None  # None=全量，设置数字则只爬前N条

    def __init__(self, standalone=True, max_items=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.standalone = standalone
        if max_items:
            self.max_items = int(max_items)
        self.page_count = 0

    def start_requests(self):
        """从本地文件加载 URL 列表"""
        urls = self._load_urls_from_file()
        if self.max_items:
            urls = urls[:self.max_items]
        self.logger.info(f"单机模式: 共 {len(urls)} 条 URL 待爬取")
        for url in urls:
            yield scrapy.Request(url, callback=self.parse)

    def _load_urls_from_file(self):
        """单机备用：从本地 txt 文件读取 URL 列表"""
        import os
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "..", "..", "data", "raw", "a3_listing_urls.txt"
        )
        if not os.path.exists(filepath):
            self.logger.warning(f"URL 文件不存在: {filepath}")
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    # ---------- 页面解析 ----------
    def parse(self, response):
        """
        解析房源详情页。

        XPath 节点定位 + 正则表达式清洗数据。

        节点表达式参考任务3（A.1）的分析结果：
        ┌──────────────────────────────────────────────────────┐
        │ XPath 映射表                                          │
        ├──────────────────────────────────────────────────────┤
        │ 标题:       //h1[@class="main"]/text()                │
        │ 总价:       //span[@class="total"]/text()             │
        │ 单价:       //span[@class="unitPriceValue"]/text()    │
        │ 小区:       //div[@class="communityName"]/a[1]/text() │
        │ 区域:       //div[@class="areaName"]//a/text()        │
        │ 基本信息:    //div[@class="base"]//li                  │
        │ 交易信息:    //div[@class="transaction"]//li           │
        │ 介绍:       //div[contains(@class,"introContent")]//li│
        │ 经度:       //meta[@itemprop="longitude"]/@content    │
        │ 纬度:       //meta[@itemprop="latitude"]/@content     │
        └──────────────────────────────────────────────────────┘
        """
        item = HouseItem()
        item["url"] = response.url
        item["crawl_time"] = time.strftime("%Y-%m-%d %H:%M:%S")

        self.page_count += 1
        if self.page_count % 100 == 0:
            self.logger.info(f"已爬取 {self.page_count} 套房源")

        # ========================
        #  XPath 辅助函数
        # ========================
        def xpath_first(path, default=""):
            r = response.xpath(path).get()
            return r.strip() if r else default

        def clean(text):
            """正则清洗：去标签、压缩空白、去首尾符号"""
            if not text:
                return ""
            text = re.sub(r'<[^>]+>', '', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip(" ：:。·\t\n\r")

        # ========================
        #  城市 & 地区 — 从 URL 提取
        #  URL 格式: .../?line=/qingdao/licang/xxx.html
        # ========================
        line_match = re.search(r'line=/(\w+)/(\w+)/(\d+)\.html', response.url)
        if line_match:
            city_pinyin = line_match.group(1)
            district_pinyin = line_match.group(2)

            # 拼音→中文映射
            PINYIN_TO_CITY = {
                "qingdao": "青岛", "jinan": "济南", "yantai": "烟台",
                "weihai": "威海", "zibo": "淄博", "linyi": "临沂",
                "weifang": "潍坊", "jining": "济宁", "taian": "泰安",
                "dezhou": "德州", "liaocheng": "聊城", "binzhou": "滨州",
                "heze": "菏泽", "rizhao": "日照", "zaozhuang": "枣庄",
                "dongying": "东营",
            }
            item["city"] = PINYIN_TO_CITY.get(city_pinyin, city_pinyin)
            item["district"] = district_pinyin

        # ========================
        #  基础信息
        # ========================
        item["house_title"] = (
            xpath_first('//h1[@class="main"]/text()') or
            xpath_first('//title/text()')
        )
        total_text = xpath_first('//span[@class="total"]/text()')
        item["total_price"] = re.search(r'[\d.]+', total_text).group() if total_text else ""

        unit_text = xpath_first('//span[@class="unitPriceValue"]/text()')
        item["unit_price"] = re.search(r'[\d.]+', unit_text).group() if unit_text else ""

        item["community_name"] = xpath_first('//div[@class="communityName"]/a[1]/text()')

        # 区域 & 商圈
        area_nodes = response.xpath('//div[@class="areaName"]//a/text()').getall()
        if len(area_nodes) >= 2:
            item["area_name"] = f"{area_nodes[0].strip()} {area_nodes[1].strip()}"
            item["biz_circle"] = area_nodes[1].strip()

        # ========================
        #  房屋属性（base 区块）
        # ========================
        for li in response.xpath('//div[@class="base"]//li'):
            raw = "".join(li.xpath(".//text()").getall()).strip()
            text = clean(raw)
            if not text:
                continue

            if "房屋户型" in text:
                item["house_layout"] = re.sub(r'房屋户型\s*', '', text).strip(" ：:。")
            elif "户型结构" in text:
                item["layout_structure"] = re.sub(r'户型结构\s*', '', text).strip(" ：:。")
            elif "所在楼层" in text:
                item["floor_position"] = re.sub(r'所在楼层\s*', '', text).strip(" ：:。")
            elif "建筑面积" in text:
                item["building_area"] = re.sub(r'建筑面积\s*', '', text).strip(" ：:。")
            elif "房屋朝向" in text:
                item["orientation"] = re.sub(r'房屋朝向\s*', '', text).strip(" ：:。")
            elif "建筑结构" in text:
                item["building_structure"] = re.sub(r'建筑结构\s*', '', text).strip(" ：:。")
            elif "建筑类型" in text:
                item["building_type"] = re.sub(r'建筑类型\s*', '', text).strip(" ：:。")
            elif "装修情况" in text:
                item["decoration"] = re.sub(r'装修情况\s*', '', text).strip(" ：:。")
            elif "建筑年代" in text or "年代" in text:
                item["build_year"] = re.sub(r'建筑年代|年代\s*', '', text).strip(" ：:。")
            elif "梯户比例" in text:
                item["elevator_ratio"] = re.sub(r'梯户比例\s*', '', text).strip(" ：:。")
            elif "供暖方式" in text:
                item["heating"] = re.sub(r'供暖方式\s*', '', text).strip(" ：:。")
            elif "配备电梯" in text:
                item["has_elevator"] = re.sub(r'配备电梯\s*', '', text).strip(" ：:。")
            elif "产权年限" in text and "产权所属" not in text:
                item["property_rights"] = re.sub(r'产权年限\s*', '', text).strip(" ：:。")

        # ========================
        #  交易属性（transaction 区块）
        # ========================
        for li in response.xpath('//div[@class="transaction"]//li'):
            raw = "".join(li.xpath(".//text()").getall()).strip()
            text = clean(raw)
            if not text:
                continue

            if "挂牌时间" in text:
                item["listing_time"] = re.sub(r'挂牌时间\s*', '', text).strip(" ：:。")
            elif "交易权属" in text:
                item["transaction_ownership"] = re.sub(r'交易权属\s*', '', text).strip(" ：:。")
            elif "产权所属" in text:
                item["property_ownership"] = re.sub(r'产权所属\s*', '', text).strip(" ：:。")
            elif "抵押信息" in text:
                item["mortgage_info"] = re.sub(r'抵押信息\s*', '', text).strip(" ：:。")
            elif "房屋用途" in text:
                item["usage"] = re.sub(r'房屋用途\s*', '', text).strip(" ：:。")
            elif "房本年限" in text:
                item["deed_year"] = re.sub(r'房本年限\s*', '', text).strip(" ：:。")
            elif "上次交易" in text:
                item["last_trade"] = re.sub(r'上次交易\s*', '', text).strip(" ：:。")
            elif "产权年限" in text and not item.get("property_rights"):
                item["property_rights"] = re.sub(r'产权年限\s*', '', text).strip(" ：:。")

        # ========================
        #  配套介绍（introContent 区块）
        # ========================
        for li in response.xpath('//div[contains(@class, "introContent")]//li'):
            label_texts = li.xpath('./span[@class="label"]/text()').getall()
            label = "".join(label_texts).strip() if label_texts else ""

            all_content = "".join(li.xpath('.//text()').getall()).strip()
            content = clean(all_content)

            if "核心卖点" in label:
                item["key_selling_points"] = re.sub(r'核心卖点\s*[：:]*\s*', '', content)
            elif "小区介绍" in label:
                item["community_intro"] = re.sub(r'小区介绍\s*[：:]*\s*', '', content)
            elif "户型介绍" in label:
                item["layout_intro"] = re.sub(r'户型介绍\s*[：:]*\s*', '', content)
            elif "交通出行" in label:
                item["transportation"] = re.sub(r'交通出行\s*[：:]*\s*', '', content)

        # 备选：正则从全文中提取
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
                pattern = (
                    re.escape(keyword) +
                    r'\s*[：:]*\s*(.+?)(?=核心卖点|小区介绍|户型介绍|交通出行|$)'
                )
                m = re.search(pattern, intro_full, re.DOTALL)
                if m:
                    item[field] = clean(m.group(1))[:500]

        # ========================
        #  地理坐标
        # ========================
        item["longitude"] = xpath_first('//meta[@itemprop="longitude"]/@content')
        item["latitude"] = xpath_first('//meta[@itemprop="latitude"]/@content')

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
