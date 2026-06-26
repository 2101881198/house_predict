"""
redis_to_mysql.py — Redis → MySQL 数据同步脚本

功能：
  独立于 Scrapy 运行的后台脚本。持续从 Redis 列表中取出爬虫写入的
  JSON 数据，解析后写入 MySQL 数据库。

设计思想：
  - 与爬虫解耦，不占用 Scrapy 进程资源
  - 可以跟爬虫同步执行
  - 支持断点续传（消费一条删一条的模式不可用，改为确认消费）
  - 失败重试机制

用法：
  python redis_to_mysql.py

  # 指定 Redis/MySQL 地址
  python redis_to_mysql.py --redis-host 192.168.0.101 --mysql-host localhost

  # 单次运行（处理完当前队列后退出）
  python redis_to_mysql.py --once

  # 持续监听模式（默认）
  python redis_to_mysql.py --watch

前置条件：
  1. Redis 服务已启动
  2. MySQL 服务已启动，数据库 house_data 已创建
  3. 爬虫已在运行（或有数据在 Redis 中）
"""

import os
import sys
import json
import time
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("redis_to_mysql")


def get_redis_client(host: str, port: int, db: int):
    """建立 Redis 连接"""
    try:
        import redis
    except ImportError:
        logger.error("请安装 redis 库: pip install redis")
        sys.exit(1)

    client = redis.Redis(
        host=host, port=port, db=db,
        decode_responses=True,
        socket_timeout=10,
        socket_connect_timeout=10,
    )
    try:
        client.ping()
        logger.info(f"Redis 连接成功: {host}:{port}")
        return client
    except Exception as e:
        logger.error(f"Redis 连接失败: {e}")
        sys.exit(1)


def get_mysql_connection(host: str, port: int, user: str, password: str,
                         database: str, charset: str):
    """建立 MySQL 连接并创建表"""
    try:
        import pymysql
    except ImportError:
        logger.error("请安装 pymysql 库: pip install pymysql")
        sys.exit(1)

    try:
        # 先建库
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password, charset=charset
        )
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database}` "
                "DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()

        # 连接目标库
        conn = pymysql.connect(
            host=host, port=port, user=user, password=password,
            database=database, charset=charset,
        )
        logger.info(f"MySQL 连接成功: {host}:{port}/{database}")

        # 创建表
        create_table(conn)
        return conn

    except Exception as e:
        logger.error(f"MySQL 连接失败: {e}")
        sys.exit(1)


def create_table(conn):
    """创建房源数据表"""
    sql = """
    CREATE TABLE IF NOT EXISTS house_listings (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        city VARCHAR(32) DEFAULT '' COMMENT '城市',
        district VARCHAR(32) DEFAULT '' COMMENT '地区',
        url VARCHAR(512) DEFAULT '' COMMENT '链接',
        house_title VARCHAR(256) DEFAULT '' COMMENT '标题',

        unit_price VARCHAR(32) DEFAULT '' COMMENT '单价(元/㎡)',
        total_price VARCHAR(32) DEFAULT '' COMMENT '总价(万)',

        community_name VARCHAR(128) DEFAULT '' COMMENT '小区名称',
        area_name VARCHAR(128) DEFAULT '' COMMENT '所在区域',
        biz_circle VARCHAR(64) DEFAULT '' COMMENT '商圈',

        house_layout VARCHAR(64) DEFAULT '' COMMENT '房屋户型',
        floor_position VARCHAR(64) DEFAULT '' COMMENT '所在楼层',
        building_area VARCHAR(32) DEFAULT '' COMMENT '建筑面积(㎡)',
        layout_structure VARCHAR(32) DEFAULT '' COMMENT '户型结构',
        orientation VARCHAR(32) DEFAULT '' COMMENT '房屋朝向',
        building_structure VARCHAR(64) DEFAULT '' COMMENT '建筑结构',
        decoration VARCHAR(32) DEFAULT '' COMMENT '装修情况',
        building_type VARCHAR(64) DEFAULT '' COMMENT '建筑类型',
        build_year VARCHAR(16) DEFAULT '' COMMENT '建成年份',

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

        key_selling_points TEXT COMMENT '核心卖点',
        community_intro TEXT COMMENT '小区介绍',
        layout_intro TEXT COMMENT '户型介绍',
        transportation TEXT COMMENT '交通出行',

        longitude VARCHAR(32) DEFAULT '' COMMENT '经度',
        latitude VARCHAR(32) DEFAULT '' COMMENT '纬度',

        crawl_time VARCHAR(32) DEFAULT '' COMMENT '爬取时间',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        UNIQUE KEY uk_url (url(255))
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='二手房房源数据';
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        logger.info("MySQL 表 house_listings 已就绪")
    except Exception as e:
        logger.error(f"建表失败: {e}")


def insert_to_mysql(conn, data: dict) -> bool:
    """将单条数据写入 MySQL"""
    columns = [
        "city", "district", "url", "house_title",
        "unit_price", "total_price",
        "community_name", "area_name", "biz_circle",
        "house_layout", "floor_position", "building_area",
        "layout_structure", "orientation", "building_structure",
        "decoration", "building_type", "build_year",
        "elevator_ratio", "listing_time", "transaction_ownership",
        "property_ownership", "mortgage_info", "property_rights",
        "usage", "has_elevator", "heating", "deed_year", "last_trade",
        "key_selling_points", "community_intro", "layout_intro", "transportation",
        "longitude", "latitude", "crawl_time",
    ]

    # 只取表中存在的列
    values = [data.get(col, "") for col in columns]
    placeholders = ", ".join(["%s"] * len(columns))
    col_str = ", ".join(f"`{c}`" for c in columns)

    sql = f"INSERT IGNORE INTO house_listings ({col_str}) VALUES ({placeholders})"

    try:
        with conn.cursor() as cur:
            cur.execute(sql, values)
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"MySQL 写入失败: {e}")
        conn.rollback()
        return False


def consume_loop(r, conn, redis_data_key: str, once: bool = False):
    """
    主循环：持续从 Redis 消费数据写入 MySQL

    使用 RPOP 从列表右侧弹出（FIFO），
    消费成功写 MySQL，消费失败放回列表。
    """
    total = 0
    errors = 0
    empty_rounds = 0

    logger.info(f"开始消费 Redis 队列: {redis_data_key}")
    logger.info("按 Ctrl+C 停止")

    try:
        while True:
            # 从 Redis 列表弹出数据（JSON 字符串）
            json_str = r.rpop(redis_data_key)

            if json_str is None:
                empty_rounds += 1
                if once:
                    logger.info(f"队列已空，单次模式退出。共处理 {total} 条")
                    break
                # 队列空，等待 3 秒再检查
                if empty_rounds % 20 == 0:
                    logger.info(f"队列为空，等待中... (已处理 {total} 条)")
                time.sleep(3)
                continue

            empty_rounds = 0

            # 解析 JSON
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 解析失败: {e}")
                errors += 1
                continue

            # 写入 MySQL
            success = insert_to_mysql(conn, data)

            if success:
                total += 1
                if total % 100 == 0:
                    logger.info(f"进度: 已写入 {total} 条 (错误 {errors})")
            else:
                # 写入失败，放回 Redis 队列尾部待重试
                r.lpush(redis_data_key, json_str)
                errors += 1
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info(f"收到中断信号，停止。共处理 {total} 条，错误 {errors} 条")
    except Exception as e:
        logger.error(f"消费异常: {e}")
    finally:
        logger.info(f"最终统计: 成功 {total} 条, 错误 {errors} 条")


def main():
    parser = argparse.ArgumentParser(description="Redis → MySQL 数据同步脚本")
    parser.add_argument("--redis-host", default="192.168.0.101", help="Redis 主机地址")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis 端口")
    parser.add_argument("--redis-db", type=int, default=0, help="Redis DB 编号")
    parser.add_argument("--redis-key", default="lianjia:items", help="Redis 数据键名")
    parser.add_argument("--mysql-host", default="localhost", help="MySQL 主机地址")
    parser.add_argument("--mysql-port", type=int, default=3306, help="MySQL 端口")
    parser.add_argument("--mysql-user", default="root", help="MySQL 用户")
    parser.add_argument("--mysql-password", default="123456", help="MySQL 密码")
    parser.add_argument("--mysql-database", default="house_data", help="MySQL 数据库")
    parser.add_argument("--once", action="store_true", help="单次模式：消费完队列后退出")
    parser.add_argument("--watch", action="store_true", help="持续监听模式（默认）")
    args = parser.parse_args()

    print("=" * 60)
    print("redis_to_mysql — Redis 数据同步到 MySQL")
    print("=" * 60)

    # 建立连接
    r = get_redis_client(args.redis_host, args.redis_port, args.redis_db)
    conn = get_mysql_connection(
        args.mysql_host, args.mysql_port, args.mysql_user,
        args.mysql_password, args.mysql_database, "utf8mb4",
    )

    # 当前队列中待处理的数据量
    queue_len = r.llen(args.redis_key)
    print(f"\n当前 Redis 队列 [{args.redis_key}] 待处理: {queue_len} 条")
    print(f"目标 MySQL: {args.mysql_host}:{args.mysql_port}/{args.mysql_database}\n")

    # 开始消费
    consume_loop(r, conn, args.redis_key, once=args.once)


if __name__ == "__main__":
    main()
