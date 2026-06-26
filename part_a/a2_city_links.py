"""
A.2 爬取山东省各城市各地区链接
====================================
从 http://node4:8000/ 首页解析所有城市/地区的列表页链接，
存为 CSV 文件，供 A.3 使用。

URL 体系（node4 代理）：
  首页:   http://node4:8000/
  列表页: http://node4:8000/list?line=/qingdao/licang&page=1
  详情页: http://node4:8000/details/?line=/qingdao/licang/xxx.html
"""

import os
import re
import csv
import json
import sys
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from lxml import etree
from config import HEADERS, REQUEST_TIMEOUT, RAW_DIR


def fetch_all_districts() -> list:
    """
    从 node4 首页解析所有地区链接。

    首页 HTML 中的链接格式：
      <a href="http://node4:8000/list?line=/qingdao/licang&page=1">李沧</a>

    返回 [{city_name, city_pinyin, district_name, district_pinyin, list_url}]
    """
    url = "http://node4:8000/"
    print(f"[1] 正在获取首页: {url}")

    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.encoding = "utf-8"
    tree = etree.HTML(resp.text)

    print(f"    首页大小: {len(resp.text)} 字节")

    # 提取所有 /list?line= 链接
    links = tree.xpath('//a[contains(@href, "/list?line=")]')
    print(f"    找到 {len(links)} 个地区链接")

    # 拼音→中文映射
    PINYIN_TO_CITY = {
        "qingdao": "青岛", "jinan": "济南", "yantai": "烟台",
        "weihai": "威海", "zibo": "淄博", "linyi": "临沂",
        "weifang": "潍坊", "jining": "济宁", "taian": "泰安",
        "dezhou": "德州", "liaocheng": "聊城", "binzhou": "滨州",
        "heze": "菏泽", "rizhao": "日照", "zaozhuang": "枣庄",
        "dongying": "东营",
    }

    districts = []
    seen = set()

    for a in links:
        district_name = "".join(a.xpath(".//text()")).strip()
        href = "".join(a.xpath("./@href")).strip()

        if not district_name or not href:
            continue

        # 解析 /list?line=/qingdao/licang&page=1
        # 提取城市拼音和地区拼音
        match = re.search(r'line=/(\w+)/([\w\d]+)', href)
        if not match:
            continue

        city_pinyin = match.group(1)
        district_pinyin = match.group(2)

        # 去重
        key = f"{city_pinyin}/{district_pinyin}"
        if key in seen:
            continue
        seen.add(key)

        city_name = PINYIN_TO_CITY.get(city_pinyin, city_pinyin)

        # 构造列表页基础 URL（不要 page 参数）
        list_url = f"http://node4:8000/list?line=/{city_pinyin}/{district_pinyin}&page=1"

        districts.append({
            "city_name": city_name,
            "city_pinyin": city_pinyin,
            "district_name": district_name,
            "district_pinyin": district_pinyin,
            "list_url": list_url,
        })

    return districts


def main():
    print("=" * 65)
    print("A.2 爬取山东省各城市各地区链接")
    print("=" * 65)

    districts = fetch_all_districts()

    # 按城市统计
    city_stats = {}
    for d in districts:
        cn = d["city_name"]
        city_stats[cn] = city_stats.get(cn, 0) + 1

    print(f"\n[2] 统计:")
    for cn, cnt in sorted(city_stats.items(), key=lambda x: -x[1]):
        print(f"    {cn}: {cnt} 个地区")
    print(f"    共 {len(city_stats)} 个城市, {len(districts)} 个地区")

    # 保存 CSV
    csv_path = os.path.join(RAW_DIR, "a2_shandong_district_links.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "city_name", "city_pinyin", "district_name", "district_pinyin", "list_url"
        ])
        writer.writeheader()
        writer.writerows(districts)
    print(f"\n[OK] CSV 已保存: {csv_path}")

    # 保存 JSON（A.3 使用）
    json_path = os.path.join(RAW_DIR, "a2_district_urls.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(districts, f, ensure_ascii=False, indent=2)
    print(f"[OK] JSON 已保存: {json_path}")

    print("[完成] A.2 运行结束。")


if __name__ == "__main__":
    main()
