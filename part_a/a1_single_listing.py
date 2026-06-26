"""
A.1 使用 Request + XPath + 正则表达式 爬取青岛市李沧区单套房源信息
====================================================================
任务目标：
  从 http://node4:8000/details/?line=/qingdao/licang/103127976551.html
  爬取房源的全部数据，为后期全站爬取建立基础。

爬取字段（共21个）：
  基础：房子单价、所在区域、小区名称
  房屋属性：房屋户型、户型结构、所在楼层、建筑面积、房屋朝向、建筑结构、装修情况
  交易信息：梯户比例、挂牌时间、交易权属、产权所属、抵押信息
  介绍：核心卖点、小区介绍、户型介绍、交通出行
  坐标：经度、纬度

技术要点：
  1. 使用 Chrome DevTools (F12) 分析网页结构，定位目标节点
  2. 使用 requests 库发起 HTTP 请求获取页面 HTML
  3. 使用 lxml+XPath 定位节点并提取文本
  4. 使用 re (正则表达式) 清洗数据（去标签、去单位、提取数字）
  5. 结果保存为 CSV 和 JSON

任务步骤：
  步骤1 — 分析网页，确定网页规则及节点信息
  步骤2 — 访问网页，读取网页内容
  步骤3 — 获取节点数据，解析并打印内容
"""

import requests
import json
import csv
import os
import time
import re
import io
import sys
import os

# 将项目根目录加入 sys.path（解决直接运行时找不到 config 模块的问题）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lxml import etree

# 修复终端编码问题
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except (AttributeError, OSError):
        pass

# 导入项目配置
from config import (
    HEADERS, REQUEST_TIMEOUT, RAW_DIR,
    build_detail_url, SHANDONG_CITIES, DETAIL_URL,
)


# ================================================================
#  步骤1：分析网页 — 确定目标 URL 和 User-Agent
# ================================================================
# 目标房源 URL（青岛李沧区，房源ID=103127976551）
CITY = "青岛"
CITY_PINYIN = SHANDONG_CITIES[CITY]          # "qingdao"
DISTRICT = "李沧"
DISTRICT_PINYIN = "licang"                    # 李沧区拼音
HOUSE_ID = "103127976551"                     # 房源编号

# 构造完整请求 URL
TARGET_URL = build_detail_url(CITY_PINYIN, DISTRICT_PINYIN, HOUSE_ID)
# → http://node4:8000/details/?line=/qingdao/licang/103127976551.html

# User-Agent 已在 config.py 中配置（模拟 Chrome 浏览器）
# 可通过 Chrome F12 → Network → Request Headers 获取


# ================================================================
#  步骤2：访问网页，读取网页内容
# ================================================================
def fetch_page(url: str) -> str:
    """
    使用 requests 库发起 GET 请求，获取页面 HTML 文本。

    关键点：
    - 使用 session 保持连接
    - 设置 User-Agent 模拟浏览器
    - 设置超时避免无限等待
    - 指定 utf-8 编码正确处理中文
    """
    print(f"\n[步骤2] 正在请求页面...")
    print(f"  URL: {url}")

    session = requests.Session()
    try:
        resp = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            raise Exception(f"HTTP 状态码异常: {resp.status_code}")

        html = resp.text
        print(f"  [OK] 页面获取成功")
        print(f"  响应长度: {len(html)} 字符")
        print(f"  状态码: {resp.status_code}")
        return html

    except requests.exceptions.Timeout:
        raise Exception(f"请求超时（>{REQUEST_TIMEOUT}秒），请检查网络或服务器状态")
    except requests.exceptions.ConnectionError:
        raise Exception(f"连接失败，请确认服务器 {url} 是否可访问")
    except Exception as e:
        raise Exception(f"请求失败: {e}")


# ================================================================
#  步骤3：获取节点数据 — XPath 定位 + 正则清洗
# ================================================================
def parse_house_detail(html: str, url: str) -> dict:
    """
    使用 XPath 定位节点 + 正则表达式清洗数据。

    XPath 用于精确定位 HTML 中的目标元素；
    正则表达式用于从文本中提取/清洗数值和标签。

    F12 分析网页结构（以链家详情页为例）：
    ┌─────────────────────────────────────────────────┐
    │ h1.main          → 房源标题                       │
    │ span.total       → 总价（万元）                    │
    │ span.unitPriceValue → 单价（元/㎡）                │
    │ div.communityName > a → 小区名称                   │
    │ div.areaName > a     → 区域/商圈                   │
    │                                                   │
    │ div.base > div.content > ul > li                  │
    │   → 房屋户型、户型结构、楼层、面积、朝向、建筑结构等    │
    │                                                   │
    │ div.transaction > div.content > ul > li           │
    │   → 挂牌时间、交易权属、产权所属、抵押信息等          │
    │                                                   │
    │ div.introContent > ul > li                        │
    │   → 核心卖点、小区介绍、户型介绍、交通出行            │
    │                                                   │
    │ <meta itemprop="longitude/latitude">              │
    │   → 经度、纬度（需查看 HTML 源代码）                 │
    └─────────────────────────────────────────────────┘
    """
    # 构建 XPath 解析树
    tree = etree.HTML(html)

    # 初始化结果字典（按类别组织）
    data = {
        # 元信息
        "url": url,
        "city": CITY,
        "district": DISTRICT,
    }

    # ---------- 辅助函数 ----------
    def xpath_text(xpath_expr: str, default: str = "") -> str:
        """XPath 取文本，失败返回默认值"""
        result = tree.xpath(xpath_expr)
        if result:
            text = str(result[0]).strip() if isinstance(result[0], str) else "".join(result[0].xpath(".//text()")).strip()
            return text
        return default

    def clean_with_regex(text: str) -> str:
        """正则清洗：去 HTML 标签、压缩空白、去首尾符号"""
        text = re.sub(r'<[^>]+>', '', text)           # 去标签
        text = re.sub(r'\s+', ' ', text)              # 压缩空白
        text = text.strip(" ：:。·\t\n\r")            # 去首尾符号
        return text

    def extract_number(text: str) -> str:
        """正则提取数值（含小数点），如 '128.5万' → '128.5'"""
        match = re.search(r'[\d.]+', str(text))
        return match.group() if match else ""

    # ================================================================
    #  3.1 基础信息（标题、价格、小区、区域）
    # ================================================================
    # 标题 — XPath: //h1[@class="main"]/text()
    data["title"] = xpath_text('//h1[@class="main"]/text()')
    if not data["title"]:
        # 备选：从 <title> 标签获取
        data["title"] = xpath_text('//title/text()')

    # 总价（万元）— XPath: //span[@class="total"]/text()
    total_text = xpath_text('//span[@class="total"]/text()')
    data["total_price_wan"] = extract_number(total_text) if total_text else ""

    # 房子单价（元/㎡）— XPath: //span[@class="unitPriceValue"]/text()
    unit_text = xpath_text('//span[@class="unitPriceValue"]/text()')
    data["unit_price_yuan"] = extract_number(unit_text) if unit_text else ""

    # 小区名称 — XPath: //div[@class="communityName"]/a[1]/text()
    data["community"] = xpath_text('//div[@class="communityName"]/a[1]/text()')

    # 所在区域 & 商圈 — XPath: //div[@class="areaName"]//a/text()
    area_nodes = tree.xpath('//div[@class="areaName"]//a/text()')
    data["biz_circle"] = area_nodes[1].strip() if len(area_nodes) > 1 else ""

    print(f"\n  [3.1 基础信息]")
    print(f"    标题: {data['title'][:50] if data['title'] else 'N/A'}...")
    print(f"    总价: {data['total_price_wan']}万 | 单价: {data['unit_price_yuan']}元/㎡")
    print(f"    小区: {data['community']} | 商圈: {data['biz_circle']}")

    # ================================================================
    #  3.2 房屋属性（从 div.base 区块的 li 遍历解析）
    #  字段：房屋户型、户型结构、所在楼层、建筑面积、房屋朝向、
    #        建筑结构、装修情况、梯户比例、建筑类型
    # ================================================================
    base_items = tree.xpath('//div[@class="base"]//li')
    for li in base_items:
        # 获取 li 下所有文本，拼接为完整字符串
        text = "".join(li.xpath(".//text()")).strip()
        text = clean_with_regex(text)

        if not text:
            continue

        # 使用正则匹配关键词并提取值
        # 房屋户型（如"3室2厅1厨2卫"）
        if "房屋户型" in text:
            data["layout"] = re.sub(r'房屋户型\s*', '', text).strip(" ：:。")
        # 户型结构（如"平层"/"跃层"/"复式"）
        elif "户型结构" in text:
            data["layout_structure"] = re.sub(r'户型结构\s*', '', text).strip(" ：:。")
        # 所在楼层（如"低楼层/共6层"）
        elif "所在楼层" in text:
            data["floor"] = re.sub(r'所在楼层\s*', '', text).strip(" ：:。")
        # 建筑面积（如"89.5㎡"）
        elif "建筑面积" in text:
            val = re.sub(r'建筑面积\s*', '', text).strip(" ：:。")
            data["area_sqm"] = val
        # 房屋朝向（如"南"/"南北通透"）
        elif "房屋朝向" in text:
            data["orientation"] = re.sub(r'房屋朝向\s*', '', text).strip(" ：:。")
        # 建筑结构（如"钢混结构"/"砖混结构"）
        elif "建筑结构" in text:
            data["building_structure"] = re.sub(r'建筑结构\s*', '', text).strip(" ：:。")
        # 建筑类型（如"板楼"/"塔楼"）
        elif "建筑类型" in text:
            data["building_type"] = re.sub(r'建筑类型\s*', '', text).strip(" ：:。")
        # 装修情况（如"精装"/"简装"/"毛坯"）
        elif "装修情况" in text:
            data["decoration"] = re.sub(r'装修情况\s*', '', text).strip(" ：:。")
        # 建成年份
        elif "建筑年代" in text or "年代" in text:
            data["build_year"] = re.sub(r'建筑年代\s*|年代\s*', '', text).strip(" ：:。")
        # 梯户比例（如"一梯两户"）
        elif "梯户比例" in text:
            data["elevator_ratio"] = re.sub(r'梯户比例\s*', '', text).strip(" ：:。")
        # 供暖方式
        elif "供暖方式" in text:
            data["heating"] = re.sub(r'供暖方式\s*', '', text).strip(" ：:。")
        # 配备电梯
        elif "配备电梯" in text:
            data["has_elevator"] = re.sub(r'配备电梯\s*', '', text).strip(" ：:。")
        # 产权年限
        elif "产权年限" in text and "产权所属" not in text:
            data["property_rights"] = re.sub(r'产权年限\s*', '', text).strip(" ：:。")

    print(f"\n  [3.2 房屋属性]")
    print(f"    户型: {data.get('layout','?')} | 户型结构: {data.get('layout_structure','?')}")
    print(f"    面积: {data.get('area_sqm','?')} | 朝向: {data.get('orientation','?')}")
    print(f"    楼层: {data.get('floor','?')} | 装修: {data.get('decoration','?')}")
    print(f"    建筑结构: {data.get('building_structure','?')} | 建筑类型: {data.get('building_type','?')}")

    # ================================================================
    #  3.3 交易属性（从 div.transaction 区块的 li 遍历解析）
    #  字段：挂牌时间、交易权属、产权所属、抵押信息
    # ================================================================
    tx_items = tree.xpath('//div[@class="transaction"]//li')
    for li in tx_items:
        text = "".join(li.xpath(".//text()")).strip()
        text = clean_with_regex(text)

        if not text:
            continue

        # 挂牌时间（如"2024-03-15"）
        if "挂牌时间" in text:
            data["listing_time"] = re.sub(r'挂牌时间\s*', '', text).strip(" ：:。")
        # 交易权属（如"商品房"/"经济适用房"）
        elif "交易权属" in text:
            data["transaction_ownership"] = re.sub(r'交易权属\s*', '', text).strip(" ：:。")
        # 产权所属（如"共有"/"非共有"/"个人"）
        elif "产权所属" in text:
            data["property_ownership"] = re.sub(r'产权所属\s*', '', text).strip(" ：:。")
        # 抵押信息（如"无抵押"/"有抵押 xxx万"）
        elif "抵押信息" in text:
            data["mortgage_info"] = re.sub(r'抵押信息\s*', '', text).strip(" ：:。")
        # 房屋用途
        elif "房屋用途" in text:
            data["usage"] = re.sub(r'房屋用途\s*', '', text).strip(" ：:。")
        # 上次交易
        elif "上次交易" in text:
            data["last_trade"] = re.sub(r'上次交易\s*', '', text).strip(" ：:。")
        # 房本年限
        elif "房本年限" in text:
            data["deed_year"] = re.sub(r'房本年限\s*', '', text).strip(" ：:。")
        # 补充产权年限（如果在 base 没抓到）
        elif "产权年限" in text and not data.get("property_rights"):
            data["property_rights"] = re.sub(r'产权年限\s*', '', text).strip(" ：:。")

    print(f"\n  [3.3 交易信息]")
    print(f"    挂牌时间: {data.get('listing_time','?')}")
    print(f"    交易权属: {data.get('transaction_ownership','?')}")
    print(f"    产权所属: {data.get('property_ownership','?')}")
    print(f"    抵押信息: {data.get('mortgage_info','?')}")

    # ================================================================
    #  3.4 配套介绍（核心卖点、小区介绍、户型介绍、交通出行）
    #  来源1：div.introContent > ul > li（推荐）
    #  来源2：全页文本正则分段提取（备选）
    # ================================================================
    intro_items = tree.xpath('//div[contains(@class, "introContent")]//li')
    if intro_items:
        for li in intro_items:
            # 提取标签和内容
            label_texts = li.xpath('./span[@class="label"]/text()')
            if not label_texts:
                label_texts = li.xpath('./label/text()')
            label = label_texts[0].strip() if label_texts else ""

            # 提取内容（排除标签本身的文本）
            all_text = "".join(li.xpath(".//text()")).strip()
            content = clean_with_regex(all_text)

            if "核心卖点" in label:
                data["key_selling_points"] = re.sub(r'核心卖点\s*[：:]*\s*', '', content)
            elif "小区介绍" in label or "周边配套" in label:
                data["community_intro"] = re.sub(r'(小区介绍|周边配套)\s*[：:]*\s*', '', content)
            elif "户型介绍" in label or "户型特色" in label:
                data["layout_intro"] = re.sub(r'(户型介绍|户型特色)\s*[：:]*\s*', '', content)
            elif "交通出行" in label:
                data["transportation"] = re.sub(r'交通出行\s*[：:]*\s*', '', content)

    # 备选方案：从全文用正则分段提取
    intro_full = "".join(
        tree.xpath('//div[contains(@class, "introContent")]//text()')
    ).strip()

    for keyword, field in [
        ("核心卖点", "key_selling_points"),
        ("小区介绍", "community_intro"),
        ("户型介绍", "layout_intro"),
        ("交通出行", "transportation"),
    ]:
        if not data.get(field) and keyword in intro_full:
            # 正则匹配：关键词 + 冒号 + 内容（直到下一个关键词或结尾）
            pattern = re.escape(keyword) + r'\s*[：:]*\s*(.+?)(?=核心卖点|小区介绍|户型介绍|交通出行|周边配套|$)'
            match = re.search(pattern, intro_full, re.DOTALL)
            if match:
                data[field] = clean_with_regex(match.group(1))[:500]

    print(f"\n  [3.4 配套介绍]")
    for label, field in [("核心卖点","key_selling_points"), ("小区介绍","community_intro"),
                          ("户型介绍","layout_intro"), ("交通出行","transportation")]:
        val = data.get(field, "")
        preview = val[:60] + "..." if len(val) > 60 else val
        print(f"    {label}: {preview if val else 'N/A'}")

    # ================================================================
    #  3.5 地理坐标 — 从 <meta> 标签获取（需查看 HTML 源代码）
    #  XPath: //meta[@itemprop="longitude"]/@content
    # ================================================================
    data["longitude"] = xpath_text('//meta[@itemprop="longitude"]/@content')
    data["latitude"] = xpath_text('//meta[@itemprop="latitude"]/@content')

    # 正则备选：从 JS 代码中提取
    if not data["longitude"]:
        lon_match = re.search(r'"longitude":\s*([\d.]+)', html)
        if lon_match:
            data["longitude"] = lon_match.group(1)
    if not data["latitude"]:
        lat_match = re.search(r'"latitude":\s*([\d.]+)', html)
        if lat_match:
            data["latitude"] = lat_match.group(1)

    print(f"\n  [3.5 地理坐标]")
    print(f"    经度: {data['longitude'] or 'N/A'} | 纬度: {data['latitude'] or 'N/A'}")

    return data


# ================================================================
#  保存结果
# ================================================================
def save_result(data: dict, output_dir: str = RAW_DIR):
    """保存为 CSV 和 JSON"""
    house_id = HOUSE_ID
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # 保存 JSON（便于查看完整数据）
    json_path = os.path.join(output_dir, f"a1_single_house_{house_id}_{timestamp}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] JSON 已保存: {json_path}")

    # 保存 CSV（追加模式，便于后续批量处理）
    csv_path = os.path.join(output_dir, "a1_house_details.csv")
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(data.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
    print(f"[OK] CSV  已保存: {csv_path}")


# ================================================================
#  主流程
# ================================================================
def main():
    print("=" * 65)
    print("A.1 使用 Request + XPath + 正则表达式")
    print("    爬取青岛市李沧区单套房源信息")
    print("=" * 65)

    # ---- 步骤1：分析网页 ----
    print(f"\n{'='*65}")
    print("步骤1 — 分析网页结构")
    print(f"{'='*65}")
    print(f"  目标城市: {CITY} ({CITY_PINYIN})")
    print(f"  目标区域: {DISTRICT} ({DISTRICT_PINYIN})")
    print(f"  房源ID:   {HOUSE_ID}")
    print(f"  请求URL:  {TARGET_URL}")
    print(f"  User-Agent: {HEADERS['User-Agent'][:60]}...")
    print()
    print("  F12 开发者工具分析要点：")
    print("  - Network → Doc → 查看请求头和响应")
    print("  - Elements → 定位目标节点（h1.main, span.total, div.base 等）")
    print("  - 右键 → 查看网页源代码 → 搜索经纬度 meta 标签")

    # ---- 步骤2：访问网页 ----
    print(f"\n{'='*65}")
    print("步骤2 — 访问网页，读取网页内容")
    print(f"{'='*65}")

    try:
        html = fetch_page(TARGET_URL)
    except Exception as e:
        print(f"\n  [FAIL] {e}")
        print("\n  排错建议：")
        print("  1. 确认服务器 http://node4:8000 是否运行")
        print("  2. 检查 URL 中的 line 参数路径是否正确")
        print("  3. 尝试在浏览器中直接访问该 URL")
        print("  4. 检查防火墙/代理设置")
        return

    # ---- 步骤3：解析数据 ----
    print(f"\n{'='*65}")
    print("步骤3 — 使用 XPath + 正则表达式解析节点数据")
    print(f"{'='*65}")

    data = parse_house_detail(html, TARGET_URL)

    # ---- 汇总输出 ----
    print(f"\n{'='*65}")
    print("解析汇总")
    print(f"{'='*65}")

    # 统计有值的字段数
    filled = sum(1 for v in data.values() if v)
    total = len(data)
    print(f"  共解析 {total} 个字段，其中 {filled} 个有值 ({filled*100//total}%)")

    # 列出所有字段
    field_labels = {
        "基础信息": ["title", "total_price_wan", "unit_price_yuan", "community", "biz_circle"],
        "房屋属性": ["layout", "layout_structure", "floor", "area_sqm", "orientation",
                   "building_structure", "building_type", "decoration", "build_year"],
        "交易信息": ["listing_time", "transaction_ownership", "property_ownership",
                   "property_rights", "mortgage_info", "usage", "deed_year",
                   "elevator_ratio", "has_elevator", "heating"],
        "配套介绍": ["key_selling_points", "community_intro", "layout_intro", "transportation"],
        "地理坐标": ["longitude", "latitude"],
    }
    for category, fields in field_labels.items():
        filled_in_cat = [f for f in fields if data.get(f)]
        print(f"  [{category}] {len(filled_in_cat)}/{len(fields)} 个有值: {', '.join(filled_in_cat)}")

    # ---- 保存 ----
    print(f"\n{'='*65}")
    print("保存结果")
    print(f"{'='*65}")
    save_result(data)

    print(f"\n[完成] A.1 运行结束。数据已保存到 {RAW_DIR}/")


if __name__ == "__main__":
    main()
