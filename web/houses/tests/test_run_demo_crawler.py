from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from houses.management.commands import run_demo_crawler
from houses.models import CrawlTask, House
from houses.sample_data import DEMO_HOUSES


@pytest.mark.django_db
def test_run_demo_crawler_records_successful_crawl_task():
    out = StringIO()

    call_command("run_demo_crawler", city="济南", pages=1, stdout=out)

    task = CrawlTask.objects.get(task_name="示例采集-济南")
    assert task.target_city == "济南"
    assert task.target_district == ""
    assert task.page_count == 1
    assert task.status == "success"
    assert task.success_count == len(DEMO_HOUSES)
    assert task.fail_count == 0
    assert task.started_at is not None
    assert task.finished_at is not None
    assert "Processed" in task.message
    assert str(len(DEMO_HOUSES)) in task.message
    assert (
        f"Demo crawler task {task.id} finished with {task.success_count} demo houses"
        in out.getvalue()
    )


@pytest.mark.django_db
def test_run_demo_crawler_rerun_keeps_useful_success_count():
    first_out = StringIO()
    second_out = StringIO()

    call_command("run_demo_crawler", city="济南", pages=1, stdout=first_out)
    call_command("run_demo_crawler", city="济南", pages=1, stdout=second_out)

    tasks = list(CrawlTask.objects.order_by("id"))
    assert len(tasks) == 2
    assert [task.status for task in tasks] == ["success", "success"]
    assert [task.success_count for task in tasks] == [len(DEMO_HOUSES), len(DEMO_HOUSES)]
    assert House.objects.count() == len(DEMO_HOUSES)
    assert "0 new houses" in second_out.getvalue()


@pytest.mark.django_db
def test_run_demo_crawler_marks_task_failed_when_seed_raises(monkeypatch):
    def raise_seed_error(*args, **kwargs):
        raise RuntimeError("seed exploded")

    monkeypatch.setattr(run_demo_crawler, "call_command", raise_seed_error)

    with pytest.raises(CommandError, match="Demo crawler failed"):
        call_command("run_demo_crawler", city="济南", pages=1)

    task = CrawlTask.objects.get()
    assert task.status == "failed"
    assert task.success_count == 0
    assert task.fail_count == 1
    assert task.finished_at is not None
    assert "seed exploded" in task.message
