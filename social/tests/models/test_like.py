import pytest
from django.db import IntegrityError, models
from django.utils import timezone

from social.models import Like, LikeSaveAbstract, Message


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
def test_like(test_user, test_message):
    return Like.objects.create(
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

    def test_like_inherits_user_field(self):
        field = Like._meta.get_field("user")

        assert isinstance(field, models.ForeignKey)
        assert field.name == "user"

    def test_like_inherits_created_field(self):
        field = Like._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)
        assert field.auto_now_add is True


class TestLike:
    def test_like_can_be_created(self, test_user, test_message):
        like = Like.objects.create(
            user=test_user,
            post=test_message,
        )

        assert like.pk is not None
        assert like.user == test_user
        assert like.post == test_message

    def test_user_relationship(self, test_like, test_user):
        assert test_like.user == test_user
        assert test_like.user_id == test_user.pk

    def test_post_relationship(self, test_like, test_message):
        assert test_like.post == test_message
        assert test_like.post_id == test_message.pk

    def test_post_related_name(self, test_like, test_message):
        assert test_like in test_message.likes.all()

    def test_created_is_set_automatically(self, test_user, test_message):
        before = timezone.now()

        like = Like.objects.create(
            user=test_user,
            post=test_message,
        )

        after = timezone.now()

        assert before <= like.created <= after

    def test_created_is_not_changed_on_update(self, test_like):
        original_created = test_like.created

        test_like.save()
        test_like.refresh_from_db()

        assert test_like.created == original_created

    def test_post_field_is_foreign_key(self):
        field = Like._meta.get_field("post")

        assert isinstance(field, models.ForeignKey)

    def test_post_field_points_to_message(self):
        field = Like._meta.get_field("post")

        assert field.remote_field.model is Message

    def test_post_field_uses_cascade_delete(self):
        field = Like._meta.get_field("post")

        assert field.remote_field.on_delete is models.CASCADE

    def test_post_field_related_name(self):
        field = Like._meta.get_field("post")

        assert field.remote_field.related_name == "likes"

    def test_user_field_uses_cascade_delete(self):
        field = Like._meta.get_field("user")

        assert field.remote_field.on_delete is models.CASCADE

    def test_unique_together_contains_user_and_post(self):
        assert ("user", "post") in Like._meta.unique_together

    def test_same_user_cannot_like_same_post(self, test_like):
        with pytest.raises(IntegrityError):
            Like.objects.create(
                user=test_like.user,
                post=test_like.post,
            )

    def test_same_user_can_like_different_posts(
        self,
        test_user,
        test_message,
        test_message_2,
    ):
        first_like = Like.objects.create(
            user=test_user,
            post=test_message,
        )
        second_like = Like.objects.create(
            user=test_user,
            post=test_message_2,
        )

        assert first_like.pk != second_like.pk
        assert first_like.post == test_message
        assert second_like.post == test_message_2

    def test_different_users_can_like_same_post(
        self,
        test_user,
        test_user_2,
        test_message,
    ):
        first_like = Like.objects.create(
            user=test_user,
            post=test_message,
        )
        second_like = Like.objects.create(
            user=test_user_2,
            post=test_message,
        )

        assert first_like.pk != second_like.pk
        assert first_like.post == second_like.post
        assert first_like.user != second_like.user

    def test_post_can_have_multiple_likes(
        self,
        test_user,
        test_user_2,
        test_message,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )
        Like.objects.create(
            user=test_user_2,
            post=test_message,
        )

        assert test_message.likes.count() == 2

    def test_deleting_post_deletes_like(
        self,
        test_like,
        test_message,
    ):
        like_id = test_like.pk

        test_message.delete()

        assert not Like.objects.filter(pk=like_id).exists()

    def test_deleting_user_deletes_like(
        self,
        test_like,
        test_user,
    ):
        like_id = test_like.pk

        test_user.delete()

        assert not Like.objects.filter(pk=like_id).exists()

    def test_like_queryset_contains_created_instance(self, test_like):
        assert Like.objects.filter(pk=test_like.pk).exists()

    def test_meta_unique_together_is_exactly_user_and_post(self):
        assert Like._meta.unique_together == (("user", "post"),)
