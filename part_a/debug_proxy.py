"""
探测 node4:8000 的所有端点
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from config import HEADERS

host = "http://node4:8000"

endpoints = [
    "/",
    "/list",
    "/api",
    "/api/houses",
    "/houses",
    "/sitemap",
    "/robots.txt",
    "/details/",
    "/details/?line=/",
    "/details/?line=/qingdao/",
    "/details/?line=/qingdao/licang/",
    "/details/?line=/qingdao/licang/103127976551.html",
]

print("探测 node4:8000 端点...")
print("=" * 60)

for ep in endpoints:
    url = f"{host}{ep}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        ct = resp.headers.get("Content-Type", "")
        print(f"  [{resp.status_code}] {url}  ({len(resp.text)}B, {ct[:40]})")
    except Exception as e:
        print(f"  [ERR] {url}  {e}")
