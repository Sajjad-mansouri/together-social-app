import pytest
from django.test import RequestFactory

from api.serializers import SavedPostSerializer
from social.models import Message, SavePost


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
    request = RequestFactory().post("/api/saved-posts/")
    request.user = test_user
    return request


class TestSavedPostSerializerMeta:
    def test_model(self):
        assert SavedPostSerializer.Meta.model is SavePost

    def test_fields(self):
        assert SavedPostSerializer.Meta.fields == [
            "id",
            "user",
            "post",
        ]


class TestSavedPostSerializerToInternalValue:
    def test_sets_user_to_request_user(
        self,
        test_request,
        test_user,
        test_message,
    ):
        serializer = SavedPostSerializer(
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
        serializer = SavedPostSerializer(
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
        serializer = SavedPostSerializer(
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
        serializer = SavedPostSerializer(
            context={"request": test_request},
        )

        data = {
            "post": test_message.pk,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["user"] == test_user


class TestSavedPostSerializerRepresentation:
    def test_serializes_saved_post(
        self,
        test_user,
        test_message,
    ):
        saved_post = SavePost.objects.create(
            user=test_user,
            post=test_message,
        )

        serializer = SavedPostSerializer(instance=saved_post)

        assert serializer.data["id"] == saved_post.id
        assert serializer.data["user"] == test_user.id
        assert serializer.data["post"] == test_message.id

    def test_contains_expected_fields(
        self,
        test_user,
        test_message,
    ):
        saved_post = SavePost.objects.create(
            user=test_user,
            post=test_message,
        )

        serializer = SavedPostSerializer(instance=saved_post)

        assert set(serializer.data) == {
            "id",
            "user",
            "post",
        }


class TestSavedPostSerializerValidation:
    def test_is_valid_with_valid_data(
        self,
        test_request,
        test_user,
        test_message,
    ):
        serializer = SavedPostSerializer(
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
        serializer = SavedPostSerializer(
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
        serializer = SavedPostSerializer(
            data={},
            context={"request": test_request},
        )

        assert serializer.is_valid() is False
        assert "post" in serializer.errors


class TestSavedPostSerializerCreate:
    def test_save_creates_saved_post_for_request_user(
        self,
        test_request,
        test_user,
        test_message,
    ):
        serializer = SavedPostSerializer(
            data={"post": test_message.pk},
            context={"request": test_request},
        )

        assert serializer.is_valid() is True

        saved_post = serializer.save()

        assert saved_post.user == test_user
        assert saved_post.post == test_message

    def test_save_does_not_create_saved_post_for_submitted_user(
        self,
        test_request,
        test_user,
        test_user_2,
        test_message,
    ):
        serializer = SavedPostSerializer(
            data={
                "user": test_user_2.pk,
                "post": test_message.pk,
            },
            context={"request": test_request},
        )

        assert serializer.is_valid() is True

        saved_post = serializer.save()

        assert saved_post.user == test_user
        assert saved_post.user != test_user_2
