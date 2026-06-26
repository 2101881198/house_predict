from django.core.management.base import BaseCommand
from django.utils import timezone

from houses.models import AnalysisResult, City
from houses.services.analysis import (
    build_city_stats,
    build_overview,
    build_price_buckets,
    build_province_stats,
    build_room_type_distribution,
)


def upsert_analysis_result(analysis_type, result, city=None, district=None):
    # 更新或创建一条统计缓存；如果同类型缓存重复存在，会保留一条并删除多余的。
    filters = {"analysis_type": analysis_type}
    if city is None:
        filters["city__isnull"] = True
    else:
        filters["city"] = city
    if district is None:
        filters["district__isnull"] = True
    else:
        filters["district"] = district

    existing = AnalysisResult.objects.filter(**filters).order_by("id")
    analysis_result = existing.first()
    generated_at = timezone.now()

    if analysis_result is None:
        return AnalysisResult.objects.create(
            analysis_type=analysis_type,
            city=city,
            district=district,
            result_json=result,
            generated_at=generated_at,
        )

    analysis_result.result_json = result
    analysis_result.generated_at = generated_at
    analysis_result.save(update_fields=["result_json", "generated_at", "updated_at"])
    existing.exclude(pk=analysis_result.pk).delete()
    return analysis_result


class Command(BaseCommand):
    help = "Generate cached house market analysis payloads."

    def handle(self, *args, **options):
        # 生成全局统计和每个城市的统计结果，保存到 AnalysisResult 表。
        payloads = {
            "overview": build_overview(),
            "province": build_province_stats(),
            "price_buckets": {"items": build_price_buckets()},
            "room_types": {"items": build_room_type_distribution()},
        }

        for analysis_type, result_json in payloads.items():
            upsert_analysis_result(analysis_type, result_json)

        city_count = 0
        for city in City.objects.all():
            upsert_analysis_result(
                "city",
                build_city_stats(city.id),
                city=city,
                district=None,
            )
            city_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {len(payloads) + city_count} analysis results."
            )
        )
