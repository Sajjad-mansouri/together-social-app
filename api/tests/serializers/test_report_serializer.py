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


@pytest.fixture
def test_report(test_user, test_message, general_problem):
    return Report.objects.create(
        user=test_user,
        content_object=test_message,
        general_report=general_problem,
    )


@pytest.mark.django_db
class TestGeneralReportSerializer:
    def test_meta_model(self):
        assert GeneralReportSerializer.Meta.model is GeneralProblem

    def test_meta_fields(self):
        assert GeneralReportSerializer.Meta.fields == [
            "id",
            "title",
        ]

    def test_serializes_general_problem(self, general_problem):
        serializer = GeneralReportSerializer(general_problem)

        assert serializer.data == {
            "id": general_problem.id,
            "title": "Spam",
        }

    def test_serializes_multiple_general_problems(self):
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
        serializer = GeneralReportSerializer(
            data={"title": "Spam"},
        )

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data["title"] == "Spam"


@pytest.mark.django_db
class TestReportSerializer:
    def test_meta_model(self):
        assert ReportSerializer.Meta.model is Report

    def test_meta_fields(self):
        assert ReportSerializer.Meta.fields == [
            "id",
            "object_id",
            "general_report",
            "content_type",
            "post_owner",
            "is_following",
        ]

    def test_content_type_is_write_only(self):
        serializer = ReportSerializer()

        assert serializer.fields["content_type"].write_only is True

    def test_post_owner_is_write_only(self):
        serializer = ReportSerializer()

        assert serializer.fields["post_owner"].write_only is True

    def test_is_following_is_serializer_method_field(self):
        serializer = ReportSerializer()

        assert isinstance(
            serializer.fields["is_following"],
            serializers.SerializerMethodField,
        )

    def test_is_following_is_read_only(self):
        serializer = ReportSerializer()

        assert serializer.fields["is_following"].read_only is True

    def test_id_is_read_only(self):
        serializer = ReportSerializer()

        assert serializer.fields["id"].read_only is True

    def test_valid_post_data(
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

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["object_id"] == test_message.id
        assert serializer.validated_data["general_report"] == general_problem
        assert serializer.validated_data["content_type"] == "post"
        assert serializer.validated_data["post_owner"] == test_user.username

    def test_valid_user_data(
        self,
        serializer_context,
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

        assert serializer.is_valid(), serializer.errors

        assert serializer.validated_data["object_id"] == test_user_2.id
        assert serializer.validated_data["content_type"] == "user"
        assert serializer.validated_data["post_owner"] == test_user_2.username

    def test_user_is_not_a_serializer_input_field(self):
        serializer = ReportSerializer()

        assert "user" not in serializer.fields

    @pytest.mark.parametrize(
        "content_type",
        ["invalid", "post123", "POST", "User", ""],
    )
    def test_invalid_content_type(
        self,
        serializer_context,
        test_message,
        general_problem,
        content_type,
    ):
        serializer = ReportSerializer(
            data={
                "object_id": test_message.id,
                "general_report": general_problem.id,
                "post_owner": "testuser",
                "content_type": content_type,
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is False
        assert "content_type" in serializer.errors

    def test_missing_content_type(
        self,
        serializer_context,
        test_message,
        general_problem,
    ):
        serializer = ReportSerializer(
            data={
                "object_id": test_message.id,
                "general_report": general_problem.id,
                "post_owner": "testuser",
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is False
        assert "content_type" in serializer.errors

    def test_missing_post_owner(
        self,
        serializer_context,
        test_message,
        general_problem,
    ):
        serializer = ReportSerializer(
            data={
                "object_id": test_message.id,
                "general_report": general_problem.id,
                "content_type": "post",
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is False
        assert "post_owner" in serializer.errors

    def test_missing_object_id(
        self,
        serializer_context,
        general_problem,
        test_user,
    ):
        serializer = ReportSerializer(
            data={
                "general_report": general_problem.id,
                "post_owner": test_user.username,
                "content_type": "post",
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is False
        assert "object_id" in serializer.errors

    def test_nonexistent_post_is_rejected(
        self,
        serializer_context,
        test_user,
        general_problem,
    ):
        serializer = ReportSerializer(
            data={
                "object_id": 999999,
                "general_report": general_problem.id,
                "post_owner": test_user.username,
                "content_type": "post",
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is False
        assert serializer.errors["object_id"] == ["The specified post does not exist."]

    def test_nonexistent_user_is_rejected(
        self,
        serializer_context,
        test_user,
        general_problem,
    ):
        serializer = ReportSerializer(
            data={
                "object_id": 999999,
                "general_report": general_problem.id,
                "post_owner": test_user.username,
                "content_type": "user",
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is False
        assert serializer.errors["object_id"] == ["The specified user does not exist."]

    def test_is_following_returns_true_when_user_follows_post_owner(
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

        report = Report.objects.create(
            user=test_user,
            content_object=test_message,
            general_report=general_problem,
        )

        report.post_owner = test_user_2.username

        serializer = ReportSerializer(
            report,
            context=serializer_context,
        )

        assert serializer.get_is_following(report) is True

    def test_is_following_returns_false_when_user_does_not_follow_post_owner(
        self,
        serializer_context,
        test_user,
        test_user_2,
        test_message,
        general_problem,
    ):
        report = Report.objects.create(
            user=test_user,
            content_object=test_message,
            general_report=general_problem,
        )

        report.post_owner = test_user_2.username

        serializer = ReportSerializer(
            report,
            context=serializer_context,
        )

        assert serializer.get_is_following(report) is False

    def test_is_following_returns_false_for_unknown_post_owner(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        report = Report.objects.create(
            user=test_user,
            content_object=test_message,
            general_report=general_problem,
        )

        report.post_owner = "does-not-exist"

        serializer = ReportSerializer(
            report,
            context=serializer_context,
        )

        assert serializer.get_is_following(report) is False

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

        assert serializer.is_valid(), serializer.errors

        report = serializer.save()

        assert isinstance(report, Report)
        assert report.pk is not None
        assert report.user == test_user
        assert report.content_object == test_message
        assert report.general_report == general_problem
        assert report.post_owner == test_user.username

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

        assert serializer.is_valid(), serializer.errors

        report = serializer.save()

        assert isinstance(report, Report)
        assert report.pk is not None
        assert report.user == test_user
        assert report.content_object == test_user_2
        assert report.general_report == general_problem
        assert report.post_owner == test_user_2.username

    def test_create_uses_authenticated_request_user(
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

        assert serializer.is_valid(), serializer.errors

        report = serializer.save()

        assert report.user == test_user
        assert report.user != test_user_2

    def test_serializer_representation_includes_is_following(
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

        report = Report.objects.create(
            user=test_user,
            content_object=test_message,
            general_report=general_problem,
        )

        report.post_owner = test_user_2.username

        serializer = ReportSerializer(
            report,
            context=serializer_context,
        )

        assert serializer.data["is_following"] is True

    def test_post_owner_is_available_after_create(
        self,
        serializer_context,
        test_user,
        test_message,
        general_problem,
    ):
        serializer = ReportSerializer(
            data={
                "object_id": test_message.id,
                "general_report": general_problem.id,
                "post_owner": test_user.username,
                "content_type": "post",
            },
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        report = serializer.save()

        assert report.post_owner == test_user.username


@pytest.mark.django_db
class TestReportProblemSerializer:
    def test_meta_model(self):
        assert ReportProblemSerializer.Meta.model is ReportProblem

    def test_meta_fields(self):
        assert ReportProblemSerializer.Meta.fields == [
            "user",
            "report",
        ]

    def test_user_is_read_only(self):
        serializer = ReportProblemSerializer()

        assert serializer.fields["user"].read_only is True

    def test_report_is_required(self):
        serializer = ReportProblemSerializer(data={})

        assert serializer.is_valid() is False
        assert "report" in serializer.errors

    def test_valid_report_is_accepted(
        self,
        serializer_context,
        test_report,
    ):
        serializer = ReportProblemSerializer(
            data={"report": test_report.id},
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

    def test_user_is_not_required_from_client(
        self,
        serializer_context,
        test_report,
    ):
        serializer = ReportProblemSerializer(
            data={"report": test_report.id},
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors
        assert "user" not in serializer.validated_data

    def test_submitted_user_is_not_accepted_as_writable_field(
        self,
        serializer_context,
        test_report,
        test_user_2,
    ):
        serializer = ReportProblemSerializer(
            data={
                "user": test_user_2.id,
                "report": test_report.id,
            },
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors
        assert "user" not in serializer.validated_data

    def test_save_sets_request_user(
        self,
        serializer_context,
        test_report,
    ):
        serializer = ReportProblemSerializer(
            data={"report": str(test_report.pk)},
            context=serializer_context,
        )

        assert serializer.is_valid() is True

        report_problem = serializer.save()

        assert report_problem.user == serializer_context["request"].user
        assert report_problem.report == str(test_report.pk)

    def test_save_ignores_submitted_user(
        self,
        serializer_context,
        test_user,
        test_user_2,
        test_report,
    ):
        serializer = ReportProblemSerializer(
            data={
                "user": test_user_2.id,
                "report": test_report.id,
            },
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        report_problem = serializer.save()

        assert report_problem.user == test_user
        assert report_problem.user != test_user_2
