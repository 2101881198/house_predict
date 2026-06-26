"""
调试 — 扫描房源 ID，找到有效房源

已知: /qingdao/licang/103127976551.html 存在
测试: 相邻 ID 是否也存在
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from lxml import etree
from config import HEADERS, DETAIL_URL

# 已知有效 ID
base_id = 103127976551

print("扫描 node4 上的房源 ID...")
print("=" * 60)

valid = []
for offset in range(-3, 10):
    test_id = base_id + offset
    url = f"{DETAIL_URL}?line=/qingdao/licang/{test_id}.html"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            print(f"  ID={test_id}  HTTP {resp.status_code}")
            continue

        tree = etree.HTML(resp.text)

        # 检查是否有房源标题（判断是否为有效房源页）
        title = tree.xpath('//h1[@class="main"]/text()')
        total = tree.xpath('//span[@class="total"]/text()')

        if title and total:
            valid.append(test_id)
            print(f"  ID={test_id}  有效!  标题={title[0][:40]}, 总价={total[0]}")
        else:
            # 可能返回了404页面
            page_title = "".join(tree.xpath('//title/text()'))
            print(f"  ID={test_id}  无效  (page title: {page_title[:50]})")

    except Exception as e:
        print(f"  ID={test_id}  错误: {e}")

print(f"\n有效房源: {len(valid)} 个")
print(f"ID 范围: {min(valid) if valid else 'N/A'} ~ {max(valid) if valid else 'N/A'}")
