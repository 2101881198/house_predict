from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from houses.management.commands.seed_demo_data import build_house_lookup
from houses.models import City, District, House
from houses.services.cleaning import clean_house_record
from houses.services.teacher_data import iter_teacher_house_records


class Command(BaseCommand):
    help = "Import teacher-provided cleaned house CSV data."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_path",
            nargs="?",
            default=str(settings.ROOT_DIR / "house_clean.csv"),
            help="Path to house_clean.csv. Defaults to the project root file.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Import only the first N rows for a quick smoke run.",
        )

    def handle(self, *args, **options):
        # 主流程：读取 CSV -> 转统一字段 -> 清洗 -> 创建城市/区县 -> 写入房源表。
        csv_path = Path(options["csv_path"])
        if not csv_path.exists():
            raise CommandError(f"CSV file does not exist: {csv_path}")

        limit = options["limit"]
        created = 0
        updated = 0
        skipped = 0

        for index, raw_record in enumerate(iter_teacher_house_records(csv_path), start=1):
            if limit is not None and index > limit:
                break
            try:
                record = clean_house_record(raw_record)
                if record is None:
                    # 清洗后为 None 表示这行数据不合格，直接跳过。
                    skipped += 1
                    continue

                city, _ = City.objects.get_or_create(
                    name=record["city"],
                    defaults={"province": "山东省"},
                )
                district, _ = District.objects.get_or_create(
                    city=city,
                    name=record["district"],
                )

                house_values = {
                    "city": city,
                    "district": district,
                    "title": record["title"],
                    "community": record["community"],
                    "total_price": record["total_price"],
                    "unit_price": record["unit_price"],
                    "area": record["area"],
                    "room_type": record["room_type"],
                    "floor": record["floor"],
                    "direction": record["direction"],
                    "decoration": record["decoration"],
                    "build_year": record["build_year"],
                    "address": record["address"],
                    "longitude": record["longitude"],
                    "latitude": record["latitude"],
                    "surrounding": record["surrounding"],
                    "source_url": record["source_url"],
                    "crawl_time": record["crawl_time"],
                }

                _, was_created = House.objects.update_or_create(
                    # update_or_create 可以保证重复导入时更新旧记录，而不是插入重复房源。
                    **build_house_lookup(record, city=city, district=district),
                    defaults=house_values,
                )
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as exc:
                skipped += 1
                self.stderr.write(f"Skipped row {index}: {exc}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created} houses, updated {updated} houses, skipped {skipped} rows."
            )
        )
