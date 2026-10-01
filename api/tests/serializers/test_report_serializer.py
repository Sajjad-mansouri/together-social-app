import pytest
from django.test import RequestFactory
from rest_framework import serializers

from account.models import Contact
from api.serializers import (
    GeneralReportSerializer,
    ReportProblemSerializer,
    ReportSerializer,
)
from social.models import (
    GeneralProblem,
    Message,
    Report,
    ReportProblem,
)


@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def test_user_2(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User Two",
    )


@pytest.fixture
def test_message(test_user):
    return Message.objects.create(
        user=test_user,
        text="Test message",
    )


@pytest.fixture
def general_problem():
    return GeneralProblem.objects.create(title="Spam")


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def serializer_context(request_factory, test_user):
    request = request_factory.get("/")
    request.user = test_user
    return {"request": request}


@pytest.mark.django_db
class TestGeneralReportSerializer:
    def test_meta_model(self):
        assert GeneralReportSerializer.Meta.model is GeneralProblem

    def test_meta_fields(self):
        assert GeneralReportSerializer.Meta.fields == ["id", "title"]

    def test_serializes_general_problem(self, general_problem):
        serializer = GeneralReportSerializer(general_problem)

        assert serializer.data == {
            "id": general_problem.id,
            "title": "Spam",
        }

    def test_serializes_multiple_general_problems(self, db):
        first = GeneralProblem.objects.create(title="Spam")
        second = GeneralProblem.objects.create(title="Harassment")

        serializer = GeneralReportSerializer(
            [first, second],
            many=True,
        )

        assert serializer.data == [
            {"id": first.id, "title": "Spam"},
            {"id": second.id, "title": "Harassment"},
        ]

    def test_deserializes_title(self):
        serializer = GeneralReportSerializer(data={"title": "Spam"})

        assert serializer.is_valid()
        assert serializer.validated_data["title"] == "Spam"


@pytest.mark.django_db
class TestReportSerializer:
    def test_meta_model(self):
        assert ReportSerializer.Meta.model is Report

    def test_meta_fields(self):
        assert ReportSerializer.Meta.fields == [
            "id",
            "user",
            "object_id",
            "general_report",
            "is_following",
        ]

    def test_to_internal_value_sets_request_user(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        data = {
            "user": test_user_2.id if False else 999999,
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        serializer.is_valid()

        assert serializer.validated_data["user"] == test_user

    def test_to_internal_value_replaces_submitted_user(
        self,
        serializer_context,
        test_user,
        test_user_2,
        test_message,
        general_problem,
    ):
        data = {
            "user": test_user_2.id,
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid()

        assert serializer.validated_data["user"] == test_user
        assert serializer.validated_data["user"] != test_user_2

    def test_to_internal_value_stores_post_owner(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        serializer.is_valid()

        assert serializer.post_owner == test_user.username

    def test_to_internal_value_sets_content_type_for_post(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        serializer.is_valid()

        assert serializer.content_type == "post"

    def test_to_internal_value_removes_post_owner_from_data(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        serializer.is_valid()

        assert "post_owner" not in serializer.validated_data

    def test_follow_returns_true_when_user_follows_post_owner(
        self,
        serializer_context,
        test_user,
        test_user_2,
        test_message,
        general_problem,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user_2.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        serializer.is_valid()

        assert serializer.follow(None) is True

    def test_follow_returns_false_when_user_does_not_follow_post_owner(
        self,
        serializer_context,
        test_user,
        test_user_2,
        test_message,
        general_problem,
    ):
        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user_2.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        serializer.is_valid()

        assert serializer.follow(None) is False

    def test_follow_returns_false_for_unknown_post_owner(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": "does-not-exist",
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        serializer.is_valid()

        assert serializer.follow(None) is False

    def test_is_following_field_is_serializer_method_field(self):
        field = ReportSerializer().fields["is_following"]

        assert isinstance(field, serializers.SerializerMethodField)

    def test_create_creates_report_for_post(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid()

        report = serializer.save()

        assert isinstance(report, Report)
        assert report.user == test_user
        assert report.content_object == test_message
        assert report.general_report == general_problem

    def test_create_creates_report_for_user(
        self,
        serializer_context,
        test_user,
        test_user_2,
        general_problem,
    ):
        data = {
            "object_id": test_user_2.id,
            "general_report": general_problem.id,
            "post_owner": test_user_2.username,
            "content_type": "user",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        # The serializer currently only sets content_type for "post".
        # Set it explicitly so create() exercises its "user" branch.
        serializer.content_type = "user"

        assert serializer.is_valid()

        report = serializer.save()

        assert isinstance(report, Report)
        assert report.user == test_user
        assert report.content_object == test_user_2
        assert report.general_report == general_problem

    def test_is_valid_returns_true_for_valid_data(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid() is True

    def test_user_is_not_required_from_client(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        data = {
            "object_id": test_message.id,
            "general_report": general_problem.id,
            "post_owner": test_user.username,
            "content_type": "post",
        }

        serializer = ReportSerializer(
            data=data,
            context=serializer_context,
        )

        assert serializer.is_valid()
        assert serializer.validated_data["user"] == test_user


@pytest.mark.django_db
class TestReportProblemSerializer:
    def test_meta_model(self):
        assert ReportProblemSerializer.Meta.model is ReportProblem

    def test_meta_fields(self):
        assert ReportProblemSerializer.Meta.fields == [
            "user",
            "report",
        ]

    def test_to_internal_value_sets_request_user(
        self,
        serializer_context,
        test_user,
        general_problem,
    ):
        report = Report.objects.create(
            user=test_user,
            content_object=test_user,
            general_report=general_problem,
        )

        serializer = ReportProblemSerializer(
            data={"report": report.id},
            context=serializer_context,
        )

        assert serializer.is_valid(False)

        assert serializer.validated_data["user"] == test_user

    def test_submitted_user_is_ignored(
        self,
        serializer_context,
        test_user,
        test_user_2,
        general_problem,
    ):
        report = Report.objects.create(
            user=test_user,
            content_object=test_user,
            general_report=general_problem,
        )

        serializer = ReportProblemSerializer(
            data={
                "user": test_user_2.id,
                "report": report.id,
            },
            context=serializer_context,
        )

        assert serializer.is_valid(False)

        assert serializer.validated_data["user"] == test_user
        assert serializer.validated_data["user"] != test_user_2

    def test_user_is_added_when_missing(
        self,
        serializer_context,
        test_user,
        general_problem,
    ):
        report = Report.objects.create(
            user=test_user,
            content_object=test_user,
            general_report=general_problem,
        )

        serializer = ReportProblemSerializer(
            data={"report": report.id},
            context=serializer_context,
        )

        assert serializer.is_valid(False)

        assert serializer.validated_data["user"] == test_user

    def test_validation_accepts_valid_report(
        self,
        serializer_context,
        test_user,
        general_problem,
    ):
        report = Report.objects.create(
            user=test_user,
            content_object=test_user,
            general_report=general_problem,
        )

        serializer = ReportProblemSerializer(
            data={"report": report.id},
            context=serializer_context,
        )

        assert serializer.is_valid(False) is True
        assert serializer.errors == {}

    def test_save_creates_report_problem(
        self,
        serializer_context,
        test_user,
        general_problem,
    ):
        report = Report.objects.create(
            user=test_user,
            content_object=test_user,
            general_report=general_problem,
        )

        serializer = ReportProblemSerializer(
            data={"report": report.id},
            context=serializer_context,
        )

        assert serializer.is_valid(False)

        report_problem = serializer.save()

        assert isinstance(report_problem, ReportProblem)
        assert report_problem.report == str(report.id)
        assert report_problem.user == test_user

    def test_save_uses_request_user_not_submitted_user(
        self,
        serializer_context,
        test_user,
        test_user_2,
        general_problem,
    ):
        report = Report.objects.create(
            user=test_user,
            content_object=test_user,
            general_report=general_problem,
        )

        serializer = ReportProblemSerializer(
            data={
                "user": test_user_2.id,
                "report": report.id,
            },
            context=serializer_context,
        )

        assert serializer.is_valid(False)

        report_problem = serializer.save()

        assert report_problem.user == test_user
        assert report_problem.user != test_user_2

    def test_report_is_required(
        self,
        serializer_context,
        test_user,
    ):
        serializer = ReportProblemSerializer(
            data={},
            context=serializer_context,
        )

        assert serializer.is_valid(False) is False
        assert "report" in serializer.errors
