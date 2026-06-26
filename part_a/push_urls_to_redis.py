"""
push_urls_to_redis.py — URL 推送脚本

功能：
  读取 A.3 生成的所有房源链接文件 (a3_listing_urls.txt)，
  将链接逐条推送到 Redis 队列 (lianjia:start_urls)，
  供分布式爬虫消费。

用法：
  python push_urls_to_redis.py

  # 指定 Redis 地址
  python push_urls_to_redis.py --host 192.168.0.101 --port 6379

  # 清空旧数据后重推
  python push_urls_to_redis.py --clear

前置条件：
  1. Redis 服务已启动
  2. A.3 已执行，生成了 a3_listing_urls.txt
"""

import os
import sys
import argparse

try:
    import redis
except ImportError:
    print("[FAIL] 请先安装 redis 库: pip install redis")
    sys.exit(1)


# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_urls(url_file: str) -> list:
    """加载 A.3 生成的房源链接"""
    if not os.path.exists(url_file):
        # 尝试 JSON 格式
        import json
        json_file = url_file.replace(".txt", ".json").replace("listing_urls", "all_listing_links")
        if os.path.exists(json_file):
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            urls = []
            for d in data:
                urls.extend(d.get("listing_urls", []))
            return urls
        print(f"[FAIL] URL 文件不存在: {url_file}")
        print("  请先运行 A.3: python part_a/a3_all_listing_links.py")
        sys.exit(1)

    with open(url_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def push_to_redis(urls: list, redis_host: str, redis_port: int, redis_db: int,
                  redis_key: str, clear_first: bool = False):
    """将 URL 列表推送到 Redis"""
    print(f"\n[1] 连接 Redis: {redis_host}:{redis_port} (db={redis_db})")
    try:
        r = redis.Redis(
            host=redis_host, port=redis_port, db=redis_db,
            decode_responses=True, socket_timeout=10,
            socket_connect_timeout=10,
        )
        r.ping()
        print("    [OK] Redis 连接成功")
    except Exception as e:
        print(f"    [FAIL] Redis 连接失败: {e}")
        sys.exit(1)

    # 清空旧数据
    if clear_first:
        r.delete(redis_key)
        print(f"    [OK] 已清空 Redis 键: {redis_key}")

    # 批量推送（使用 pipeline 提高效率）
    print(f"\n[2] 推送 {len(urls)} 个 URL 到 Redis 队列: {redis_key}")
    batch_size = 500
    pushed = 0
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        pipe = r.pipeline()
        for url in batch:
            pipe.lpush(redis_key, url)
        pipe.execute()
        pushed += len(batch)
        print(f"    进度: {pushed}/{len(urls)}")

    # 验证
    queue_len = r.llen(redis_key)
    print(f"\n[OK] 推送完成！Redis 队列长度: {queue_len}")
    print(f"     键名: {redis_key}")


def main():
    parser = argparse.ArgumentParser(description="推送房源 URL 到 Redis 队列")
    parser.add_argument("--host", default="192.168.0.101", help="Redis 主机地址")
    parser.add_argument("--port", type=int, default=6379, help="Redis 端口")
    parser.add_argument("--db", type=int, default=0, help="Redis 数据库编号")
    parser.add_argument("--key", default="lianjia:start_urls", help="Redis 键名")
    parser.add_argument("--clear", action="store_true", help="推送前清空旧数据")
    parser.add_argument("--url-file", default=None, help="URL 文件路径（默认自动查找）")
    args = parser.parse_args()

    print("=" * 60)
    print("push_urls_to_redis — 推送 URL 到 Redis 队列")
    print("=" * 60)

    # 确定 URL 文件路径
    if args.url_file:
        url_file = args.url_file
    else:
        url_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "raw", "a3_listing_urls.txt"
        )

    print(f"URL 文件: {url_file}")
    urls = load_urls(url_file)
    print(f"URL 数量: {len(urls)}")

    push_to_redis(
        urls=urls,
        redis_host=args.host,
        redis_port=args.port,
        redis_db=args.db,
        redis_key=args.key,
        clear_first=args.clear,
    )

    print("\n[完成] 现在可以启动爬虫:")
    print("  cd part_a/house_scrapy")
    print("  scrapy crawl house_spider")
    print("  # 在 node1/node2/node3 上同时运行上述命令即可分布式爬取")


if __name__ == "__main__":
    main()
