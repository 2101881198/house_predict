from django.contrib import admin

from houses.models import AnalysisResult, City, CrawlTask, District, House, PredictResult


def test_admin_changelists_do_not_use_date_hierarchy():
    models = [City, District, House, CrawlTask, AnalysisResult, PredictResult]

    for model in models:
        model_admin = admin.site._registry[model]
        assert model_admin.date_hierarchy is None
