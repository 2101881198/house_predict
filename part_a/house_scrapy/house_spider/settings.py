"""
Scrapy-Redis 分布式爬虫配置

使用说明：
  - 主节点(node1): 运行 Redis + MySQL + 爬虫
  - 从节点(node2, node3): 运行 Redis + 爬虫
  - 所有节点共享同一个 Redis 实例（主节点 IP）
"""

# ============================
#  Scrapy 基础配置
# ============================
BOT_NAME = "house_spider"
SPIDER_MODULES = ["house_spider.spiders"]
NEWSPIDER_MODULE = "house_spider.spiders"

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

# 下载延迟（秒），避免请求过快
DOWNLOAD_DELAY = 0.5
DOWNLOAD_TIMEOUT = 15

# 并发请求数
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# 重试
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# ============================
#  请求头（模拟浏览器）
# ============================
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# ============================
#  Scrapy-Redis 分布式配置
# ============================

# 使用 Redis 调度器（替换默认调度器）
SCHEDULER = "scrapy_redis.scheduler.Scheduler"

# 使用 Redis 去重过滤器（替换默认去重）
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"

# Redis 队列持久化（爬虫关闭后不清空队列，支持断点续爬）
SCHEDULER_PERSIST = True

# 调度器队列类型：先进先出
SCHEDULER_QUEUE_CLASS = "scrapy_redis.queue.FifoQueue"

# 允许暂停/恢复
SCHEDULER_IDLE_BEFORE_CLOSE = 0

# ============================
#  Redis 连接配置
#  【重要】node2/node3 需要改为 node1 的 IP 地址
# ============================
REDIS_HOST = "127.0.0.1"            # node1 本机用 127.0.0.1，node2/node3 改为 node1 的 IP
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PARAMS = {
    "socket_timeout": 30,
    "socket_connect_timeout": 30,
    "retry_on_timeout": True,
    "encoding": "utf-8",
}

# Redis 中存放起始 URL 的键名
REDIS_START_URLS_KEY = "lianjia:start_urls"

# ============================
#  Pipeline 配置
# ============================
ITEM_PIPELINES = {
    # 将数据写入 Redis（供 redis_to_mysql.py 消费）
    "house_spider.pipelines.RedisStoragePipeline": 300,
    # 将数据直接写入 MySQL（可选）
    # "house_spider.pipelines.MySQLPipeline": 400,
}

# ============================
#  下载器中间件
# ============================
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    "house_spider.middlewares.RandomUserAgentMiddleware": 200,
}

# ============================
#  MySQL 配置（供 Pipeline 使用）
# ============================
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
MYSQL_DATABASE = "house_data"
MYSQL_CHARSET = "utf8mb4"
MYSQL_TABLE = "house_listings"

# ============================
#  日志
# ============================
LOG_LEVEL = "INFO"
LOG_FILE = "house_spider.log"
