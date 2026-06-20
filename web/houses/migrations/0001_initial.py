# Generated manually because Django is unavailable in this environment.

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="City",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=50, unique=True, verbose_name="城市")),
                ("province", models.CharField(default="山东省", max_length=50, verbose_name="省份")),
            ],
            options={
                "verbose_name": "城市",
                "verbose_name_plural": "城市",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="District",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=50, verbose_name="区县")),
                (
                    "city",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="districts",
                        to="houses.city",
                        verbose_name="城市",
                    ),
                ),
            ],
            options={
                "verbose_name": "区县",
                "verbose_name_plural": "区县",
                "ordering": ["city__name", "name"],
                "unique_together": {("city", "name")},
            },
        ),
        migrations.CreateModel(
            name="CrawlTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("task_name", models.CharField(max_length=100, verbose_name="任务名称")),
                ("target_city", models.CharField(max_length=50, verbose_name="目标城市")),
                ("target_district", models.CharField(blank=True, max_length=50, verbose_name="目标区县")),
                ("page_count", models.PositiveIntegerField(default=1, verbose_name="页数")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "待执行"),
                            ("running", "执行中"),
                            ("success", "成功"),
                            ("failed", "失败"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="状态",
                    ),
                ),
                ("success_count", models.PositiveIntegerField(default=0, verbose_name="成功数量")),
                ("fail_count", models.PositiveIntegerField(default=0, verbose_name="失败数量")),
                ("started_at", models.DateTimeField(blank=True, null=True, verbose_name="开始时间")),
                ("finished_at", models.DateTimeField(blank=True, null=True, verbose_name="完成时间")),
                ("message", models.TextField(blank=True, verbose_name="消息")),
            ],
            options={
                "verbose_name": "爬取任务",
                "verbose_name_plural": "爬取任务",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="House",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=200, verbose_name="标题")),
                ("community", models.CharField(blank=True, max_length=100, verbose_name="小区")),
                (
                    "total_price",
                    models.DecimalField(db_index=True, decimal_places=2, max_digits=10, verbose_name="总价"),
                ),
                (
                    "unit_price",
                    models.DecimalField(db_index=True, decimal_places=2, max_digits=10, verbose_name="单价"),
                ),
                ("area", models.DecimalField(db_index=True, decimal_places=2, max_digits=8, verbose_name="面积")),
                ("room_type", models.CharField(db_index=True, max_length=50, verbose_name="户型")),
                ("floor", models.CharField(blank=True, max_length=50, verbose_name="楼层")),
                ("direction", models.CharField(blank=True, max_length=50, verbose_name="朝向")),
                ("decoration", models.CharField(blank=True, db_index=True, max_length=50, verbose_name="装修")),
                ("build_year", models.PositiveIntegerField(blank=True, null=True, verbose_name="建造年份")),
                ("address", models.CharField(blank=True, max_length=255, verbose_name="地址")),
                (
                    "longitude",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True, verbose_name="经度"),
                ),
                (
                    "latitude",
                    models.DecimalField(blank=True, decimal_places=6, max_digits=10, null=True, verbose_name="纬度"),
                ),
                ("surrounding", models.TextField(blank=True, verbose_name="周边配套")),
                (
                    "source_url",
                    models.CharField(blank=True, max_length=500, null=True, unique=True, verbose_name="来源链接"),
                ),
                ("crawl_time", models.DateTimeField(db_index=True, verbose_name="爬取时间")),
                (
                    "city",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="houses",
                        to="houses.city",
                        verbose_name="城市",
                    ),
                ),
                (
                    "district",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="houses",
                        to="houses.district",
                        verbose_name="区县",
                    ),
                ),
            ],
            options={
                "verbose_name": "房源",
                "verbose_name_plural": "房源",
                "ordering": ["-crawl_time", "-id"],
                "indexes": [
                    models.Index(fields=["city", "district"], name="house_city_district_idx"),
                    models.Index(fields=["total_price", "area"], name="house_price_area_idx"),
                ],
            },
        ),
        migrations.CreateModel(
            name="AnalysisResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("analysis_type", models.CharField(db_index=True, max_length=50, verbose_name="分析类型")),
                ("result_json", models.JSONField(verbose_name="分析结果")),
                ("generated_at", models.DateTimeField(default=django.utils.timezone.now, verbose_name="生成时间")),
                (
                    "city",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis_results",
                        to="houses.city",
                        verbose_name="城市",
                    ),
                ),
                (
                    "district",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analysis_results",
                        to="houses.district",
                        verbose_name="区县",
                    ),
                ),
            ],
            options={
                "verbose_name": "分析结果",
                "verbose_name_plural": "分析结果",
                "ordering": ["-generated_at"],
            },
        ),
        migrations.CreateModel(
            name="PredictResult",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("input_features", models.JSONField(verbose_name="输入特征")),
                (
                    "predicted_price",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="预测总价"),
                ),
                (
                    "predicted_unit_price",
                    models.DecimalField(decimal_places=2, max_digits=10, verbose_name="预测单价"),
                ),
                ("model_name", models.CharField(max_length=100, verbose_name="模型名称")),
                ("predict_time", models.DateTimeField(default=django.utils.timezone.now, verbose_name="预测时间")),
                (
                    "house",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="predict_results",
                        to="houses.house",
                        verbose_name="房源",
                    ),
                ),
            ],
            options={
                "verbose_name": "预测结果",
                "verbose_name_plural": "预测结果",
                "ordering": ["-predict_time"],
            },
        ),
    ]
