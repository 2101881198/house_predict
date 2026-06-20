from django.contrib import admin

from .models import AnalysisResult, City, CrawlTask, District, House, PredictResult


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "province", "created_at", "updated_at")
    search_fields = ("name", "province")
    date_hierarchy = "created_at"


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "created_at")
    list_filter = ("city",)
    search_fields = ("name", "city__name")
    date_hierarchy = "created_at"


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "city",
        "district",
        "community",
        "total_price",
        "unit_price",
        "area",
        "room_type",
        "crawl_time",
    )
    list_filter = ("city", "district", "room_type", "decoration", "crawl_time")
    search_fields = ("title", "community", "address", "source_url")
    date_hierarchy = "crawl_time"
    list_select_related = ("city", "district")


@admin.register(CrawlTask)
class CrawlTaskAdmin(admin.ModelAdmin):
    list_display = (
        "task_name",
        "target_city",
        "target_district",
        "page_count",
        "status",
        "success_count",
        "fail_count",
        "created_at",
    )
    list_filter = ("status", "target_city", "created_at")
    search_fields = ("task_name", "target_city", "target_district", "message")
    date_hierarchy = "created_at"


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ("analysis_type", "city", "district", "generated_at")
    list_filter = ("analysis_type", "city", "district", "generated_at")
    search_fields = ("analysis_type", "city__name", "district__name")
    date_hierarchy = "generated_at"
    list_select_related = ("city", "district")


@admin.register(PredictResult)
class PredictResultAdmin(admin.ModelAdmin):
    list_display = (
        "model_name",
        "house",
        "predicted_price",
        "predicted_unit_price",
        "predict_time",
    )
    list_filter = ("model_name", "predict_time")
    search_fields = ("model_name", "house__title", "house__community")
    date_hierarchy = "predict_time"
    list_select_related = ("house",)
