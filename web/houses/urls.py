from django.urls import path

from . import views


app_name = "houses"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("province/", views.province, name="province"),
    path("cities/<int:city_id>/", views.city_detail, name="city_detail"),
    path("houses/", views.house_list, name="house_list"),
    path("houses/<int:house_id>/", views.house_detail, name="house_detail"),
    path("predict/", views.predict_page, name="predict"),
    path("api/houses/", views.api_houses, name="api_houses"),
    path("api/houses/<int:house_id>/", views.api_house_detail, name="api_house_detail"),
    path("api/statistics/overview/", views.api_overview, name="api_overview"),
    path("api/statistics/province/", views.api_province, name="api_province"),
    path("api/statistics/city/", views.api_city, name="api_city"),
    path("api/predict/price/", views.api_predict_price, name="api_predict_price"),
    path("api/admin/crawl-tasks/", views.api_crawl_tasks, name="api_crawl_tasks"),
]
