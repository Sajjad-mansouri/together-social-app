from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from account.models import Profile
from api.serializers import UserSerializer


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


class TestUserSerializerMeta:
    def test_model(self):
        from django.contrib.auth import get_user_model

        assert UserSerializer.Meta.model is get_user_model()

    def test_fields(self):
        assert UserSerializer.Meta.fields == [
            "first_name",
            "last_name",
            "email",
            "username",
            "profile_image",
        ]


class TestUserSerializerSerialization:
    def test_serializes_user_fields(self, test_user, test_profile):
        serializer = UserSerializer(instance=test_user)

        assert serializer.data["first_name"] == test_user.first_name
        assert serializer.data["last_name"] == test_user.last_name
        assert serializer.data["email"] == test_user.email
        assert serializer.data["username"] == test_user.username

    def test_serializes_profile_image(self, test_user, test_profile):
        serializer = UserSerializer(instance=test_user)

        profile_image = serializer.data["profile_image"]

        assert profile_image
        assert profile_image.startswith("/media/")

    def test_serializes_expected_fields(self, test_user, test_profile):
        serializer = UserSerializer(instance=test_user)

        assert set(serializer.data) == {
            "first_name",
            "last_name",
            "email",
            "username",
            "profile_image",
        }

    def test_serializes_exact_values(self, test_user, test_profile):
        serializer = UserSerializer(instance=test_user)

        assert serializer.data == {
            "first_name": test_user.first_name,
            "last_name": test_user.last_name,
            "email": test_user.email,
            "username": test_user.username,
            "profile_image": test_user.profile.profile_image.url,
        }


class TestUserSerializerMultipleUsers:
    def test_serializes_multiple_users(self, db, django_user_model):
        user_1 = django_user_model.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="testpass123",
            first_name="First",
            last_name="User",
        )
        user_2 = django_user_model.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpass123",
            first_name="Second",
            last_name="User",
        )

        profile_image_1 = Image.new("RGB", (10, 10), color="white")
        image_data_1 = BytesIO()
        profile_image_1.save(image_data_1, format="JPEG")
        image_data_1.seek(0)

        profile_image_2 = Image.new("RGB", (10, 10), color="white")
        image_data_2 = BytesIO()
        profile_image_2.save(image_data_2, format="JPEG")
        image_data_2.seek(0)

        Profile.objects.create(
            user=user_1,
            profile_image=SimpleUploadedFile(
                "profile1.jpg",
                image_data_1.read(),
                content_type="image/jpeg",
            ),
        )
        Profile.objects.create(
            user=user_2,
            profile_image=SimpleUploadedFile(
                "profile2.jpg",
                image_data_2.read(),
                content_type="image/jpeg",
            ),
        )

        serializer = UserSerializer(
            instance=[user_1, user_2],
            many=True,
        )

        assert len(serializer.data) == 2
        assert serializer.data[0]["username"] == "user1"
        assert serializer.data[1]["username"] == "user2"
        assert serializer.data[0]["email"] == "user1@example.com"
        assert serializer.data[1]["email"] == "user2@example.com"


class TestUserSerializerProfileImage:
    def test_profile_image_uses_profile_source(self):
        field = UserSerializer._declared_fields["profile_image"]

        assert field.source == "profile.profile_image"

    def test_profile_image_is_image_field(self):
        from rest_framework import serializers

        field = UserSerializer._declared_fields["profile_image"]

        assert isinstance(field, serializers.ImageField)


class TestUserSerializerEdgeCases:
    def test_empty_first_name_and_last_name_are_serialized(
        self,
        django_user_model,
    ):
        user = django_user_model.objects.create_user(
            username="minimaluser",
            email="minimal@example.com",
            password="testpass123",
            first_name="",
            last_name="",
        )

        image = Image.new("RGB", (10, 10), color="white")
        image_data = BytesIO()
        image.save(image_data, format="JPEG")
        image_data.seek(0)

        Profile.objects.create(
            user=user,
            profile_image=SimpleUploadedFile(
                "profile.jpg",
                image_data.read(),
                content_type="image/jpeg",
            ),
        )

        serializer = UserSerializer(instance=user)

        assert serializer.data["first_name"] == ""
        assert serializer.data["last_name"] == ""
        assert serializer.data["username"] == "minimaluser"
        assert serializer.data["email"] == "minimal@example.com"
