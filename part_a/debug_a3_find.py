"""
调试 — 探测不同城市/区下的有效房源 ID
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from lxml import etree
from config import HEADERS, DETAIL_URL, SHANDONG_CITIES

# 已知有效: /qingdao/licang/103127976551.html
# 尝试: 同ID不同区, 同区不同ID

test_urls = [
    # 同一 ID，不同城市/区
    "/qingdao/shinan/103127976551.html",
    "/qingdao/shibei/103127976551.html",
    "/jinan/lixia/103127976551.html",
    "/jinan/shizhong/103127976551.html",
    # 不同 ID
    "/qingdao/licang/103127976552.html",
    "/qingdao/licang/103127976550.html",
    # 完全不同的 ID
    "/qingdao/licang/123456789.html",
    "/qingdao/shinan/123456789.html",
    # 试试链家原始格式
    "/qingdao/licang/2511046798.html",
]

print("探测有效的房源 URL...")
print("=" * 60)

valid_urls = []
for path in test_urls:
    url = f"{DETAIL_URL}?line={path}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "utf-8"

        if resp.status_code != 200:
            print(f"  [{resp.status_code}] {path}")
            continue

        tree = etree.HTML(resp.text)
        title = "".join(tree.xpath('//h1[@class="main"]/text()')).strip()
        total = "".join(tree.xpath('//span[@class="total"]/text()')).strip()

        if title and total:
            valid_urls.append((url, title[:40], total))
            print(f"  [有效] {path}")
            print(f"         标题: {title[:50]}, 总价: {total}")
        else:
            # 看看能否从 title 标签判断
            page_title = "".join(tree.xpath('//title/text()'))
            print(f"  [200但无房源数据] {path}  title={page_title[:50]}")
    except Exception as e:
        print(f"  [错误] {path}: {e}")

print(f"\n有效房源数: {len(valid_urls)}")
for u, t, p in valid_urls:
    print(f"  {u}")
    print(f"  {t} | {p}")
