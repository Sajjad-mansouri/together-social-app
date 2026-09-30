from datetime import timedelta

import pytest
from django.db import IntegrityError, models
from django.utils import timezone

from social.models import LikeSaveAbstract, Message, SavePost


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
def test_message_2(test_user):
    return Message.objects.create(
        user=test_user,
        text="Second test message",
    )


@pytest.fixture
def test_save_post(test_user, test_message):
    return SavePost.objects.create(
        user=test_user,
        post=test_message,
    )


class TestLikeSaveAbstract:
    def test_model_is_abstract(self):
        assert LikeSaveAbstract._meta.abstract is True

    def test_user_field_configuration(self):
        field = LikeSaveAbstract._meta.get_field("user")

        assert isinstance(field, models.ForeignKey)
        assert field.remote_field.model is not None
        assert field.remote_field.on_delete is models.CASCADE

    def test_created_field_configuration(self):
        field = LikeSaveAbstract._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)
        assert field.auto_now_add is True

    def test_save_post_inherits_user_field(self):
        field = SavePost._meta.get_field("user")

        assert isinstance(field, models.ForeignKey)
        assert field.name == "user"

    def test_save_post_inherits_created_field(self):
        field = SavePost._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)
        assert field.auto_now_add is True


class TestSavePost:
    def test_save_post_can_be_created(
        self,
        test_user,
        test_message,
    ):
        save_post = SavePost.objects.create(
            user=test_user,
            post=test_message,
        )

        assert save_post.pk is not None
        assert save_post.user == test_user
        assert save_post.post == test_message

    def test_user_relationship(
        self,
        test_save_post,
        test_user,
    ):
        assert test_save_post.user == test_user
        assert test_save_post.user_id == test_user.pk

    def test_post_relationship(
        self,
        test_save_post,
        test_message,
    ):
        assert test_save_post.post == test_message
        assert test_save_post.post_id == test_message.pk

    def test_post_related_name(
        self,
        test_save_post,
        test_message,
    ):
        assert test_save_post in test_message.saved_posts.all()

    def test_created_is_set_automatically(
        self,
        test_user,
        test_message,
    ):
        before = timezone.now()

        save_post = SavePost.objects.create(
            user=test_user,
            post=test_message,
        )

        after = timezone.now()

        assert before <= save_post.created <= after

    def test_created_is_not_changed_on_update(
        self,
        test_save_post,
    ):
        original_created = test_save_post.created

        test_save_post.save()

        test_save_post.refresh_from_db()

        assert test_save_post.created == original_created

    def test_created_is_close_to_current_time(
        self,
        test_save_post,
    ):
        difference = abs(timezone.now() - test_save_post.created)

        assert difference < timedelta(seconds=1)

    def test_post_field_is_foreign_key(self):
        field = SavePost._meta.get_field("post")

        assert isinstance(field, models.ForeignKey)

    def test_post_field_points_to_message(self):
        field = SavePost._meta.get_field("post")

        assert field.remote_field.model is Message

    def test_post_field_uses_cascade_delete(self):
        field = SavePost._meta.get_field("post")

        assert field.remote_field.on_delete is models.CASCADE

    def test_post_field_related_name(self):
        field = SavePost._meta.get_field("post")

        assert field.remote_field.related_name == "saved_posts"

    def test_user_field_uses_cascade_delete(self):
        field = SavePost._meta.get_field("user")

        assert field.remote_field.on_delete is models.CASCADE

    def test_unique_together_contains_user_and_post(self):
        assert ("user", "post") in SavePost._meta.unique_together

    def test_same_user_cannot_save_same_post_twice(
        self,
        test_save_post,
    ):
        with pytest.raises(IntegrityError):
            SavePost.objects.create(
                user=test_save_post.user,
                post=test_save_post.post,
            )

    def test_same_user_can_save_different_posts(
        self,
        test_user,
        test_message,
        test_message_2,
    ):
        first_save = SavePost.objects.create(
            user=test_user,
            post=test_message,
        )
        second_save = SavePost.objects.create(
            user=test_user,
            post=test_message_2,
        )

        assert first_save.pk != second_save.pk
        assert first_save.post == test_message
        assert second_save.post == test_message_2

    def test_different_users_can_save_same_post(
        self,
        test_user,
        test_user_2,
        test_message,
    ):
        first_save = SavePost.objects.create(
            user=test_user,
            post=test_message,
        )
        second_save = SavePost.objects.create(
            user=test_user_2,
            post=test_message,
        )

        assert first_save.pk != second_save.pk
        assert first_save.post == second_save.post
        assert first_save.user != second_save.user

    def test_deleting_post_deletes_save_post(
        self,
        test_save_post,
        test_message,
    ):
        save_post_id = test_save_post.pk

        test_message.delete()

        assert not SavePost.objects.filter(pk=save_post_id).exists()

    def test_deleting_user_deletes_save_post(
        self,
        test_save_post,
        test_user,
    ):
        save_post_id = test_save_post.pk

        test_user.delete()

        assert not SavePost.objects.filter(pk=save_post_id).exists()

    def test_save_post_count_for_message(
        self,
        test_user,
        test_user_2,
        test_message,
    ):
        SavePost.objects.create(
            user=test_user,
            post=test_message,
        )
        SavePost.objects.create(
            user=test_user_2,
            post=test_message,
        )

        assert test_message.saved_posts.count() == 2

    def test_save_post_queryset_contains_created_instance(
        self,
        test_save_post,
    ):
        assert SavePost.objects.filter(
            pk=test_save_post.pk,
        ).exists()

    def test_meta_unique_together_is_exactly_user_and_post(self):
        assert SavePost._meta.unique_together == (("user", "post"),)
