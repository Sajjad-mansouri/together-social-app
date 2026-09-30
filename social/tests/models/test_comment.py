import pytest
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, models
from django.utils import timezone

from social.models import Comment, LikeComment, Message


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
def message_content_type(db):
    return ContentType.objects.get_for_model(Message)


@pytest.fixture
def test_comment(
    test_user,
    test_message,
    message_content_type,
):
    return Comment.objects.create(
        author=test_user,
        comment="Test comment",
        content_type=message_content_type,
        object_id=test_message.pk,
    )


@pytest.fixture
def test_comment_2(
    test_user,
    test_message_2,
    message_content_type,
):
    return Comment.objects.create(
        author=test_user,
        comment="Second test comment",
        content_type=message_content_type,
        object_id=test_message_2.pk,
    )


@pytest.fixture
def test_reply(
    test_user_2,
    test_comment,
    message_content_type,
    test_message,
):
    return Comment.objects.create(
        author=test_user_2,
        parent=test_comment,
        main_comment=test_comment,
        comment="Test reply",
        content_type=message_content_type,
        object_id=test_message.pk,
    )


@pytest.fixture
def test_like_comment(test_user_2, test_comment):
    return LikeComment.objects.create(
        user=test_user_2,
        comment=test_comment,
    )


class TestComment:
    def test_comment_can_be_created(
        self,
        test_user,
        test_message,
        message_content_type,
    ):
        comment = Comment.objects.create(
            author=test_user,
            comment="Test comment",
            content_type=message_content_type,
            object_id=test_message.pk,
        )

        assert comment.pk is not None
        assert comment.author == test_user
        assert comment.comment == "Test comment"
        assert comment.content_type == message_content_type
        assert comment.object_id == test_message.pk

    def test_author_relationship(
        self,
        test_comment,
        test_user,
    ):
        assert test_comment.author == test_user
        assert test_comment.author_id == test_user.pk

    def test_author_field_is_foreign_key(self):
        field = Comment._meta.get_field("author")

        assert isinstance(field, models.ForeignKey)

    def test_author_field_points_to_user_model(
        self,
        django_user_model,
    ):
        field = Comment._meta.get_field("author")

        assert field.remote_field.model is django_user_model

    def test_author_field_uses_cascade_delete(self):
        field = Comment._meta.get_field("author")

        assert field.remote_field.on_delete is models.CASCADE

    def test_author_field_related_name(self):
        field = Comment._meta.get_field("author")

        assert field.remote_field.related_name == "author_comments"

    def test_author_reverse_relation(
        self,
        test_user,
        test_comment,
    ):
        assert test_comment in test_user.author_comments.all()

    def test_parent_is_nullable(self):
        field = Comment._meta.get_field("parent")

        assert field.null is True
        assert field.blank is True

    def test_parent_field_is_self_referential_foreign_key(self):
        field = Comment._meta.get_field("parent")

        assert isinstance(field, models.ForeignKey)
        assert field.remote_field.model is Comment

    def test_parent_field_uses_cascade_delete(self):
        field = Comment._meta.get_field("parent")

        assert field.remote_field.on_delete is models.CASCADE

    def test_parent_field_related_name(self):
        field = Comment._meta.get_field("parent")

        assert field.remote_field.related_name == "comments"

    def test_comment_can_have_parent(
        self,
        test_reply,
        test_comment,
    ):
        assert test_reply.parent == test_comment
        assert test_reply.parent_id == test_comment.pk

    def test_parent_reverse_relation(
        self,
        test_comment,
        test_reply,
    ):
        assert test_reply in test_comment.comments.all()

    def test_comment_can_have_no_parent(self, test_comment):
        assert test_comment.parent is None
        assert test_comment.parent_id is None

    def test_main_comment_is_nullable(self):
        field = Comment._meta.get_field("main_comment")

        assert field.null is True
        assert field.blank is True

    def test_main_comment_field_is_self_referential_foreign_key(self):
        field = Comment._meta.get_field("main_comment")

        assert isinstance(field, models.ForeignKey)
        assert field.remote_field.model is Comment

    def test_main_comment_field_uses_cascade_delete(self):
        field = Comment._meta.get_field("main_comment")

        assert field.remote_field.on_delete is models.CASCADE

    def test_main_comment_field_related_name(self):
        field = Comment._meta.get_field("main_comment")

        assert field.remote_field.related_name == "main_comments"

    def test_comment_can_have_main_comment(
        self,
        test_reply,
        test_comment,
    ):
        assert test_reply.main_comment == test_comment
        assert test_reply.main_comment_id == test_comment.pk

    def test_main_comment_reverse_relation(
        self,
        test_comment,
        test_reply,
    ):
        assert test_reply in test_comment.main_comments.all()

    def test_comment_can_have_no_main_comment(self, test_comment):
        assert test_comment.main_comment is None
        assert test_comment.main_comment_id is None

    def test_comment_field_is_text_field(self):
        field = Comment._meta.get_field("comment")

        assert isinstance(field, models.TextField)

    def test_comment_field_is_required(self):
        field = Comment._meta.get_field("comment")

        assert field.null is False
        assert field.blank is False

    def test_created_field_is_datetime_field(self):
        field = Comment._meta.get_field("created")

        assert isinstance(field, models.DateTimeField)

    def test_created_field_uses_auto_now_add(self):
        field = Comment._meta.get_field("created")

        assert field.auto_now_add is True

    def test_created_is_set_automatically(
        self,
        test_user,
        test_message,
        message_content_type,
    ):
        before = timezone.now()

        comment = Comment.objects.create(
            author=test_user,
            comment="Test comment",
            content_type=message_content_type,
            object_id=test_message.pk,
        )

        after = timezone.now()

        assert before <= comment.created <= after

    def test_created_is_not_changed_on_update(self, test_comment):
        original_created = test_comment.created

        test_comment.comment = "Updated comment"
        test_comment.save()
        test_comment.refresh_from_db()

        assert test_comment.created == original_created

    def test_content_type_field_is_foreign_key(self):
        field = Comment._meta.get_field("content_type")

        assert isinstance(field, models.ForeignKey)

    def test_content_type_points_to_content_type_model(self):
        field = Comment._meta.get_field("content_type")

        assert field.remote_field.model is ContentType

    def test_content_type_uses_cascade_delete(self):
        field = Comment._meta.get_field("content_type")

        assert field.remote_field.on_delete is models.CASCADE

    def test_content_type_limit_choices_to(self):
        field = Comment._meta.get_field("content_type")

        assert field.remote_field.limit_choices_to == models.Q(
            app_label="social",
            model="message",
        )

    def test_content_type_is_message_content_type(
        self,
        test_comment,
        test_message,
    ):
        expected_content_type = ContentType.objects.get_for_model(
            test_message,
        )

        assert test_comment.content_type == expected_content_type

    def test_object_id_field_is_positive_integer_field(self):
        field = Comment._meta.get_field("object_id")

        assert isinstance(field, models.PositiveIntegerField)

    def test_object_id_contains_message_primary_key(
        self,
        test_comment,
        test_message,
    ):
        assert test_comment.object_id == test_message.pk

    def test_content_object_is_generic_foreign_key(self):
        field = Comment._meta.get_field("content_object")

        assert isinstance(field, GenericForeignKey)

    def test_content_object_resolves_to_message(
        self,
        test_comment,
        test_message,
    ):
        assert test_comment.content_object == test_message

    def test_setting_content_object_updates_generic_relation(
        self,
        test_comment,
        test_message_2,
    ):
        test_comment.content_object = test_message_2
        test_comment.save()
        test_comment.refresh_from_db()

        assert test_comment.content_object == test_message_2
        assert test_comment.object_id == test_message_2.pk
        assert test_comment.content_type == ContentType.objects.get_for_model(Message)

    def test_like_field_is_many_to_many(self):
        field = Comment._meta.get_field("like")

        assert isinstance(field, models.ManyToManyField)

    def test_like_field_uses_like_comment_as_through_model(self):
        field = Comment._meta.get_field("like")

        assert field.remote_field.through is LikeComment

    def test_like_field_points_to_user_model(
        self,
        django_user_model,
    ):
        field = Comment._meta.get_field("like")

        assert field.remote_field.model is django_user_model

    def test_user_can_like_comment(
        self,
        test_comment,
        test_user_2,
        test_like_comment,
    ):
        assert test_user_2 in test_comment.like.all()

    def test_multiple_users_can_like_same_comment(
        self,
        test_comment,
        test_user,
        test_user_2,
    ):
        LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )
        LikeComment.objects.create(
            user=test_user_2,
            comment=test_comment,
        )

        assert test_comment.like.count() == 2
        assert test_user in test_comment.like.all()
        assert test_user_2 in test_comment.like.all()

    def test_user_cannot_like_same_comment_twice(
        self,
        test_comment,
        test_user,
    ):
        LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )

        with pytest.raises(IntegrityError):
            LikeComment.objects.create(
                user=test_user,
                comment=test_comment,
            )

    def test_deleting_author_deletes_comments(
        self,
        test_comment,
        test_user,
    ):
        comment_id = test_comment.pk

        test_user.delete()

        assert not Comment.objects.filter(pk=comment_id).exists()

    def test_deleting_parent_deletes_child_comment(
        self,
        test_comment,
        test_reply,
    ):
        reply_id = test_reply.pk

        test_comment.delete()

        assert not Comment.objects.filter(pk=reply_id).exists()

    def test_deleting_main_comment_deletes_child_comment(
        self,
        test_comment,
        test_reply,
    ):
        reply_id = test_reply.pk

        test_comment.delete()

        assert not Comment.objects.filter(pk=reply_id).exists()

    def test_deleting_content_type_deletes_comments(
        self,
        test_comment,
        message_content_type,
    ):
        comment_id = test_comment.pk

        message_content_type.delete()

        assert not Comment.objects.filter(pk=comment_id).exists()

    def test_meta_has_content_type_object_id_index(self):
        indexes = Comment._meta.indexes

        assert any(index.fields == ["content_type", "object_id"] for index in indexes)
