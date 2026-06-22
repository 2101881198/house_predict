from io import StringIO

import pytest
from django.core.management import call_command

from houses.models import CrawlTask, House


@pytest.mark.django_db
def test_run_demo_crawler_records_successful_crawl_task():
    out = StringIO()

    call_command("run_demo_crawler", city="济南", pages=1, stdout=out)

    task = CrawlTask.objects.get(task_name="示例采集-济南")
    assert task.target_city == "济南"
    assert task.target_district == ""
    assert task.page_count == 1
    assert task.status == "success"
    assert task.success_count == House.objects.count()
    assert task.fail_count == 0
    assert task.started_at is not None
    assert task.finished_at is not None
    assert task.message == "示例采集器已导入内置山东省房源数据。"
    assert (
        f"Demo crawler task {task.id} finished with {task.success_count} new houses."
        in out.getvalue()
    )
