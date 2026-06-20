from django.core.management.base import BaseCommand
from django.utils import timezone

from houses.models import AnalysisResult
from houses.services.analysis import (
    build_overview,
    build_price_buckets,
    build_province_stats,
    build_room_type_distribution,
)


class Command(BaseCommand):
    help = "Generate cached house market analysis payloads."

    def handle(self, *args, **options):
        payloads = {
            "overview": build_overview(),
            "province": build_province_stats(),
            "price_buckets": build_price_buckets(),
            "room_types": build_room_type_distribution(),
        }

        for analysis_type, result_json in payloads.items():
            AnalysisResult.objects.update_or_create(
                analysis_type=analysis_type,
                city=None,
                district=None,
                defaults={
                    "result_json": result_json,
                    "generated_at": timezone.now(),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(f"Generated {len(payloads)} analysis results.")
        )
