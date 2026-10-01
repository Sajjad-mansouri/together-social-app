import pytest
from django.test import RequestFactory
from django.utils.timesince import timesince
from rest_framework import serializers

from account.models import Profile
from api.serializers import CommentSerializer, LikeCommentSerializer
from social.models import Comment, LikeComment, Message


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
def test_profile(test_user):
    return Profile.objects.create(user=test_user)


@pytest.fixture
def test_profile_2(test_user_2):
    return Profile.objects.create(user=test_user_2)


@pytest.fixture
def test_message(test_user):
    return Message.objects.create(
        user=test_user,
        text="Test message",
    )


@pytest.fixture
def test_comment(test_user, test_message):
    return Comment.objects.create(
        content_object=test_message,
        author=test_user,
        comment="Test comment",
    )


@pytest.fixture
def test_comment_2(test_user_2, test_message):
    return Comment.objects.create(
        content_object=test_message,
        author=test_user_2,
        comment="Second comment",
    )


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def serializer_context(request_factory, test_user):
    request = request_factory.get("/")
    request.user = test_user
    return {"request": request}


class TestCommentSerializer:
    def test_meta_model(self):
        assert CommentSerializer.Meta.model is Comment

    def test_meta_fields(self):
        expected_fields = [
            "id",
            "comment",
            "object_id",
            "author",
            "parent",
            "main_comment",
            "created",
            "is_user_comment",
            "like_info",
        ]

        assert CommentSerializer.Meta.fields == expected_fields

    def test_read_only_fields(self):
        assert CommentSerializer.Meta.read_only_fields == [
            "id",
            "author",
            "created",
            "is_user_comment",
            "like_info",
        ]

    def test_author_is_read_only(self):
        serializer = CommentSerializer()

        assert serializer.fields["author"].read_only is True

    def test_created_is_read_only(self):
        serializer = CommentSerializer()

        assert serializer.fields["created"].read_only is True

    def test_is_user_comment_is_read_only(self):
        serializer = CommentSerializer()

        assert serializer.fields["is_user_comment"].read_only is True

    def test_like_info_is_read_only(self):
        serializer = CommentSerializer()

        assert serializer.fields["like_info"].read_only is True

    def test_serializes_comment(
        self,
        test_comment,
        test_profile,
        serializer_context,
    ):
        serializer = CommentSerializer(
            test_comment,
            context=serializer_context,
        )

        data = serializer.data

        assert data["id"] == test_comment.id
        assert data["comment"] == test_comment.comment
        assert data["object_id"] == test_comment.object_id
        assert data["parent"] is None
        assert data["main_comment"] is None

    def test_serializes_nested_author(
        self,
        test_comment,
        test_profile,
        serializer_context,
    ):
        serializer = CommentSerializer(
            test_comment,
            context=serializer_context,
        )

        author = serializer.data["author"]

        assert author["username"] == test_comment.author.username
        assert set(author) == {"username", "profile"}

    def test_get_created(self, test_comment, serializer_context):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        expected = timesince(test_comment.created).split(",")[0]

        assert serializer.get_created(test_comment) == expected

    def test_created_representation_uses_get_created(
        self,
        test_comment,
        serializer_context,
    ):
        serializer = CommentSerializer(
            test_comment,
            context=serializer_context,
        )

        assert serializer.data["created"] == serializer.get_created(test_comment)

    def test_get_is_user_comment_returns_true_for_request_user(
        self,
        test_comment,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        assert serializer.get_is_user_comment(test_comment) is True

    def test_get_is_user_comment_returns_false_for_different_author(
        self,
        test_comment_2,
        test_profile_2,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        assert serializer.get_is_user_comment(test_comment_2) is False

    def test_is_user_comment_representation(
        self,
        test_comment,
        serializer_context,
    ):
        serializer = CommentSerializer(
            test_comment,
            context=serializer_context,
        )

        assert serializer.data["is_user_comment"] is True

    def test_like_info_returns_no_likes(
        self,
        test_comment,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        result = serializer.get_like_info(test_comment)

        assert result == {
            "is_liked": False,
            "like_count": 0,
        }

    def test_like_info_returns_liked_status_and_like_id(
        self,
        test_comment,
        test_user,
        serializer_context,
    ):
        liked = LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )

        serializer = CommentSerializer(
            context=serializer_context,
        )

        result = serializer.get_like_info(test_comment)

        assert result == {
            "is_liked": True,
            "id": liked.id,
            "like_count": 1,
        }

    def test_like_info_returns_false_for_different_user(
        self,
        test_comment,
        test_user_2,
        test_profile_2,
        serializer_context,
    ):
        LikeComment.objects.create(
            user=test_user_2,
            comment=test_comment,
        )

        serializer = CommentSerializer(
            context=serializer_context,
        )

        result = serializer.get_like_info(test_comment)

        assert result == {
            "is_liked": False,
            "like_count": 1,
        }

    def test_like_info_count_includes_all_likes(
        self,
        test_comment,
        test_user,
        test_user_2,
        test_profile_2,
        serializer_context,
    ):
        LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )
        LikeComment.objects.create(
            user=test_user_2,
            comment=test_comment,
        )

        serializer = CommentSerializer(
            context=serializer_context,
        )

        result = serializer.get_like_info(test_comment)

        assert result["like_count"] == 2
        assert result["is_liked"] is True

    def test_like_info_representation(
        self,
        test_comment,
        serializer_context,
    ):
        serializer = CommentSerializer(
            test_comment,
            context=serializer_context,
        )

        assert serializer.data["like_info"] == {
            "is_liked": False,
            "like_count": 0,
        }

    def test_author_is_not_accepted_from_request_data(
        self,
        test_message,
        test_user,
        test_user_2,
        serializer_context,
    ):
        serializer = CommentSerializer(
            data={
                "comment": "New comment",
                "object_id": test_message.id,
                "author": {"username": test_user_2.username},
            },
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors
        assert "author" not in serializer.validated_data

    def test_author_is_not_required_for_creation(
        self,
        test_message,
        serializer_context,
    ):
        serializer = CommentSerializer(
            data={
                "comment": "New comment",
                "object_id": test_message.id,
            },
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors
        assert "author" not in serializer.validated_data

    def test_create_creates_comment_with_request_user(
        self,
        test_user,
        test_message,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        validated_data = {
            "object_id": test_message.id,
            "comment": "Created comment",
        }

        comment = serializer.create(validated_data)

        assert comment.pk is not None
        assert comment.author == test_user
        assert comment.content_object == test_message
        assert comment.comment == "Created comment"
        assert comment.parent is None
        assert comment.main_comment is None

    def test_create_does_not_use_submitted_author(
        self,
        test_user,
        test_user_2,
        test_message,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        validated_data = {
            "object_id": test_message.id,
            "comment": "Created comment",
        }

        comment = serializer.create(validated_data)

        assert comment.author == test_user
        assert comment.author != test_user_2

    def test_create_creates_reply_with_parent_and_main_comment(
        self,
        test_user,
        test_message,
        test_comment,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        validated_data = {
            "object_id": test_message.id,
            "comment": "Reply comment",
            "parent": test_comment,
            "main_comment": test_comment,
        }

        comment = serializer.create(validated_data)

        assert comment.author == test_user
        assert comment.content_object == test_message
        assert comment.comment == "Reply comment"
        assert comment.parent == test_comment
        assert comment.main_comment == test_comment

    def test_create_uses_message_from_object_id(
        self,
        test_message,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        validated_data = {
            "object_id": test_message.id,
            "comment": "Object ID test",
        }

        comment = serializer.create(validated_data)

        assert comment.content_object == test_message

    def test_validate_object_id_accepts_existing_message(
        self,
        test_message,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        result = serializer.validate_object_id(test_message.id)

        assert result == test_message.id

    def test_validate_object_id_rejects_nonexistent_message(
        self,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        with pytest.raises(
            serializers.ValidationError,
            match="The specified message does not exist.",
        ):
            serializer.validate_object_id(999999)

    def test_invalid_object_id_fails_serializer_validation(
        self,
        serializer_context,
    ):
        serializer = CommentSerializer(
            data={
                "comment": "Invalid message",
                "object_id": 999999,
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is False
        assert "object_id" in serializer.errors

    def test_create_requires_object_id(
        self,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        with pytest.raises(KeyError):
            serializer.create(
                {
                    "comment": "Missing object ID",
                }
            )

    def test_create_requires_comment(
        self,
        test_message,
        serializer_context,
    ):
        serializer = CommentSerializer(
            context=serializer_context,
        )

        with pytest.raises(KeyError):
            serializer.create(
                {
                    "object_id": test_message.id,
                }
            )

    def test_is_valid_returns_boolean(
        self,
        test_message,
        serializer_context,
    ):
        serializer = CommentSerializer(
            data={
                "comment": "Test comment",
                "object_id": test_message.id,
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is True


class TestLikeCommentSerializer:
    def test_meta_model(self):
        assert LikeCommentSerializer.Meta.model is LikeComment

    def test_meta_fields(self):
        assert LikeCommentSerializer.Meta.fields == [
            "id",
            "user",
            "comment",
        ]

    def test_serializes_like_comment(
        self,
        test_user,
        test_comment,
        serializer_context,
    ):
        like = LikeComment.objects.create(
            user=test_user,
            comment=test_comment,
        )

        serializer = LikeCommentSerializer(like)

        assert serializer.data["id"] == like.id
        assert serializer.data["user"] == test_user.id
        assert serializer.data["comment"] == test_comment.id

    def test_to_internal_value_sets_request_user(
        self,
        test_user,
        test_comment,
        serializer_context,
    ):
        serializer = LikeCommentSerializer(
            context=serializer_context,
        )

        data = {
            "user": 999999,
            "comment": test_comment.id,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["user"].id == test_user.id

    def test_to_internal_value_adds_user_when_missing(
        self,
        test_user,
        test_comment,
        serializer_context,
    ):
        serializer = LikeCommentSerializer(
            context=serializer_context,
        )

        data = {
            "comment": test_comment.id,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["user"].id == test_user.id

    def test_to_internal_value_ignores_submitted_user(
        self,
        test_user,
        test_user_2,
        test_comment,
        serializer_context,
    ):
        serializer = LikeCommentSerializer(
            context=serializer_context,
        )

        data = {
            "user": test_user_2.id,
            "comment": test_comment.id,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["user"].id == test_user.id
        assert internal_data["user"].id != test_user_2.id

    def test_validation_accepts_valid_comment(
        self,
        test_comment,
        serializer_context,
    ):
        serializer = LikeCommentSerializer(
            data={"comment": test_comment.id},
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

    def test_save_creates_like_for_request_user(
        self,
        test_user,
        test_comment,
        serializer_context,
    ):
        serializer = LikeCommentSerializer(
            data={"comment": test_comment.id},
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        like = serializer.save()

        assert like.pk is not None
        assert like.user == test_user
        assert like.comment == test_comment

    def test_save_does_not_use_submitted_user(
        self,
        test_user,
        test_user_2,
        test_comment,
        serializer_context,
    ):
        serializer = LikeCommentSerializer(
            data={
                "user": test_user_2.id,
                "comment": test_comment.id,
            },
            context=serializer_context,
        )

        assert serializer.is_valid(), serializer.errors

        like = serializer.save()

        assert like.user == test_user
        assert like.user != test_user_2
