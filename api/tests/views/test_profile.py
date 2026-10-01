import io

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from account.models import Profile
from api.serializers import ProfileSerializer
from api.views import ProfileApiView, ProfileDetailApiView

UserModel = get_user_model()


@pytest.mark.django_db
class TestProfileApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def test_user(self):
        return UserModel.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )

    @pytest.fixture
    def test_user_2(self):
        return UserModel.objects.create_user(
            username="test_user_2",
            email="test2@example.com",
            password="testpass123",
            first_name="Second",
            last_name="User",
        )

    @pytest.fixture
    def profile(self, test_user):
        return Profile.objects.create(
            user=test_user,
            bio="Original bio",
            private=False,
        )

    @pytest.fixture
    def profile_2(self, test_user_2):
        return Profile.objects.create(
            user=test_user_2,
            bio="Second bio",
            private=True,
        )

    @pytest.fixture
    def profile_url(self):
        return reverse("api:profile")

    def profile_detail_url(self, profile):
        return reverse(
            "api:profile-detail",
            kwargs={"pk": profile.pk},
        )

    @staticmethod
    def image_file(name="profile.jpg"):
        image = Image.new("RGB", (100, 100), "white")
        image_file = io.BytesIO()
        image.save(image_file, format="JPEG")
        image_file.seek(0)

        from django.core.files.uploadedfile import SimpleUploadedFile

        return SimpleUploadedFile(
            name,
            image_file.read(),
            content_type="image/jpeg",
        )

    # ------------------------------------------------------------------
    # View configuration
    # ------------------------------------------------------------------

    def test_serializer_class(self):
        assert ProfileApiView.serializer_class is ProfileSerializer

    def test_queryset(self):
        assert ProfileApiView.queryset.model is Profile

    def test_detail_serializer_class(self):
        assert ProfileDetailApiView.serializer_class is ProfileSerializer

    def test_detail_queryset(self):
        assert ProfileDetailApiView.queryset.model is Profile

    def test_detail_parser_classes(self):
        from rest_framework.parsers import (
            FormParser,
            JSONParser,
            MultiPartParser,
        )

        assert ProfileDetailApiView.parser_classes == [
            FormParser,
            MultiPartParser,
            JSONParser,
        ]

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def test_get_returns_profiles(
        self,
        api_client,
        profile_url,
        profile,
        profile_2,
    ):
        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        profile_ids = {item["id"] for item in response.data}

        assert profile.id in profile_ids
        assert profile_2.id in profile_ids

    def test_get_returns_empty_list_when_no_profiles(
        self,
        api_client,
        profile_url,
    ):
        response = api_client.get(profile_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_create_profile(
        self,
        api_client,
        profile_url,
    ):
        response = api_client.post(
            profile_url,
            {
                "user": {
                    "first_name": "New",
                    "last_name": "User",
                    "email": "new@example.com",
                    "username": "new_user",
                },
                "bio": "New profile",
                "private": True,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        profile = Profile.objects.get(
            user__username="new_user",
        )

        assert profile.bio == "New profile"
        assert profile.private is True
        assert profile.user.first_name == "New"
        assert profile.user.last_name == "User"
        assert profile.user.email == "new@example.com"

    def test_create_profile_requires_nested_user(
        self,
        api_client,
        profile_url,
    ):
        response = api_client.post(
            profile_url,
            {
                "bio": "Profile without user",
                "private": False,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "user" in response.data

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def test_retrieve_profile(
        self,
        api_client,
        profile,
    ):
        response = api_client.get(
            self.profile_detail_url(profile),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == profile.id
        assert response.data["bio"] == profile.bio
        assert response.data["private"] is profile.private

        assert response.data["user"]["username"] == profile.user.username
        assert response.data["user"]["email"] == profile.user.email

    def test_retrieve_nonexistent_profile_returns_404(
        self,
        api_client,
    ):
        response = api_client.get(
            reverse(
                "api:profile-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Partial update
    # ------------------------------------------------------------------

    def test_partial_update_profile(
        self,
        api_client,
        profile,
    ):
        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "bio": "Updated bio",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.bio == "Updated bio"
        assert profile.private is False

    def test_partial_update_profile_updates_nested_user(
        self,
        api_client,
        profile,
    ):
        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "user": {
                    "first_name": "Updated",
                    "last_name": "Name",
                    "email": "updated@example.com",
                    "username": "updated_user",
                },
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        profile.user.refresh_from_db()

        assert profile.user.first_name == "Updated"
        assert profile.user.last_name == "Name"
        assert profile.user.email == "updated@example.com"
        assert profile.user.username == "updated_user"

    def test_partial_update_preserves_unspecified_profile_fields(
        self,
        api_client,
        profile,
    ):
        original_private = profile.private
        original_user = profile.user

        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "bio": "Changed only",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.bio == "Changed only"
        assert profile.private is original_private
        assert profile.user == original_user

    def test_partial_update_preserves_unspecified_nested_user_fields(
        self,
        api_client,
        profile,
    ):
        original_last_name = profile.user.last_name
        original_email = profile.user.email
        original_username = profile.user.username

        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "user": {
                    "first_name": "Changed",
                },
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.user.refresh_from_db()

        assert profile.user.first_name == "Changed"
        assert profile.user.last_name == original_last_name
        assert profile.user.email == original_email
        assert profile.user.username == original_username

    def test_partial_update_private_field(
        self,
        api_client,
        profile,
    ):
        assert profile.private is False

        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "private": True,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.private is True

    # ------------------------------------------------------------------
    # Full update
    # ------------------------------------------------------------------

    def test_full_update_profile(
        self,
        api_client,
        profile,
    ):
        response = api_client.put(
            self.profile_detail_url(profile),
            {
                "user": {
                    "first_name": "Full",
                    "last_name": "Update",
                    "email": "full@example.com",
                    "username": "full_update",
                },
                "bio": "Fully updated profile",
                "private": True,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()
        profile.user.refresh_from_db()

        assert profile.bio == "Fully updated profile"
        assert profile.private is True
        assert profile.user.first_name == "Full"
        assert profile.user.last_name == "Update"
        assert profile.user.email == "full@example.com"
        assert profile.user.username == "full_update"

    # ------------------------------------------------------------------
    # Image update
    # ------------------------------------------------------------------

    def test_update_profile_image(
        self,
        api_client,
        profile,
    ):
        image = self.image_file()

        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "profile_image": image,
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.profile_image
        assert profile.profile_image.name

        # DRF returns an absolute URL when a request is available,
        # while FieldFile.url is relative.
        assert response.data["profile_image"].endswith(
            profile.profile_image.url,
        )

    def test_update_profile_image_and_bio(
        self,
        api_client,
        profile,
    ):
        image = self.image_file("updated-profile.jpg")

        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "profile_image": image,
                "bio": "Bio with image",
            },
            format="multipart",
        )

        assert response.status_code == status.HTTP_200_OK

        profile.refresh_from_db()

        assert profile.profile_image
        assert profile.profile_image.name
        assert profile.bio == "Bio with image"

        assert response.data["profile_image"].endswith(
            profile.profile_image.url,
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def test_delete_profile(
        self,
        api_client,
        profile,
    ):
        profile_id = profile.id

        response = api_client.delete(
            self.profile_detail_url(profile),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Profile.objects.filter(pk=profile_id).exists()

    def test_delete_nonexistent_profile_returns_404(
        self,
        api_client,
    ):
        response = api_client.delete(
            reverse(
                "api:profile-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Update implementation behavior
    # ------------------------------------------------------------------

    def test_update_returns_updated_serializer_data(
        self,
        api_client,
        profile,
    ):
        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "bio": "Returned in response",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["bio"] == "Returned in response"

    def test_update_invalid_data_returns_400(
        self,
        api_client,
        profile,
    ):
        response = api_client.patch(
            self.profile_detail_url(profile),
            {
                "user": {
                    "username": "",
                },
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
