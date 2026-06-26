"""
定义房源数据 Item

字段清单（共 23 个）：
  基础：城市、地区、链接、房子单价、所在区域、小区名称
  房屋属性：房屋户型、所在楼层、建筑面积、户型结构、房屋朝向、
            建筑结构、装修情况
  交易信息：梯户比例、挂牌时间、交易权属、产权所属、抵押信息
  介绍：核心卖点、小区介绍、户型介绍、交通出行
  坐标：经度、纬度
"""

import scrapy


class HouseItem(scrapy.Item):
    """二手房房源数据模型 — 全部字段与任务需求完全对齐"""

    # ============ 基础信息 ============
    city = scrapy.Field()                   # 城市（如"青岛"）
    district = scrapy.Field()               # 地区（如"李沧"）
    url = scrapy.Field()                    # 链接（房源详情页URL）
    house_title = scrapy.Field()            # 标题

    # ============ 价格 ============
    unit_price = scrapy.Field()             # 房子单价（元/㎡）
    total_price = scrapy.Field()            # 总价（万元）

    # ============ 位置 ============
    community_name = scrapy.Field()         # 小区名称
    area_name = scrapy.Field()              # 所在区域（区域+商圈）
    biz_circle = scrapy.Field()             # 商圈

    # ============ 房屋属性 ============
    house_layout = scrapy.Field()           # 房屋户型（如"3室2厅"）
    floor_position = scrapy.Field()         # 所在楼层（如"低楼层/共6层"）
    building_area = scrapy.Field()          # 建筑面积（㎡）
    layout_structure = scrapy.Field()       # 户型结构（平层/跃层/复式）
    orientation = scrapy.Field()            # 房屋朝向（南/南北/东南等）
    building_structure = scrapy.Field()     # 建筑结构（钢混/砖混/框架/剪力墙）
    decoration = scrapy.Field()             # 装修情况（精装/简装/毛坯/豪装）
    building_type = scrapy.Field()          # 建筑类型（板楼/塔楼/板塔结合）
    build_year = scrapy.Field()             # 建成年份

    # ============ 交易信息 ============
    elevator_ratio = scrapy.Field()         # 梯户比例（如"一梯两户"）
    listing_time = scrapy.Field()           # 挂牌时间
    transaction_ownership = scrapy.Field()  # 交易权属（商品房/经适房等）
    property_ownership = scrapy.Field()     # 产权所属（共有/非共有/个人）
    mortgage_info = scrapy.Field()          # 抵押信息
    property_rights = scrapy.Field()        # 产权年限
    usage = scrapy.Field()                  # 房屋用途
    has_elevator = scrapy.Field()           # 配备电梯
    heating = scrapy.Field()                # 供暖方式
    deed_year = scrapy.Field()              # 房本年限
    last_trade = scrapy.Field()             # 上次交易

    # ============ 配套介绍 ============
    key_selling_points = scrapy.Field()     # 核心卖点
    community_intro = scrapy.Field()        # 小区介绍
    layout_intro = scrapy.Field()           # 户型介绍
    transportation = scrapy.Field()         # 交通出行

    # ============ 地理坐标 ============
    longitude = scrapy.Field()              # 经度
    latitude = scrapy.Field()               # 纬度

    # ============ 爬取元信息 ============
    crawl_time = scrapy.Field()             # 爬取时间
