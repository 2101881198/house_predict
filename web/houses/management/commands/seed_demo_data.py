from django.core.management.base import BaseCommand

from houses.models import City, District, House
from houses.sample_data import DEMO_HOUSES
from houses.services.cleaning import clean_house_record


class Command(BaseCommand):
    help = "Import bundled deterministic demo house data."

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for raw_record in DEMO_HOUSES:
            try:
                record = clean_house_record(raw_record)
                if record is None:
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

                if record["source_url"]:
                    _, was_created = House.objects.update_or_create(
                        source_url=record["source_url"],
                        defaults=house_values,
                    )
                else:
                    lookup = {
                        "title": record["title"],
                        "community": record["community"],
                        "area": record["area"],
                        "total_price": record["total_price"],
                    }
                    _, was_created = House.objects.update_or_create(
                        **lookup,
                        defaults=house_values,
                    )

                if was_created:
                    created += 1
            except Exception as exc:
                skipped += 1
                self.stderr.write(f"Skipped invalid demo record: {exc}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {created} houses, skipped {skipped} invalid records."
            )
        )
