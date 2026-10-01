from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from account.models import Profile
from api.serializers import (
    UserProfileSerializer,
    profileSerializerReadOnly,
)


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
def profile_image():
    image = Image.new("RGB", (10, 10), color="white")
    image_data = BytesIO()
    image.save(image_data, format="JPEG")
    image_data.seek(0)

    return SimpleUploadedFile(
        "profile.jpg",
        image_data.read(),
        content_type="image/jpeg",
    )


@pytest.fixture
def test_profile(test_user, profile_image):
    return Profile.objects.create(
        user=test_user,
        profile_image=profile_image,
    )


class TestProfileSerializerReadOnlyMeta:
    def test_model(self):
        assert profileSerializerReadOnly.Meta.model is Profile

    def test_fields(self):
        assert profileSerializerReadOnly.Meta.fields == [
            "profile_image",
        ]


class TestProfileSerializerReadOnlySerialization:
    def test_serializes_profile_image(
        self,
        test_profile,
    ):
        serializer = profileSerializerReadOnly(instance=test_profile)

        profile_image = serializer.data["profile_image"]

        assert profile_image
        assert profile_image.startswith("/media/")

    def test_contains_only_profile_image(
        self,
        test_profile,
    ):
        serializer = profileSerializerReadOnly(instance=test_profile)

        assert set(serializer.data) == {"profile_image"}

    def test_profile_image_matches_model_url(
        self,
        test_profile,
    ):
        serializer = profileSerializerReadOnly(instance=test_profile)

        assert serializer.data["profile_image"] == test_profile.profile_image.url


class TestUserProfileSerializerMeta:
    def test_model(self):
        from django.contrib.auth import get_user_model

        assert UserProfileSerializer.Meta.model is get_user_model()

    def test_fields(self):
        assert UserProfileSerializer.Meta.fields == [
            "username",
            "profile",
        ]


class TestUserProfileSerializerSerialization:
    def test_serializes_username(
        self,
        test_user,
        test_profile,
    ):
        serializer = UserProfileSerializer(instance=test_user)

        assert serializer.data["username"] == test_user.username

    def test_serializes_nested_profile(
        self,
        test_user,
        test_profile,
    ):
        serializer = UserProfileSerializer(instance=test_user)

        assert serializer.data["profile"]["profile_image"]
        assert serializer.data["profile"]["profile_image"].startswith("/media/")

    def test_contains_expected_fields(
        self,
        test_user,
        test_profile,
    ):
        serializer = UserProfileSerializer(instance=test_user)

        assert set(serializer.data) == {
            "username",
            "profile",
        }

    def test_nested_profile_contains_only_profile_image(
        self,
        test_user,
        test_profile,
    ):
        serializer = UserProfileSerializer(instance=test_user)

        assert set(serializer.data["profile"]) == {"profile_image"}

    def test_nested_profile_image_matches_model_url(
        self,
        test_user,
        test_profile,
    ):
        serializer = UserProfileSerializer(instance=test_user)

        assert (
            serializer.data["profile"]["profile_image"]
            == test_profile.profile_image.url
        )


class TestUserProfileSerializerReadOnly:
    def test_profile_field_is_read_only(self):
        field = UserProfileSerializer._declared_fields["profile"]

        assert field.read_only is True

    def test_profile_uses_profile_serializer(self):
        field = UserProfileSerializer._declared_fields["profile"]

        assert isinstance(field, profileSerializerReadOnly)

    def test_profile_serializer_has_one_field(self):
        field = UserProfileSerializer().fields["profile"]

        assert set(field.fields) == {"profile_image"}
