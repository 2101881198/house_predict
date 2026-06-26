"""
全局配置文件
- 爬虫请求头、延迟设置
- 文件路径配置
- 代理服务器 URL 构建
- 数据库/Redis 连接配置（分布式爬虫使用）
- 山东省城市与拼音路径映射

目标网站：http://node4:8000/details/?line={城市拼音}/{区拼音}/{房源ID}.html
"""

import os

# ==================== 项目路径 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

for d in [DATA_DIR, RAW_DIR, PROCESSED_DIR]:
    os.makedirs(d, exist_ok=True)

# ==================== 服务器配置 ====================
# 代理服务器地址
SERVER_HOST = "http://node4:8000"
# 详情页接口：GET /details/?line=/qingdao/licang/xxx.html
DETAIL_URL = f"{SERVER_HOST}/details/"
# 列表页接口：GET /list?line=/qingdao/licang&page=1
LIST_URL = f"{SERVER_HOST}/list"

# ==================== 爬虫通用配置 ====================
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# 请求间隔（秒），避免被封 IP
REQUEST_DELAY = 2
# 请求超时（秒）
REQUEST_TIMEOUT = 15

# ==================== URL 构建工具 ====================
def build_detail_url(city_pinyin: str, district_pinyin: str, house_id: str) -> str:
    """
    构建房源详情页 URL（A.1 / A.4 使用）
    格式: http://node4:8000/details/?line=/qingdao/licang/103127976551.html
    """
    line = f"/{city_pinyin}/{district_pinyin}/{house_id}.html"
    return f"{DETAIL_URL}?line={line}"


def build_district_list_url(city_pinyin: str, district_pinyin: str = None, page: int = None) -> str:
    """
    构建区级列表页 URL（A.2 / A.3 使用）
    格式: http://node4:8000/details/?line=/qingdao/licang/       (第1页)
          http://node4:8000/details/?line=/qingdao/licang/pg2/   (第2页)
    """
    if district_pinyin:
        if page and page > 1:
            line = f"/{city_pinyin}/{district_pinyin}/pg{page}/"
        else:
            line = f"/{city_pinyin}/{district_pinyin}/"
    else:
        # 城市首页
        line = f"/{city_pinyin}/"
    return f"{DETAIL_URL}?line={line}"


def build_city_url(city_pinyin: str) -> str:
    """
    构建城市首页 URL
    格式: http://node4:8000/details/?line=/qingdao/
    """
    return f"{DETAIL_URL}?line=/{city_pinyin}/"


# ==================== 山东省城市映射 ====================
# 城市中文名 → 拼音路径名
SHANDONG_CITIES = {
    "青岛": "qingdao",
    "济南": "jinan",
    "烟台": "yantai",
    "威海": "weihai",
    "淄博": "zibo",
    "临沂": "linyi",
    "潍坊": "weifang",
    "济宁": "jining",
    "泰安": "taian",
    "德州": "dezhou",
    "聊城": "liaocheng",
    "滨州": "binzhou",
    "菏泽": "heze",
    "日照": "rizhao",
    "枣庄": "zaozhuang",
    "东营": "dongying",
}

# 拼音 → 中文名（反向映射）
PINYIN_TO_CITY = {v: k for k, v in SHANDONG_CITIES.items()}

# 济南各区拼音
JINAN_DISTRICTS = [
    "lixia", "shizhong", "huaiyin", "tianqiao",
    "licheng", "changqing", "zhangqiu", "jiyang",
    "laiwu", "gangcheng",
]

# 青岛各区拼音
QINGDAO_DISTRICTS = [
    "shinan", "shibei", "huangdao", "laoshan",
    "licheng", "chengyang", "jimo", "jiaozhou",
]

# ==================== 分布式部署配置（任务6） ====================
# node1: 主节点(Redis + MySQL + 爬虫)
# node2/node3: 从节点(Redis + 爬虫)
MASTER_IP = "192.168.0.101"
NODE_CONFIG = {
    "node1": {"ip": "192.168.0.101", "role": "master"},
    "node2": {"ip": "192.168.0.102", "role": "slave"},
    "node3": {"ip": "192.168.0.103", "role": "slave"},
}

# ==================== Redis 配置（分布式爬虫 A.4 使用） ====================
REDIS_HOST = MASTER_IP           # 主节点 IP（从节点需修改为此地址）
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None
# Redis 键名
REDIS_START_URLS_KEY = "lianjia:start_urls"   # 待爬 URL 队列
REDIS_ITEMS_KEY = "lianjia:items"              # 已爬取数据队列

# ==================== MySQL 配置（可选，存储爬取结果） ====================
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "house_data",
    "charset": "utf8mb4",
}

# ==================== Scrapy 配置 ====================
SCRAPY_SETTINGS = {
    "BOT_NAME": "house_spider",
    "ROBOTSTXT_OBEY": False,
    "DOWNLOAD_DELAY": REQUEST_DELAY,
    "DOWNLOAD_TIMEOUT": REQUEST_TIMEOUT,
    "DEFAULT_REQUEST_HEADERS": HEADERS,
    "CONCURRENT_REQUESTS": 8,
    "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
    "COOKIES_ENABLED": False,
    "TELNETCONSOLE_ENABLED": False,
    "RETRY_TIMES": 3,
    "DOWNLOADER_MIDDLEWARES": {
        "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
        "scrapy.downloadermiddlewares.retry.RetryMiddleware": 90,
    },
}
