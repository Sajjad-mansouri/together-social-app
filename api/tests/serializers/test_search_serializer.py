from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from api.serializers import SearchSerializer


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
    from account.models import Profile

    return Profile.objects.create(
        user=test_user,
        profile_image=profile_image,
    )


class TestSearchSerializerMeta:
    def test_model(self):
        from django.contrib.auth import get_user_model

        assert SearchSerializer.Meta.model is get_user_model()

    def test_fields(self):
        assert SearchSerializer.Meta.fields == [
            "first_name",
            "last_name",
            "username",
            "profile_image",
        ]


class TestSearchSerializerSerialization:
    def test_serializes_user_fields(self, test_user, test_profile):
        serializer = SearchSerializer(instance=test_user)

        assert serializer.data["first_name"] == "Test"
        assert serializer.data["last_name"] == "User"
        assert serializer.data["username"] == "testuser"

    def test_serializes_profile_image(self, test_user, test_profile):
        serializer = SearchSerializer(instance=test_user)

        profile_image = serializer.data["profile_image"]

        assert profile_image
        assert profile_image.startswith("/media/")

    def test_serializes_all_expected_fields(self, test_user, test_profile):
        serializer = SearchSerializer(instance=test_user)

        assert set(serializer.data) == {
            "first_name",
            "last_name",
            "username",
            "profile_image",
        }

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

        serializer = SearchSerializer(
            instance=[user_1, user_2],
            many=True,
        )

        assert len(serializer.data) == 2
        assert serializer.data[0]["username"] == "user1"
        assert serializer.data[1]["username"] == "user2"


class TestSearchSerializerValidation:
    def test_serializer_is_read_only_for_model_instance(
        self,
        test_user,
        test_profile,
    ):
        serializer = SearchSerializer(instance=test_user)

        assert serializer.data["username"] == test_user.username

    def test_profile_image_field_uses_profile_source(self):
        assert (
            SearchSerializer._declared_fields["profile_image"].source
            == "profile.profile_image"
        )
