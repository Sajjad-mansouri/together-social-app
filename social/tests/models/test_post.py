from datetime import timedelta

import pytest
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from social.models import Message, custom_upload


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


class TestMessage:
    def test_message_can_be_created(self, test_user):
        message = Message.objects.create(
            user=test_user,
            text="Test message",
        )

        assert message.pk is not None
        assert message.user == test_user
        assert message.text == "Test message"

    def test_user_relationship(self, test_message, test_user):
        assert test_message.user == test_user
        assert test_message.user_id == test_user.pk

    def test_user_related_name_messages(self, test_message, test_user):
        assert test_message in test_user.messages.all()

    def test_text_field_is_text_field(self):
        field = Message._meta.get_field("text")

        assert isinstance(field, models.TextField)

    def test_text_field_is_required(self):
        field = Message._meta.get_field("text")

        assert field.null is False
        assert field.blank is False

    def test_image_field_is_image_field(self):
        field = Message._meta.get_field("image")

        assert isinstance(field, models.ImageField)

    def test_image_field_is_required(self):
        field = Message._meta.get_field("image")

        assert field.null is False
        assert field.blank is False

    def test_created_field_configuration(self):
        field = Message._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)
        assert field.auto_now_add is True

    def test_updated_field_configuration(self):
        field = Message._meta.get_field("updated")

        assert isinstance(field, models.DateTimeField)
        assert field.auto_now is True

    def test_created_is_set_when_message_is_created(self, test_user):
        before = timezone.now()

        message = Message.objects.create(
            user=test_user,
            text="Test message",
        )

        after = timezone.now()

        assert before <= message.created <= after

    def test_updated_is_set_when_message_is_created(self, test_user):
        before = timezone.now()

        message = Message.objects.create(
            user=test_user,
            text="Test message",
        )

        after = timezone.now()

        assert before <= message.updated <= after

    def test_updated_changes_when_message_is_saved(
        self,
        test_message,
    ):
        original_updated = test_message.updated

        test_message.text = "Updated message"
        test_message.save()

        test_message.refresh_from_db()

        assert test_message.updated > original_updated

    def test_created_does_not_change_when_message_is_updated(
        self,
        test_message,
    ):
        original_created = test_message.created

        test_message.text = "Updated message"
        test_message.save()

        test_message.refresh_from_db()

        assert test_message.created == original_created

    def test_created_and_updated_are_close_on_initial_creation(
        self,
        test_message,
    ):
        difference = abs(test_message.updated - test_message.created)

        assert difference < timedelta(seconds=1)

    def test_custom_upload_returns_expected_path(self, test_user):
        message = Message(
            user=test_user,
            text="Test message",
        )

        filename = "photo.jpg"

        path = custom_upload(message, filename)

        current_year = timezone.now().year
        current_month = timezone.now().month

        assert path == (f"uploads/{test_user.username}/{current_year}/{current_month}")

    def test_image_field_uses_custom_upload_function(self):
        field = Message._meta.get_field("image")

        assert field.upload_to is custom_upload

    def test_str_returns_message_id(self, test_message):
        assert str(test_message) == str(test_message.id)

    def test_str_returns_string_for_unsaved_message(self, test_user):
        message = Message(
            user=test_user,
            text="Test message",
        )

        assert str(message) == "None"

    def test_like_field_is_many_to_many(self):
        field = Message._meta.get_field("like")

        assert isinstance(field, models.ManyToManyField)
        assert field.remote_field.through.__name__ == "Like"

    def test_saved_post_field_is_many_to_many(self):
        field = Message._meta.get_field("saved_post")

        assert isinstance(field, models.ManyToManyField)
        assert field.remote_field.through.__name__ == "SavePost"

    def test_saved_post_has_save_messages_related_name(self):
        field = Message._meta.get_field("saved_post")

        assert field.remote_field.related_name == "save_messages"

    def test_comment_is_generic_relation(self):
        field = Message._meta.get_field("comment")

        assert isinstance(field, GenericRelation)

    def test_reports_is_generic_relation(self):
        field = Message._meta.get_field("reports")

        assert isinstance(field, GenericRelation)

    def test_reports_has_related_query_name(self):
        field = Message._meta.get_field("reports")

        assert field.related_query_name() == "reports"

    def test_meta_ordering_is_by_created_descending(self):
        assert Message._meta.ordering == ["-created"]

    def test_messages_are_ordered_by_newest_first(self, test_user):
        first_message = Message.objects.create(
            user=test_user,
            text="First message",
        )
        second_message = Message.objects.create(
            user=test_user,
            text="Second message",
        )

        messages = list(Message.objects.all())

        assert messages == [second_message, first_message]

    def test_messages_from_different_users_are_ordered_by_created(
        self,
        test_user,
        test_user_2,
    ):
        first_message = Message.objects.create(
            user=test_user,
            text="First message",
        )
        second_message = Message.objects.create(
            user=test_user_2,
            text="Second message",
        )

        messages = list(Message.objects.all())

        assert messages == [second_message, first_message]
