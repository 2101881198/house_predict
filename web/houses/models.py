from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class City(TimeStampedModel):
    name = models.CharField("城市", max_length=50, unique=True)
    province = models.CharField("省份", max_length=50, default="山东省")

    class Meta:
        ordering = ["name"]
        verbose_name = "城市"
        verbose_name_plural = "城市"

    def __str__(self):
        return self.name


class District(TimeStampedModel):
    city = models.ForeignKey(
        City,
        on_delete=models.CASCADE,
        related_name="districts",
        verbose_name="城市",
    )
    name = models.CharField("区县", max_length=50)

    class Meta:
        ordering = ["city__name", "name"]
        unique_together = [["city", "name"]]
        verbose_name = "区县"
        verbose_name_plural = "区县"

    def __str__(self):
        return f"{self.city} {self.name}"


class House(TimeStampedModel):
    title = models.CharField("标题", max_length=200)
    city = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        related_name="houses",
        verbose_name="城市",
    )
    district = models.ForeignKey(
        District,
        on_delete=models.PROTECT,
        related_name="houses",
        verbose_name="区县",
    )
    community = models.CharField("小区", max_length=100, blank=True)
    total_price = models.DecimalField("总价", max_digits=10, decimal_places=2, db_index=True)
    unit_price = models.DecimalField("单价", max_digits=10, decimal_places=2, db_index=True)
    area = models.DecimalField("面积", max_digits=8, decimal_places=2, db_index=True)
    room_type = models.CharField("户型", max_length=50, db_index=True)
    floor = models.CharField("楼层", max_length=50, blank=True)
    direction = models.CharField("朝向", max_length=50, blank=True)
    decoration = models.CharField("装修", max_length=50, blank=True, db_index=True)
    build_year = models.PositiveIntegerField("建造年份", null=True, blank=True)
    address = models.CharField("地址", max_length=255, blank=True)
    longitude = models.DecimalField("经度", max_digits=10, decimal_places=6, null=True, blank=True)
    latitude = models.DecimalField("纬度", max_digits=10, decimal_places=6, null=True, blank=True)
    surrounding = models.TextField("周边配套", blank=True)
    source_url = models.CharField("来源链接", max_length=500, unique=True, null=True, blank=True)
    crawl_time = models.DateTimeField("爬取时间", db_index=True)

    class Meta:
        ordering = ["-crawl_time", "-id"]
        indexes = [
            models.Index(fields=["city", "district"], name="house_city_district_idx"),
            models.Index(fields=["total_price", "area"], name="house_price_area_idx"),
        ]
        verbose_name = "房源"
        verbose_name_plural = "房源"

    def __str__(self):
        return f"{self.city} {self.title}"


class CrawlTask(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "待执行"
        RUNNING = "running", "执行中"
        SUCCESS = "success", "成功"
        FAILED = "failed", "失败"

    task_name = models.CharField("任务名称", max_length=100)
    target_city = models.CharField("目标城市", max_length=50)
    target_district = models.CharField("目标区县", max_length=50, blank=True)
    page_count = models.PositiveIntegerField("页数", default=1)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    success_count = models.PositiveIntegerField("成功数量", default=0)
    fail_count = models.PositiveIntegerField("失败数量", default=0)
    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    finished_at = models.DateTimeField("完成时间", null=True, blank=True)
    message = models.TextField("消息", blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "爬取任务"
        verbose_name_plural = "爬取任务"

    def __str__(self):
        return self.task_name


class AnalysisResult(TimeStampedModel):
    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        related_name="analysis_results",
        null=True,
        blank=True,
        verbose_name="城市",
    )
    district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        related_name="analysis_results",
        null=True,
        blank=True,
        verbose_name="区县",
    )
    analysis_type = models.CharField("分析类型", max_length=50, db_index=True)
    result_json = models.JSONField("分析结果")
    generated_at = models.DateTimeField("生成时间", default=timezone.now)

    class Meta:
        ordering = ["-generated_at"]
        verbose_name = "分析结果"
        verbose_name_plural = "分析结果"

    def __str__(self):
        return f"{self.analysis_type} {self.generated_at:%Y-%m-%d %H:%M}"


class PredictResult(TimeStampedModel):
    house = models.ForeignKey(
        House,
        on_delete=models.SET_NULL,
        related_name="predict_results",
        null=True,
        blank=True,
        verbose_name="房源",
    )
    input_features = models.JSONField("输入特征")
    predicted_price = models.DecimalField("预测总价", max_digits=10, decimal_places=2)
    predicted_unit_price = models.DecimalField("预测单价", max_digits=10, decimal_places=2)
    model_name = models.CharField("模型名称", max_length=100)
    predict_time = models.DateTimeField("预测时间", default=timezone.now)

    class Meta:
        ordering = ["-predict_time"]
        verbose_name = "预测结果"
        verbose_name_plural = "预测结果"

    def __str__(self):
        return f"{self.model_name} {self.predicted_price}"
