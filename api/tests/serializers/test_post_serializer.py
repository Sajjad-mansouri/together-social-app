from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from PIL import Image

from api.serializers import PostSerializer
from social.models import Like, Message, SavePost


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
def test_request(test_user):
    request = RequestFactory().get("/api/posts/")
    request.user = test_user
    return request


@pytest.fixture
def serializer(test_request):
    return PostSerializer(context={"request": test_request})


@pytest.fixture
def image_file():
    image = Image.new("RGB", (10, 10), color="white")

    image_data = BytesIO()
    image.save(image_data, format="JPEG")
    image_data.seek(0)

    return SimpleUploadedFile(
        "test.jpg",
        image_data.read(),
        content_type="image/jpeg",
    )


class TestPostSerializerMeta:
    def test_model(self):
        assert PostSerializer.Meta.model is Message

    def test_fields(self):
        assert PostSerializer.Meta.fields == [
            "id",
            "text",
            "image",
            "created",
            "owner",
            "user",
            "is_liked",
            "is_saved",
        ]

    def test_read_only_fields(self):
        assert PostSerializer.Meta.read_only_fields == [
            "owner",
            "is_liked",
        ]


class TestPostSerializerLiked:
    def test_unliked_post_returns_false_none_and_zero_count(
        self,
        serializer,
        test_message,
    ):
        result = serializer.liked(test_message)

        assert result == (False, None, 0)

    def test_liked_post_returns_like_information(
        self,
        serializer,
        test_message,
        test_user,
    ):
        like = Like.objects.create(
            user=test_user,
            post=test_message,
        )

        result = serializer.liked(test_message)

        assert result == (True, like.id, 1)

    def test_like_count_includes_likes_from_other_users(
        self,
        serializer,
        test_message,
        test_user,
        test_user_2,
    ):
        first_like = Like.objects.create(
            user=test_user,
            post=test_message,
        )
        Like.objects.create(
            user=test_user_2,
            post=test_message,
        )

        result = serializer.liked(test_message)

        assert result == (True, first_like.id, 2)

    def test_like_on_different_post_does_not_mark_current_post_as_liked(
        self,
        serializer,
        test_message,
        test_message_2,
        test_user,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message_2,
        )

        result = serializer.liked(test_message)

        assert result == (False, None, 0)


class TestPostSerializerSaved:
    def test_unsaved_post_returns_false_and_none(
        self,
        serializer,
        test_message,
    ):
        result = serializer.saved(test_message)

        assert result == (False, None)

    def test_saved_post_returns_save_information(
        self,
        serializer,
        test_message,
        test_user,
    ):
        saved_post = SavePost.objects.create(
            user=test_user,
            post=test_message,
        )

        result = serializer.saved(test_message)

        assert result == (True, saved_post.id)

    def test_save_on_different_post_does_not_mark_current_post_as_saved(
        self,
        serializer,
        test_message,
        test_message_2,
        test_user,
    ):
        SavePost.objects.create(
            user=test_user,
            post=test_message_2,
        )

        result = serializer.saved(test_message)

        assert result == (False, None)


class TestPostSerializerRepresentation:
    def test_contains_expected_fields(
        self,
        serializer,
        test_message,
    ):
        data = serializer.to_representation(test_message)

        assert set(data) == {
            "id",
            "text",
            "image",
            "created",
            "owner",
            "user",
            "is_liked",
            "is_saved",
        }

    def test_basic_message_fields(
        self,
        serializer,
        test_message,
    ):
        data = serializer.to_representation(test_message)

        assert data["id"] == test_message.id
        assert data["text"] == test_message.text
        assert data["user"] == test_message.user.id

    def test_owner_contains_username(
        self,
        serializer,
        test_message,
    ):
        data = serializer.to_representation(test_message)

        assert data["owner"]["username"] == test_message.user.username

    def test_unliked_post_has_expected_like_state(
        self,
        serializer,
        test_message,
    ):
        data = serializer.to_representation(test_message)

        assert data["is_liked"] == (False, None, 0)

    def test_unsaved_post_has_expected_save_state(
        self,
        serializer,
        test_message,
    ):
        data = serializer.to_representation(test_message)

        assert data["is_saved"] == (False, None)

    def test_liked_post_has_expected_like_state(
        self,
        serializer,
        test_message,
        test_user,
    ):
        like = Like.objects.create(
            user=test_user,
            post=test_message,
        )

        data = serializer.to_representation(test_message)

        assert data["is_liked"] == (True, like.id, 1)

    def test_saved_post_has_expected_save_state(
        self,
        serializer,
        test_message,
        test_user,
    ):
        saved_post = SavePost.objects.create(
            user=test_user,
            post=test_message,
        )

        data = serializer.to_representation(test_message)

        assert data["is_saved"] == (True, saved_post.id)


class TestPostSerializerValidation:
    def test_to_internal_value_sets_request_user(
        self,
        test_user,
        image_file,
    ):
        request = RequestFactory().post("/api/posts/")
        request.user = test_user

        serializer = PostSerializer(
            context={"request": request},
        )

        internal_data = serializer.to_internal_value(
            {
                "text": "New message",
                "image": image_file,
            }
        )

        assert internal_data["user"] == test_user

    def test_to_internal_value_replaces_submitted_user(
        self,
        test_user,
        test_user_2,
        image_file,
    ):
        request = RequestFactory().post("/api/posts/")
        request.user = test_user

        serializer = PostSerializer(
            context={"request": request},
        )

        internal_data = serializer.to_internal_value(
            {
                "text": "New message",
                "image": image_file,
                "user": test_user_2.pk,
            }
        )

        assert internal_data["user"] == test_user

    def test_to_internal_value_does_not_trust_submitted_user(
        self,
        test_user,
        test_user_2,
        image_file,
    ):
        request = RequestFactory().post("/api/posts/")
        request.user = test_user

        serializer = PostSerializer(
            context={"request": request},
        )

        internal_data = serializer.to_internal_value(
            {
                "text": "New message",
                "image": image_file,
                "user": test_user_2.pk,
            }
        )

        assert internal_data["user"] != test_user_2
        assert internal_data["user"] == test_user

    def test_is_valid_returns_false_without_required_image(
        self,
        test_user,
    ):
        request = RequestFactory().post("/api/posts/")
        request.user = test_user

        serializer = PostSerializer(
            data={
                "text": "New message",
            },
            context={"request": request},
        )

        assert serializer.is_valid() is False
        assert "image" in serializer.errors

    def test_is_valid_returns_true_with_valid_data(
        self,
        test_user,
        image_file,
    ):
        request = RequestFactory().post("/api/posts/")
        request.user = test_user

        serializer = PostSerializer(
            data={
                "text": "New message",
                "image": image_file,
            },
            context={"request": request},
        )

        assert serializer.is_valid() is True

    def test_validated_data_contains_request_user(
        self,
        test_user,
        image_file,
    ):
        request = RequestFactory().post("/api/posts/")
        request.user = test_user

        serializer = PostSerializer(
            data={
                "text": "New message",
                "image": image_file,
            },
            context={"request": request},
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["user"] == test_user


class TestPostSerializerContext:
    def test_liked_state_uses_request_user(
        self,
        test_user,
        test_user_2,
        test_message,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )

        request = RequestFactory().get("/api/posts/")
        request.user = test_user_2

        serializer = PostSerializer(
            instance=test_message,
            context={"request": request},
        )

        data = serializer.data

        assert data["is_liked"] == (False, None, 1)

    def test_saved_state_uses_request_user(
        self,
        test_user,
        test_user_2,
        test_message,
    ):
        SavePost.objects.create(
            user=test_user,
            post=test_message,
        )

        request = RequestFactory().get("/api/posts/")
        request.user = test_user_2

        serializer = PostSerializer(
            instance=test_message,
            context={"request": request},
        )

        data = serializer.data

        assert data["is_saved"] == (False, None)
