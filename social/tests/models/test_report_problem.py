import pytest
from django.db import models
from django.utils import timezone

from social.models import ReportProblem


@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_user_2(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_report_problem(test_user):
    return ReportProblem.objects.create(
        user=test_user,
        report="This is a test report.",
    )


@pytest.mark.django_db
class TestReportProblem:
    def test_report_problem_can_be_created(self, test_user):
        report_problem = ReportProblem.objects.create(
            user=test_user,
            report="This is a test report.",
        )

        assert report_problem.pk is not None
        assert report_problem.user == test_user
        assert report_problem.report == "This is a test report."

    def test_user_field_is_foreign_key(self):
        field = ReportProblem._meta.get_field("user")

        assert isinstance(field, models.ForeignKey)

    def test_user_field_points_to_user_model(
        self,
        django_user_model,
    ):
        field = ReportProblem._meta.get_field("user")

        assert field.remote_field.model is django_user_model

    def test_user_field_uses_cascade_delete(self):
        field = ReportProblem._meta.get_field("user")

        assert field.remote_field.on_delete is models.CASCADE

    def test_user_relationship(
        self,
        test_report_problem,
        test_user,
    ):
        assert test_report_problem.user == test_user
        assert test_report_problem.user_id == test_user.pk

    def test_report_field_is_text_field(self):
        field = ReportProblem._meta.get_field("report")

        assert isinstance(field, models.TextField)

    def test_report_field_is_required(self):
        field = ReportProblem._meta.get_field("report")

        assert field.null is False
        assert field.blank is False

    def test_report_text_is_persisted(
        self,
        test_report_problem,
    ):
        report_problem = ReportProblem.objects.get(
            pk=test_report_problem.pk,
        )

        assert report_problem.report == "This is a test report."

    def test_created_field_is_datetime_field(self):
        field = ReportProblem._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)

    def test_created_uses_auto_now_add(self):
        field = ReportProblem._meta.get_field("created")

        assert field.auto_now_add is True

    def test_created_is_set_automatically(self, test_user):
        before = timezone.now()

        report_problem = ReportProblem.objects.create(
            user=test_user,
            report="This is a test report.",
        )

        after = timezone.now()

        assert before <= report_problem.created <= after

    def test_created_is_not_changed_on_update(
        self,
        test_report_problem,
    ):
        original_created = test_report_problem.created

        test_report_problem.report = "Updated report."
        test_report_problem.save()
        test_report_problem.refresh_from_db()

        assert test_report_problem.created == original_created

    def test_report_can_be_updated(
        self,
        test_report_problem,
    ):
        test_report_problem.report = "Updated report."
        test_report_problem.save()
        test_report_problem.refresh_from_db()

        assert test_report_problem.report == "Updated report."

    def test_different_users_can_create_reports(
        self,
        test_user,
        test_user_2,
    ):
        first_report = ReportProblem.objects.create(
            user=test_user,
            report="First report.",
        )
        second_report = ReportProblem.objects.create(
            user=test_user_2,
            report="Second report.",
        )

        assert first_report.pk != second_report.pk
        assert first_report.user == test_user
        assert second_report.user == test_user_2

    def test_user_can_create_multiple_reports(
        self,
        test_user,
    ):
        first_report = ReportProblem.objects.create(
            user=test_user,
            report="First report.",
        )
        second_report = ReportProblem.objects.create(
            user=test_user,
            report="Second report.",
        )

        assert first_report.pk != second_report.pk
        assert ReportProblem.objects.filter(user=test_user).count() == 2

    def test_deleting_user_deletes_report_problems(
        self,
        test_report_problem,
        test_user,
    ):
        report_problem_id = test_report_problem.pk

        test_user.delete()

        assert not ReportProblem.objects.filter(
            pk=report_problem_id,
        ).exists()

    def test_queryset_contains_created_instance(
        self,
        test_report_problem,
    ):
        assert ReportProblem.objects.filter(
            pk=test_report_problem.pk,
        ).exists()
