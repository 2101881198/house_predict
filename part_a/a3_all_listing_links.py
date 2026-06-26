"""
A.3 爬取和整理网站所有房源链接
====================================
通过 /list 端点遍历每个地区的分页列表，
提取所有房源详情页 URL，为 A.4 分布式爬虫提供种子 URL。

URL 体系（node4 代理）：
  列表页: http://node4:8000/list?line=/qingdao/licang&page=1
  详情页: http://node4:8000/details/?line=/qingdao/licang/xxx.html

执行方式：
  python part_a/a3_all_listing_links.py          # 全量
  python part_a/a3_all_listing_links.py --test   # 测试（每区1页）
"""

import os
import re
import json
import time
import sys
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from lxml import etree
from config import HEADERS, REQUEST_TIMEOUT, REQUEST_DELAY, RAW_DIR


def load_district_links() -> list:
    """加载 A.2 生成的地区链接"""
    path = os.path.join(RAW_DIR, "a2_district_urls.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            districts = json.load(f)
        print(f"[1] 从 A.2 加载: {len(districts)} 个地区")
        return districts
    print("[FAIL] 未找到 a2_district_urls.json，请先运行 A.2")
    sys.exit(1)


def get_page_count(tree: etree._Element) -> int:
    """
    从列表页解析总页数。
    列表页 URL: /list?line=/qingdao/licang&page=1
    """
    # 方式1：分页器中的最大页码
    page_links = tree.xpath('//div[contains(@class, "page-box")]//a/@href')
    pages = set()
    for href in page_links:
        match = re.search(r'page=(\d+)', href)
        if match:
            pages.add(int(match.group(1)))

    # 也检查 data 属性
    page_data = tree.xpath('//div[contains(@class, "page-box")]//@data-page')
    for p in page_data:
        if p.isdigit():
            pages.add(int(p))

    if pages:
        return min(max(pages), 100)

    # 方式2：从总房源数推算
    total_texts = tree.xpath('//h2[contains(@class, "total")]/span/text()')
    if not total_texts:
        total_texts = tree.xpath('//*[contains(text(), "共找到")]/text()')
    if total_texts:
        nums = re.findall(r'\d+', "".join(total_texts))
        if nums:
            total = int(nums[0])
            return min((total // 30) + 1, 100)

    return 1


def fetch_listing_urls(page_url: str) -> list:
    """
    从一页列表页提取所有房源详情 URL。

    列表页中的房源链接格式：
      <a href="http://node4:8000/details/?line=/qingdao/licang/xxx.html">...</a>
      或相对路径: /details/?line=/qingdao/licang/xxx.html
    """
    try:
        resp = requests.get(page_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.encoding = "utf-8"
        if resp.status_code != 200:
            return []
    except Exception as e:
        print(f"      [FAIL] {page_url}: {e}")
        return []

    tree = etree.HTML(resp.text)

    # 提取详情页链接
    links = tree.xpath('//a[contains(@href, "/details/")]/@href')
    if not links:
        # 备选: 找 .html 结尾的链接
        links = tree.xpath('//a[contains(@href, ".html")]/@href')

    urls = []
    seen = set()
    for href in links:
        if href in seen:
            continue
        seen.add(href)

        # 补全 URL
        if href.startswith("/details/"):
            full = f"http://node4:8000{href}"
        elif href.startswith("http"):
            full = href
        else:
            full = f"http://node4:8000/details/{href}"

        urls.append(full)

    return urls


def crawl_all_listing_urls(districts: list, test_mode: bool = False) -> tuple:
    """遍历所有地区所有页，提取所有房源链接"""
    max_pages = 1 if test_mode else 100
    all_results = []
    all_urls = []

    for i, d in enumerate(districts):
        city = d["city_name"]
        district_name = d["district_name"]
        list_url = d["list_url"]

        print(f"\n[{i+1}/{len(districts)}] {city} - {district_name}")
        print(f"    {list_url}")

        # 获取第1页 + 解析总页数
        try:
            resp = requests.get(list_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.encoding = "utf-8"
            if resp.status_code != 200:
                print(f"    [FAIL] HTTP {resp.status_code}")
                continue
            tree = etree.HTML(resp.text)
            total_pages = get_page_count(tree)
        except Exception as e:
            print(f"    [FAIL] {e}")
            continue

        pages_to_crawl = min(total_pages, max_pages)
        print(f"    总 {total_pages} 页, 爬取 {pages_to_crawl} 页")

        district_urls = []
        for page in range(1, pages_to_crawl + 1):
            # 构造分页 URL
            page_url = re.sub(r'page=\d+', f'page={page}', list_url)
            urls = fetch_listing_urls(page_url)
            district_urls.extend(urls)

            if page % 5 == 0 or page == pages_to_crawl:
                print(f"    第 {page}/{pages_to_crawl} 页, 累计 {len(district_urls)} 个链接")
            time.sleep(0.3)

        print(f"    [OK] 共 {len(district_urls)} 个房源链接")
        all_results.append({
            "city": city,
            "district": district_name,
            "list_url": list_url,
            "pages_crawled": pages_to_crawl,
            "listing_count": len(district_urls),
            "listing_urls": district_urls,
        })
        all_urls.extend(district_urls)

        time.sleep(REQUEST_DELAY)

    return all_results, all_urls


def main():
    test_mode = "--test" in sys.argv

    print("=" * 65)
    print("A.3 爬取和整理网站所有房源链接")
    if test_mode:
        print("【测试模式: 每个地区仅爬取 1 页】")
    print("=" * 65)

    districts = load_district_links()

    print(f"\n[2] 开始爬取房源链接...")
    results, all_urls = crawl_all_listing_urls(districts, test_mode=test_mode)

    # 保存详细结果
    json_path = os.path.join(RAW_DIR, "a3_all_listing_links.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] 详细结果: {json_path}")

    # 保存纯 URL 列表（供 A.4 使用）
    txt_path = os.path.join(RAW_DIR, "a3_listing_urls.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        for url in all_urls:
            f.write(url + "\n")
    print(f"[OK] URL 列表: {txt_path}")

    # 统计
    city_stats = {}
    for r in results:
        city = r["city"]
        city_stats[city] = city_stats.get(city, 0) + r["listing_count"]

    print("\n" + "=" * 50)
    print("统计")
    for city, count in sorted(city_stats.items(), key=lambda x: -x[1]):
        print(f"  {city}: {count} 套房源链接")
    print(f"  总计: {len(all_urls)} 套房源链接")
    print("=" * 50)

    print("[完成] A.3 运行结束。")


if __name__ == "__main__":
    main()
