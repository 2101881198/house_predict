from django.urls import path  # 导入 Django 的 URL 路由定义函数

from . import views  # 从当前应用目录导入 views 视图模块

app_name = "houses"  # 设置应用命名空间，便于反向解析 URL（如 {% url 'houses:dashboard' %}）

urlpatterns = [
    path("", views.dashboard, name="dashboard"),  # 仪表盘首页，展示数据概览
    path("province/", views.province, name="province"),  # 省份级统计页面，显示各城市汇总数据
    path("cities/<int:city_id>/", views.city_detail, name="city_detail"),  # 城市详情页，展示某城市下房源及价格分布
    path("houses/", views.house_list, name="house_list"),  # 房源列表页，支持分页、筛选与排序
    path("houses/<int:house_id>/", views.house_detail, name="house_detail"),  # 房源详情页，展示单套房源全部信息
    path("predict/", views.predict_page, name="predict"),  # 房价预测页面，提供预测表单和最近预测记录
    path("api/houses/", views.api_houses, name="api_houses"),  # API：获取房源列表（JSON），支持查询参数过滤
    path("api/houses/<int:house_id>/", views.api_house_detail, name="api_house_detail"),  # API：获取单个房源详情（JSON）
    path("api/statistics/overview/", views.api_overview, name="api_overview"),  # API：获取全局统计概览（总房源数、平均价格等）
    path("api/statistics/province/", views.api_province, name="api_province"),  # API：获取省份级统计数据（各城市指标）
    path("api/statistics/city/", views.api_city, name="api_city"),  # API：获取城市级统计数据（需传城市参数）
    path("api/predict/price/", views.api_predict_price, name="api_predict_price"),  # API：执行房价预测，POST 提交特征后返回预测结果
    path("api/admin/crawl-tasks/", views.api_crawl_tasks, name="api_crawl_tasks"),  # API：爬虫任务管理，查看/创建爬取任务
]