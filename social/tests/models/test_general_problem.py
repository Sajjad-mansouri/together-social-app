import pytest
from django.db import models
from django.utils import timezone

from social.models import GeneralProblem


@pytest.fixture
def test_general_problem(db):
    return GeneralProblem.objects.create(
        title="Test general problem",
    )


@pytest.mark.django_db
class TestGeneralProblem:
    def test_general_problem_can_be_created(self):
        problem = GeneralProblem.objects.create(
            title="Test general problem",
        )

        assert problem.pk is not None
        assert problem.title == "Test general problem"

    def test_title_field_is_char_field(self):
        field = GeneralProblem._meta.get_field("title")

        assert isinstance(field, models.CharField)

    def test_title_max_length(self):
        field = GeneralProblem._meta.get_field("title")

        assert field.max_length == 200

    def test_title_is_required(self):
        field = GeneralProblem._meta.get_field("title")

        assert field.null is False
        assert field.blank is False

    def test_created_field_is_datetime_field(self):
        field = GeneralProblem._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)

    def test_created_uses_auto_now_add(self):
        field = GeneralProblem._meta.get_field("created")

        assert field.auto_now_add is True

    def test_created_is_set_automatically(self):
        before = timezone.now()

        problem = GeneralProblem.objects.create(
            title="Test general problem",
        )

        after = timezone.now()

        assert before <= problem.created <= after

    def test_created_is_not_changed_on_update(
        self,
        test_general_problem,
    ):
        original_created = test_general_problem.created

        test_general_problem.title = "Updated problem"
        test_general_problem.save()
        test_general_problem.refresh_from_db()

        assert test_general_problem.created == original_created

    def test_str_returns_title(self, test_general_problem):
        assert str(test_general_problem) == test_general_problem.title

    def test_str_returns_exact_title(self):
        problem = GeneralProblem.objects.create(
            title="Password reset problem",
        )

        assert str(problem) == "Password reset problem"

    def test_title_is_persisted(self, test_general_problem):
        problem = GeneralProblem.objects.get(
            pk=test_general_problem.pk,
        )

        assert problem.title == "Test general problem"

    def test_title_accepts_exact_maximum_length(self):
        title = "a" * 200

        problem = GeneralProblem.objects.create(
            title=title,
        )

        assert problem.title == title
        assert len(problem.title) == 200
