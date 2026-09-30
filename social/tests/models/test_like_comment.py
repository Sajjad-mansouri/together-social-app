import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models
from django.utils import timezone

from social.models import Comment, LikeComment, LikeSaveAbstract, Message


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
def test_comment(test_user, test_message):
    content_type = ContentType.objects.get_for_model(Message)

    return Comment.objects.create(
        author=test_user,
        comment="Test comment",
        content_type=content_type,
        object_id=test_message.pk,
    )


@pytest.fixture
def test_comment_2(test_user, test_message_2):
    content_type = ContentType.objects.get_for_model(Message)

    return Comment.objects.create(
        author=test_user,
        comment="Second test comment",
        content_type=content_type,
        object_id=test_message_2.pk,
    )


@pytest.fixture
def test_like_comment(test_user, test_comment):
    return LikeComment.objects.create(
        user=test_user,
        comment=test_comment,
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

    def test_like_comment_inherits_user_field(self):
        field = LikeComment._meta.get_field("user")

        assert isinstance(field, models.ForeignKey)
        assert field.name == "user"

    def test_like_comment_inherits_created_field(self):
        field = LikeComment._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)
        assert field.auto_now_add is True


class TestLikeComment:
    def test_like_comment_can_be_created(
        self,
        test_user,
        test_comment,
    ):
        like_comment = LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )

        assert like_comment.pk is not None
        assert like_comment.user == test_user
        assert like_comment.comment == test_comment

    def test_user_relationship(
        self,
        test_like_comment,
        test_user,
    ):
        assert test_like_comment.user == test_user
        assert test_like_comment.user_id == test_user.pk

    def test_comment_relationship(
        self,
        test_like_comment,
        test_comment,
    ):
        assert test_like_comment.comment == test_comment
        assert test_like_comment.comment_id == test_comment.pk

    def test_comment_field_is_foreign_key(self):
        field = LikeComment._meta.get_field("comment")

        assert isinstance(field, models.ForeignKey)

    def test_comment_field_points_to_comment(self):
        field = LikeComment._meta.get_field("comment")

        assert field.remote_field.model is Comment

    def test_comment_field_uses_cascade_delete(self):
        field = LikeComment._meta.get_field("comment")

        assert field.remote_field.on_delete is models.CASCADE

    def test_user_field_uses_cascade_delete(self):
        field = LikeComment._meta.get_field("user")

        assert field.remote_field.on_delete is models.CASCADE

    def test_created_is_set_automatically(
        self,
        test_user,
        test_comment,
    ):
        before = timezone.now()

        like_comment = LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )

        after = timezone.now()

        assert before <= like_comment.created <= after

    def test_created_is_not_changed_on_update(
        self,
        test_like_comment,
    ):
        original_created = test_like_comment.created

        test_like_comment.save()
        test_like_comment.refresh_from_db()

        assert test_like_comment.created == original_created

    def test_same_user_cannot_like_same_comment(
        self,
        test_like_comment,
    ):
        with pytest.raises(IntegrityError):
            LikeComment.objects.create(
                user=test_like_comment.user,
                comment=test_like_comment.comment,
            )

    def test_same_user_can_like_different_comments(
        self,
        test_user,
        test_comment,
        test_comment_2,
    ):
        first_like = LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )
        second_like = LikeComment.objects.create(
            user=test_user,
            comment=test_comment_2,
        )

        assert first_like.pk != second_like.pk
        assert first_like.comment == test_comment
        assert second_like.comment == test_comment_2

    def test_different_users_can_like_same_comment(
        self,
        test_user,
        test_user_2,
        test_comment,
    ):
        first_like = LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )
        second_like = LikeComment.objects.create(
            user=test_user_2,
            comment=test_comment,
        )

        assert first_like.pk != second_like.pk
        assert first_like.comment == second_like.comment
        assert first_like.user != second_like.user

    def test_deleting_comment_deletes_like_comment(
        self,
        test_like_comment,
        test_comment,
    ):
        like_comment_id = test_like_comment.pk

        test_comment.delete()

        assert not LikeComment.objects.filter(
            pk=like_comment_id,
        ).exists()

    def test_deleting_user_deletes_like_comment(
        self,
        test_like_comment,
        test_user,
    ):
        like_comment_id = test_like_comment.pk

        test_user.delete()

        assert not LikeComment.objects.filter(
            pk=like_comment_id,
        ).exists()

    def test_queryset_contains_created_instance(
        self,
        test_like_comment,
    ):
        assert LikeComment.objects.filter(
            pk=test_like_comment.pk,
        ).exists()

    def test_meta_unique_together_contains_user_and_comment(self):
        assert ("user", "comment") in LikeComment._meta.unique_together

    def test_meta_unique_together_is_exactly_user_and_comment(self):
        assert LikeComment._meta.unique_together == (("user", "comment"),)
