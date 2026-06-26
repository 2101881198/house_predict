"""
调试 A.3 — 检查地区列表页是否返回房源列表
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from lxml import etree
from config import HEADERS, DETAIL_URL

# 测试青岛李沧区的列表页
test_urls = [
    f"{DETAIL_URL}?line=/qingdao/licang/",
    f"{DETAIL_URL}?line=/qingdao/shinan/",
    f"{DETAIL_URL}?line=/jinan/lixia/",
]

for url in test_urls:
    print(f"\n{'='*60}")
    print(f"URL: {url}")
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        html = resp.text
        tree = etree.HTML(html)
    except Exception as e:
        print(f"  请求失败: {e}")
        continue

    print(f"  响应长度: {len(html)}")

    # 找房源链接（.html 结尾的）
    house_links = tree.xpath('//a[contains(@href, ".html")]')
    print(f"  包含 .html 的链接: {len(house_links)} 个")

    # 找 sellListContent（列表页标志）
    sell_list = tree.xpath('//ul[contains(@class, "sellListContent")]')
    print(f"  sellListContent ul: {len(sell_list)} 个")

    # 找 page-box（分页器标志）
    page_box = tree.xpath('//div[contains(@class, "page-box")]')
    print(f"  page-box div: {len(page_box)} 个")

    # 找所有 /ershoufang/ 开头且 .html 结尾的链接
    house_urls = tree.xpath('//a[contains(@href, "/ershoufang/") and contains(@href, ".html")]/@href')
    print(f"  房源链接(/ershoufang/xxx.html): {len(house_urls)} 个")
    for href in house_urls[:5]:
        print(f"    {href}")

    # 找所有 a 标签文本包含"室"的（户型特征）
    room_links = tree.xpath('//a[contains(text(), "室")]')
    print(f"  含'室'字的链接: {len(room_links)} 个")

    # 取页面中的主要文本（判断是否列表页）
    body_text = "".join(tree.xpath('//body//text()')).strip()
    # 统计关键字
    keywords = ["房源", "二手房", "共找到", "套", "在售", "均价"]
    for kw in keywords:
        count = body_text.count(kw)
        if count > 0:
            print(f"  关键字'{kw}'出现: {count} 次")
