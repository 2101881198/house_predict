#!/bin/bash
# ============================================
#  安装脚本 — CentOS 7 / Python 3.9
#  在 node1 上以 root 执行
# ============================================

set -e

echo "========================================"
echo "  二手房爬虫 — 环境安装 (CentOS 7)"
echo "========================================"

# 1. 检查 Python
echo ""
echo "[1/5] 检查 Python 环境..."
python3 --version
pip3 --version
echo "  OK"

# 2. 安装编译工具（CentOS 7 的 GCC 4.8.5）
echo ""
echo "[2/5] 安装编译工具..."
yum install -y gcc-c++ python3-devel libxml2-devel libxslt-devel openssl-devel
echo "  OK"

# 3. 升级 pip
echo ""
echo "[3/5] 升级 pip/setuptools..."
pip3 install --upgrade pip setuptools wheel -i https://mirrors.aliyun.com/pypi/simple/
echo "  OK"

# 4. 安装依赖（优先使用预编译 wheel）
echo ""
echo "[4/5] 安装 Python 依赖..."
pip3 install -r requirements.txt \
    --only-binary :all: \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    2>&1 || {
    echo "  [警告] --only-binary 失败，回退到源码编译模式..."
    pip3 install -r requirements.txt \
        -i https://mirrors.aliyun.com/pypi/simple/
}
echo "  OK"

# 5. 验证
echo ""
echo "[5/5] 验证安装..."
python3 -c "
import scrapy;           print('scrapy:', scrapy.__version__)
import scrapy_redis;     print('scrapy_redis: OK')
import pandas;           print('pandas:', pandas.__version__)
import numpy;            print('numpy:', numpy.__version__)
import sklearn;          print('scikit-learn:', sklearn.__version__)
import matplotlib;       print('matplotlib:', matplotlib.__version__)
import seaborn;          print('seaborn:', seaborn.__version__)
import lxml;             print('lxml:', lxml.__version__)
import redis;            print('redis:', redis.__version__)
import pymysql;          print('pymysql:', pymysql.__version__)
import requests;         print('requests:', requests.__version__)
import xgboost;          print('xgboost:', xgboost.__version__)
print('')
print('所有依赖安装成功！')
"

echo ""
echo "========================================"
echo "  安装完成！"
echo "========================================"
echo ""
echo "下一步："
echo "  1. 复制项目到 node1~/lesson_liu/"
echo "  2. 启动 Redis: systemctl start redis"
echo "  3. 推送 URL:  python3 part_a/push_urls_to_redis.py"
echo "  4. 启动爬虫:  cd part_a/house_scrapy && scrapy crawl house_spider"
echo "  5. 启动同步:  python3 part_a/redis_to_mysql.py --watch"
