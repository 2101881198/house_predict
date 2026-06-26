"""
Pipeline — 数据处理管道

1. RedisStoragePipeline: 将 Item 存入 Redis（供 redis_to_mysql.py 消费）
2. MySQLPipeline:     直接写入 MySQL（可选）
"""

import json
import logging
import redis
import pymysql

logger = logging.getLogger(__name__)


class RedisStoragePipeline:
    """
    将爬虫产出的 Item 存入 Redis List。

    设计思路：
      - Scrapy 爬虫产出 Item → 序列化为 JSON → 推入 Redis 列表
      - 独立的 redis_to_mysql.py 脚本从该列表取数据写入 MySQL
      - 实现爬虫和 MySQL 写入的解耦，互不影响
    """

    # Redis 中存放已爬取数据的键名
    REDIS_DATA_KEY = "lianjia:items"

    def __init__(self, redis_host, redis_port, redis_db):
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.redis_db = redis_db
        self.client = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            redis_host=crawler.settings.get("REDIS_HOST", "localhost"),
            redis_port=crawler.settings.get("REDIS_PORT", 6379),
            redis_db=crawler.settings.get("REDIS_DB", 0),
        )

    def open_spider(self, spider):
        """爬虫启动时建立 Redis 连接"""
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                decode_responses=True,
                socket_timeout=30,
                socket_connect_timeout=30,
            )
            self.client.ping()
            logger.info(f"Redis 连接成功: {self.redis_host}:{self.redis_port}")
        except Exception as e:
            logger.error(f"Redis 连接失败: {e}")
            self.client = None

    def close_spider(self, spider):
        """爬虫关闭时释放连接"""
        if self.client:
            self.client.close()

    def process_item(self, item, spider):
        """将 Item 转为 JSON 字符串推入 Redis"""
        if self.client:
            try:
                data = dict(item)
                json_str = json.dumps(data, ensure_ascii=False)
                self.client.rpush(self.REDIS_DATA_KEY, json_str)
                logger.debug(f"Item 已写入 Redis: {data.get('url', '')}")
            except Exception as e:
                logger.error(f"写入 Redis 失败: {e}")
        return item


class MySQLPipeline:
    """
    直接将 Item 写入 MySQL（可选使用）。

    注意：如果同时使用 RedisStoragePipeline，
          建议只保留 RedisStoragePipeline，
          由 redis_to_mysql.py 统一负责 MySQL 写入。
    """

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS house_listings (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        city VARCHAR(32) DEFAULT '' COMMENT '城市',
        district VARCHAR(32) DEFAULT '' COMMENT '地区',
        url VARCHAR(512) DEFAULT '' COMMENT '链接',
        house_title VARCHAR(256) DEFAULT '' COMMENT '标题',

        -- 价格
        unit_price VARCHAR(32) DEFAULT '' COMMENT '单价(元/㎡)',
        total_price VARCHAR(32) DEFAULT '' COMMENT '总价(万)',

        -- 位置
        community_name VARCHAR(128) DEFAULT '' COMMENT '小区名称',
        area_name VARCHAR(128) DEFAULT '' COMMENT '所在区域',
        biz_circle VARCHAR(64) DEFAULT '' COMMENT '商圈',

        -- 房屋属性
        house_layout VARCHAR(64) DEFAULT '' COMMENT '房屋户型',
        floor_position VARCHAR(64) DEFAULT '' COMMENT '所在楼层',
        building_area VARCHAR(32) DEFAULT '' COMMENT '建筑面积(㎡)',
        layout_structure VARCHAR(32) DEFAULT '' COMMENT '户型结构',
        orientation VARCHAR(32) DEFAULT '' COMMENT '房屋朝向',
        building_structure VARCHAR(64) DEFAULT '' COMMENT '建筑结构',
        decoration VARCHAR(32) DEFAULT '' COMMENT '装修情况',
        building_type VARCHAR(64) DEFAULT '' COMMENT '建筑类型',
        build_year VARCHAR(16) DEFAULT '' COMMENT '建成年份',

        -- 交易信息
        elevator_ratio VARCHAR(64) DEFAULT '' COMMENT '梯户比例',
        listing_time VARCHAR(32) DEFAULT '' COMMENT '挂牌时间',
        transaction_ownership VARCHAR(64) DEFAULT '' COMMENT '交易权属',
        property_ownership VARCHAR(64) DEFAULT '' COMMENT '产权所属',
        mortgage_info VARCHAR(128) DEFAULT '' COMMENT '抵押信息',
        property_rights VARCHAR(32) DEFAULT '' COMMENT '产权年限',
        `usage` VARCHAR(32) DEFAULT '' COMMENT '房屋用途',
        has_elevator VARCHAR(8) DEFAULT '' COMMENT '配备电梯',
        heating VARCHAR(32) DEFAULT '' COMMENT '供暖方式',
        deed_year VARCHAR(32) DEFAULT '' COMMENT '房本年限',
        last_trade VARCHAR(32) DEFAULT '' COMMENT '上次交易',

        -- 配套介绍
        key_selling_points TEXT COMMENT '核心卖点',
        community_intro TEXT COMMENT '小区介绍',
        layout_intro TEXT COMMENT '户型介绍',
        transportation TEXT COMMENT '交通出行',

        -- 坐标
        longitude VARCHAR(32) DEFAULT '' COMMENT '经度',
        latitude VARCHAR(32) DEFAULT '' COMMENT '纬度',

        -- 元信息
        crawl_time VARCHAR(32) DEFAULT '' COMMENT '爬取时间',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        UNIQUE KEY uk_url (url(255))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='二手房房源数据';
    """

    def __init__(self, mysql_config):
        self.mysql_config = mysql_config
        self.conn = None
        self.cursor = None
        self.count = 0

    @classmethod
    def from_crawler(cls, crawler):
        config = {
            "host": crawler.settings.get("MYSQL_HOST", "localhost"),
            "port": crawler.settings.get("MYSQL_PORT", 3306),
            "user": crawler.settings.get("MYSQL_USER", "root"),
            "password": crawler.settings.get("MYSQL_PASSWORD", ""),
            "database": crawler.settings.get("MYSQL_DATABASE", "house_data"),
            "charset": crawler.settings.get("MYSQL_CHARSET", "utf8mb4"),
        }
        return cls(config)

    def open_spider(self, spider):
        try:
            # 先连接 MySQL 创建数据库
            conn = pymysql.connect(
                host=self.mysql_config["host"],
                port=self.mysql_config["port"],
                user=self.mysql_config["user"],
                password=self.mysql_config["password"],
                charset=self.mysql_config["charset"],
            )
            with conn.cursor() as cur:
                cur.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.mysql_config['database']}` "
                    "DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            conn.close()

            # 连接目标数据库
            self.conn = pymysql.connect(**self.mysql_config)
            self.cursor = self.conn.cursor()
            self.cursor.execute(self.CREATE_TABLE_SQL)
            self.conn.commit()
            logger.info(f"MySQL 连接成功: {self.mysql_config['host']}")
        except Exception as e:
            logger.error(f"MySQL 连接失败: {e}")

    def close_spider(self, spider):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def process_item(self, item, spider):
        if not self.conn:
            return item

        data = dict(item)
        columns = ", ".join(f"`{k}`" for k in data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = list(data.values())

        sql = f"INSERT IGNORE INTO house_listings ({columns}) VALUES ({placeholders})"

        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
            self.count += 1
            if self.count % 50 == 0:
                logger.info(f"MySQL: 已写入 {self.count} 条数据")
        except Exception as e:
            logger.error(f"MySQL 写入失败: {e}")
            self.conn.rollback()

        return item
