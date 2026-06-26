"""
调试 A.2 — 查看城市页面的实际 HTML 结构，找到正确的 XPath
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from lxml import etree
from config import HEADERS, DETAIL_URL

# 抓取青岛城市页
url = f"{DETAIL_URL}?line=/qingdao/"
print(f"URL: {url}")

resp = requests.get(url, headers=HEADERS, timeout=15)
resp.encoding = "utf-8"
html = resp.text

print(f"响应长度: {len(html)}")
print()

# 保存原始 HTML 供检查
debug_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "raw", "debug_qingdao_page.html")
with open(debug_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"原始 HTML 已保存到: {debug_path}")
print()

tree = etree.HTML(html)

# 尝试多种 XPath 找到地区链接
print("=" * 60)
print("尝试各种 XPath 找地区链接：")
print("=" * 60)

# 1. 所有 <a> 标签中 href 包含 /qingdao/ 的
links = tree.xpath('//a[contains(@href, "/qingdao/")]')
print(f"\n[1] //a[contains(@href, '/qingdao/')]  → {len(links)} 个")
for a in links[:10]:
    href = "".join(a.xpath("./@href"))
    text = "".join(a.xpath(".//text()")).strip()
    print(f"    text={text[:30]:30s} href={href}")

# 2. 所有 <a> 标签
all_links = tree.xpath('//a')
print(f"\n[2] 页面中所有 <a> 标签  → {len(all_links)} 个")
for a in all_links[:20]:
    href = "".join(a.xpath("./@href"))
    text = "".join(a.xpath(".//text()")).strip()
    if text:
        print(f"    text={text[:40]:40s} href={href[:80]}")

# 3. data-role 属性
data_roles = tree.xpath('//div[@data-role]')
print(f"\n[3] //div[@data-role]  → {len(data_roles)} 个")
for div in data_roles:
    role = div.xpath("./@data-role")
    print(f"    data-role={role}")

# 4. 搜索 "区" 关键字的链接
qu_links = tree.xpath('//a[contains(text(), "区")]')
print(f"\n[4] //a[contains(text(), '区')]  → {len(qu_links)} 个")
for a in qu_links[:15]:
    href = "".join(a.xpath("./@href"))
    text = "".join(a.xpath(".//text()")).strip()
    print(f"    {text[:30]} → {href}")

# 5. 搜索 "ershoufang" 的链接
esf_links = tree.xpath('//a[contains(@href, "ershoufang")]')
print(f"\n[5] //a[contains(@href, 'ershoufang')]  → {len(esf_links)} 个")
for a in esf_links[:15]:
    href = "".join(a.xpath("./@href"))
    text = "".join(a.xpath(".//text()")).strip()
    print(f"    {text[:30]} → {href}")

# 6. 找 class 包含 filter 或 district 的元素
filter_divs = tree.xpath('//div[contains(@class, "filter") or contains(@class, "district") or contains(@class, "position")]')
print(f"\n[6] filter/district/position div  → {len(filter_divs)} 个")
for div in filter_divs[:5]:
    cls = div.xpath("./@class")
    text = "".join(div.xpath(".//text()")).strip()[:100]
    print(f"    class={cls}  text={text}")

# 7. 直接看页面中有哪些 class
all_classes = tree.xpath('//*/@class')
unique_classes = list(set(all_classes))
print(f"\n[7] 页面中不重复的 class 值 (前50个):")
for c in sorted(unique_classes)[:50]:
    print(f"    {c}")
