import pytest
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from social.models import GeneralProblem, Message, Report


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
def test_message(test_user):
    return Message.objects.create(
        user=test_user,
        text="Test message",
    )


@pytest.fixture
def test_general_report(db):
    return GeneralProblem.objects.create(
        title="Test general problem",
    )


@pytest.fixture
def message_content_type(db):
    return ContentType.objects.get_for_model(Message)


@pytest.fixture
def user_content_type(db, django_user_model):
    return ContentType.objects.get_for_model(django_user_model)


@pytest.fixture
def test_report(
    test_user,
    test_message,
    message_content_type,
    test_general_report,
):
    return Report.objects.create(
        user=test_user,
        content_type=message_content_type,
        object_id=test_message.pk,
        general_report=test_general_report,
    )


@pytest.mark.django_db
class TestReport:
    def test_report_can_be_created(
        self,
        test_user,
        test_message,
        message_content_type,
    ):
        report = Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
        )

        assert report.pk is not None
        assert report.user == test_user
        assert report.content_type == message_content_type
        assert report.object_id == test_message.pk

    def test_user_field_is_foreign_key(self):
        field = Report._meta.get_field("user")

        assert isinstance(field, models.ForeignKey)

    def test_user_field_points_to_user_model(
        self,
        django_user_model,
    ):
        field = Report._meta.get_field("user")

        assert field.remote_field.model is django_user_model

    def test_user_field_uses_cascade_delete(self):
        field = Report._meta.get_field("user")

        assert field.remote_field.on_delete is models.CASCADE

    def test_user_relationship(self, test_report, test_user):
        assert test_report.user == test_user
        assert test_report.user_id == test_user.pk

    def test_content_type_field_is_foreign_key(self):
        field = Report._meta.get_field("content_type")

        assert isinstance(field, models.ForeignKey)

    def test_content_type_points_to_content_type_model(self):
        field = Report._meta.get_field("content_type")

        assert field.remote_field.model is ContentType

    def test_content_type_uses_cascade_delete(self):
        field = Report._meta.get_field("content_type")

        assert field.remote_field.on_delete is models.CASCADE

    def test_content_type_limit_choices_to(self):
        field = Report._meta.get_field("content_type")

        expected_limit = models.Q(app_label="account", model="myuser") | models.Q(
            app_label="social", model="message"
        )

        assert field.remote_field.limit_choices_to == expected_limit

    def test_message_content_type_is_allowed(
        self,
        message_content_type,
    ):
        field = Report._meta.get_field("content_type")
        limit = field.remote_field.limit_choices_to

        assert limit.check(
            {
                "app_label": message_content_type.app_label,
                "model": message_content_type.model,
            }
        )

    def test_user_content_type_is_allowed(
        self,
        user_content_type,
    ):
        field = Report._meta.get_field("content_type")
        limit = field.remote_field.limit_choices_to

        assert limit.check(
            {
                "app_label": user_content_type.app_label,
                "model": user_content_type.model,
            }
        )

    def test_object_id_field_is_positive_integer_field(self):
        field = Report._meta.get_field("object_id")

        assert isinstance(field, models.PositiveIntegerField)

    def test_object_id_contains_target_primary_key(
        self,
        test_report,
        test_message,
    ):
        assert test_report.object_id == test_message.pk

    def test_content_object_is_generic_foreign_key(self):
        field = Report._meta.get_field("content_object")

        assert isinstance(field, GenericForeignKey)

    def test_content_object_resolves_to_message(
        self,
        test_report,
        test_message,
    ):
        assert test_report.content_object == test_message

    def test_setting_content_object_updates_generic_relation(
        self,
        test_report,
        test_user_2,
    ):
        test_report.content_object = test_user_2
        test_report.save()
        test_report.refresh_from_db()

        expected_content_type = ContentType.objects.get_for_model(
            test_user_2,
        )

        assert test_report.content_object == test_user_2
        assert test_report.object_id == test_user_2.pk
        assert test_report.content_type == expected_content_type

    def test_general_report_field_is_foreign_key(self):
        field = Report._meta.get_field("general_report")

        assert isinstance(field, models.ForeignKey)

    def test_general_report_points_to_general_problem(self):
        field = Report._meta.get_field("general_report")

        assert field.remote_field.model is GeneralProblem

    def test_general_report_uses_cascade_delete(self):
        field = Report._meta.get_field("general_report")

        assert field.remote_field.on_delete is models.CASCADE

    def test_general_report_is_nullable(self):
        field = Report._meta.get_field("general_report")

        assert field.null is True
        assert field.blank is False

    def test_report_can_be_created_without_general_report(
        self,
        test_user,
        test_message,
        message_content_type,
    ):
        report = Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
        )

        assert report.general_report is None

    def test_general_report_relationship(
        self,
        test_report,
        test_general_report,
    ):
        assert test_report.general_report == test_general_report
        assert test_report.general_report_id == test_general_report.pk

    def test_account_pretending_field_is_foreign_key(self):
        field = Report._meta.get_field("account_pretending")

        assert isinstance(field, models.ForeignKey)

    def test_account_pretending_points_to_user_model(
        self,
        django_user_model,
    ):
        field = Report._meta.get_field("account_pretending")

        assert field.remote_field.model is django_user_model

    def test_account_pretending_uses_cascade_delete(self):
        field = Report._meta.get_field("account_pretending")

        assert field.remote_field.on_delete is models.CASCADE

    def test_account_pretending_is_nullable(self):
        field = Report._meta.get_field("account_pretending")

        assert field.null is True
        assert field.blank is True

    def test_account_pretending_related_name(self):
        field = Report._meta.get_field("account_pretending")

        assert field.remote_field.related_name == "target_user"

    def test_account_pretending_relationship(
        self,
        test_user,
        test_user_2,
        test_message,
        message_content_type,
    ):
        report = Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
            account_pretending=test_user_2,
        )

        assert report.account_pretending == test_user_2
        assert report.account_pretending_id == test_user_2.pk

    def test_report_can_be_created_without_account_pretending(
        self,
        test_user,
        test_message,
        message_content_type,
    ):
        report = Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
        )

        assert report.account_pretending is None

    def test_account_pretending_reverse_relation(
        self,
        test_user,
        test_user_2,
        test_message,
        message_content_type,
    ):
        report = Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
            account_pretending=test_user_2,
        )

        assert report in test_user_2.target_user.all()

    def test_seen_field_is_boolean_field(self):
        field = Report._meta.get_field("seen")

        assert isinstance(field, models.BooleanField)

    def test_seen_defaults_to_false(self):
        field = Report._meta.get_field("seen")

        assert field.default is False

    def test_seen_is_false_when_report_is_created(
        self,
        test_user,
        test_message,
        message_content_type,
    ):
        report = Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
        )

        assert report.seen is False

    def test_seen_can_be_set_to_true(
        self,
        test_report,
    ):
        test_report.seen = True
        test_report.save()
        test_report.refresh_from_db()

        assert test_report.seen is True

    def test_seen_date_time_is_datetime_field(self):
        field = Report._meta.get_field("seen_date_time")

        assert isinstance(field, models.DateTimeField)

    def test_seen_date_time_is_nullable_and_optional(self):
        field = Report._meta.get_field("seen_date_time")

        assert field.null is True
        assert field.blank is True

    def test_seen_date_time_can_be_none(
        self,
        test_report,
    ):
        assert test_report.seen_date_time is None

    def test_seen_date_time_can_be_set(
        self,
        test_report,
    ):
        seen_date_time = timezone.now()

        test_report.seen = True
        test_report.seen_date_time = seen_date_time
        test_report.save()
        test_report.refresh_from_db()

        assert test_report.seen is True
        assert test_report.seen_date_time == seen_date_time

    def test_created_field_is_datetime_field(self):
        field = Report._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)

    def test_created_uses_auto_now_add(self):
        field = Report._meta.get_field("created")

        assert field.auto_now_add is True

    def test_created_is_set_automatically(
        self,
        test_user,
        test_message,
        message_content_type,
    ):
        before = timezone.now()

        report = Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
        )

        after = timezone.now()

        assert before <= report.created <= after

    def test_created_is_not_changed_on_update(
        self,
        test_report,
    ):
        original_created = test_report.created

        test_report.seen = True
        test_report.save()
        test_report.refresh_from_db()

        assert test_report.created == original_created

    def test_deleting_report_user_deletes_report(
        self,
        test_report,
        test_user,
    ):
        report_id = test_report.pk

        test_user.delete()

        assert not Report.objects.filter(pk=report_id).exists()

    def test_deleting_general_report_deletes_report(
        self,
        test_report,
        test_general_report,
    ):
        report_id = test_report.pk

        test_general_report.delete()

        assert not Report.objects.filter(pk=report_id).exists()

    def test_deleting_account_pretending_user_deletes_report(
        self,
        test_user,
        test_user_2,
        test_message,
        message_content_type,
    ):
        report = Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
            account_pretending=test_user_2,
        )
        report_id = report.pk

        test_user_2.delete()

        assert not Report.objects.filter(pk=report_id).exists()

    def test_deleting_content_type_deletes_report(
        self,
        test_report,
        message_content_type,
    ):
        report_id = test_report.pk

        message_content_type.delete()

        assert not Report.objects.filter(pk=report_id).exists()
