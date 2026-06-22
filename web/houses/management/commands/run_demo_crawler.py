from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from houses.models import CrawlTask, House
from houses.sample_data import DEMO_HOUSES


class Command(BaseCommand):
    help = "Run the course-project demo crawler flow using bundled sample data."

    def add_arguments(self, parser):
        parser.add_argument("--city", default="济南")
        parser.add_argument("--district", default="")
        parser.add_argument("--pages", type=int, default=1)

    def handle(self, *args, **options):
        city = options["city"]
        district = options["district"]
        pages = options["pages"]

        task = CrawlTask.objects.create(
            task_name=f"示例采集-{city}",
            target_city=city,
            target_district=district,
            page_count=pages,
            status="running",
            started_at=timezone.now(),
        )

        before_count = House.objects.count()
        try:
            call_command("seed_demo_data")
        except Exception as exc:
            task.status = "failed"
            task.fail_count = 1
            task.finished_at = timezone.now()
            task.message = f"Demo crawler failed: {exc}"
            task.save()
            raise CommandError(f"Demo crawler failed: {exc}") from exc

        after_count = House.objects.count()
        new_count = max(after_count - before_count, 0)
        processed_count = len(DEMO_HOUSES)

        task.status = "success"
        task.success_count = processed_count
        task.fail_count = 0
        task.finished_at = timezone.now()
        task.message = (
            f"Processed {processed_count} bundled demo houses; "
            f"imported {new_count} new houses."
        )
        task.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo crawler task {task.id} finished with "
                f"{task.success_count} demo houses ({new_count} new houses)."
            )
        )
