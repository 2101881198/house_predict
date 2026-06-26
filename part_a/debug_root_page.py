"""
分析 node4:8000 首页 — 很可能是房源列表入口
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from lxml import etree
from config import HEADERS

url = "http://node4:8000/"
print(f"URL: {url}")

resp = requests.get(url, headers=HEADERS, timeout=15)
resp.encoding = "utf-8"
html = resp.text
tree = etree.HTML(html)

print(f"响应长度: {len(html)} 字节\n")

# 1. 查找所有 <a> 标签中 href 含关键字的
print("=" * 60)
print("[1] 含 .html 的链接（房源详情）:")
links = tree.xpath('//a[contains(@href, ".html")]/@href')
for href in links[:20]:
    print(f"    {href}")
print(f"  共 {len(links)} 个")

# 2. 含 /ershoufang/ 的链接
print(f"\n[2] 含 /ershoufang/ 的链接:")
links = tree.xpath('//a[contains(@href, "/ershoufang/")]/@href')
for href in links[:20]:
    print(f"    {href}")
print(f"  共 {len(links)} 个")

# 3. 含 /details/ 的链接
print(f"\n[3] 含 /details/ 的链接:")
links = tree.xpath('//a[contains(@href, "/details/")]/@href')
for href in links[:20]:
    print(f"    {href}")
print(f"  共 {len(links)} 个")

# 4. 所有 <a> 标签（有文本的）
print(f"\n[4] 所有有内容的 <a> 标签（前30个）:")
all_a = tree.xpath('//a[string-length(normalize-space(text())) > 0]')
count = 0
for a in all_a:
    text = "".join(a.xpath(".//text()")).strip()
    href = "".join(a.xpath("./@href")).strip()
    if text and href:
        print(f"    [{text[:30]:30s}] → {href[:80]}")
        count += 1
        if count >= 30:
            break
print(f"  共 {len(all_a)} 个有文本的链接")

# 5. 查找搜索/筛选相关元素
print(f"\n[5] 页面主要结构:")
for sel in ['//title', '//h1', '//h2', '//h3']:
    results = tree.xpath(sel + '/text()')
    if results:
        for r in results[:5]:
            print(f"    {sel}: {r.strip()[:80]}")

# 6. class 中含 list/sell/content 的元素
print(f"\n[6] 查找列表相关元素:")
for cls_pattern in ['sellList', 'listContent', 'houseList', 'info', 'title']:
    elems = tree.xpath(f'//*[contains(@class, "{cls_pattern}")]')
    if elems:
        # 取第一个元素的文本片段
        text = "".join(elems[0].xpath('.//text()'))[:100]
        print(f"    .{cls_pattern}: {len(elems)} 个, 例: {text}")

# 7. 存 HTML 到文件
debug_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "data", "raw", "debug_root_page.html")
with open(debug_path, "w", encoding="utf-8") as f:
    f.write(html)
print(f"\n完整 HTML 已保存: {debug_path}")
