import pytest
from django.test import RequestFactory

from api.serializers import LikeSerializer
from social.models import Like, Message


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
def test_request(test_user):
    request = RequestFactory().post("/api/likes/")
    request.user = test_user
    return request


class TestLikeSerializerMeta:
    def test_model(self):
        assert LikeSerializer.Meta.model is Like

    def test_fields(self):
        assert LikeSerializer.Meta.fields == [
            "id",
            "user",
            "post",
        ]


class TestLikeSerializerToInternalValue:
    def test_sets_user_to_request_user(
        self,
        test_request,
        test_user,
        test_message,
    ):
        serializer = LikeSerializer(
            context={"request": test_request},
        )

        data = {
            "user": test_user.pk,
            "post": test_message.pk,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["user"] == test_user

    def test_does_not_trust_submitted_user(
        self,
        test_request,
        test_user,
        test_user_2,
        test_message,
    ):
        serializer = LikeSerializer(
            context={"request": test_request},
        )

        data = {
            "user": test_user_2.pk,
            "post": test_message.pk,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["user"] == test_user
        assert internal_data["user"] != test_user_2

    def test_user_is_overwritten_when_submitted_user_is_different(
        self,
        test_request,
        test_user,
        test_user_2,
        test_message,
    ):
        serializer = LikeSerializer(
            context={"request": test_request},
        )

        data = {
            "user": test_user_2.pk,
            "post": test_message.pk,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["user"].pk == test_user.pk

    def test_user_is_added_when_not_submitted(
        self,
        test_request,
        test_user,
        test_message,
    ):
        serializer = LikeSerializer(
            context={"request": test_request},
        )

        data = {
            "post": test_message.pk,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["user"] == test_user


class TestLikeSerializerRepresentation:
    def test_serializes_like(
        self,
        test_user,
        test_message,
    ):
        like = Like.objects.create(
            user=test_user,
            post=test_message,
        )

        serializer = LikeSerializer(instance=like)

        assert serializer.data["id"] == like.id
        assert serializer.data["user"] == test_user.id
        assert serializer.data["post"] == test_message.id

    def test_contains_expected_fields(
        self,
        test_user,
        test_message,
    ):
        like = Like.objects.create(
            user=test_user,
            post=test_message,
        )

        serializer = LikeSerializer(instance=like)

        assert set(serializer.data) == {
            "id",
            "user",
            "post",
        }


class TestLikeSerializerValidation:
    def test_is_valid_with_valid_data(
        self,
        test_request,
        test_user,
        test_message,
    ):
        serializer = LikeSerializer(
            data={"post": test_message.pk},
            context={"request": test_request},
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["user"] == test_user
        assert serializer.validated_data["post"] == test_message

    def test_is_valid_ignores_submitted_user(
        self,
        test_request,
        test_user,
        test_user_2,
        test_message,
    ):
        serializer = LikeSerializer(
            data={
                "user": test_user_2.pk,
                "post": test_message.pk,
            },
            context={"request": test_request},
        )

        assert serializer.is_valid() is True
        assert serializer.validated_data["user"] == test_user
        assert serializer.validated_data["user"] != test_user_2

    def test_is_invalid_without_post(
        self,
        test_request,
    ):
        serializer = LikeSerializer(
            data={},
            context={"request": test_request},
        )

        assert serializer.is_valid() is False
        assert "post" in serializer.errors


class TestLikeSerializerCreate:
    def test_save_creates_like_for_request_user(
        self,
        test_request,
        test_user,
        test_message,
    ):
        serializer = LikeSerializer(
            data={"post": test_message.pk},
            context={"request": test_request},
        )

        assert serializer.is_valid() is True

        like = serializer.save()

        assert like.user == test_user
        assert like.post == test_message

    def test_save_does_not_create_like_for_submitted_user(
        self,
        test_request,
        test_user,
        test_user_2,
        test_message,
    ):
        serializer = LikeSerializer(
            data={
                "user": test_user_2.pk,
                "post": test_message.pk,
            },
            context={"request": test_request},
        )

        assert serializer.is_valid() is True

        like = serializer.save()

        assert like.user == test_user
        assert like.user != test_user_2
