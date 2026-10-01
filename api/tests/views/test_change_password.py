import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient

from api.views import ChangePasswordView


@pytest.mark.django_db
class TestChangePasswordView:
    def test_view_configuration(self):
        assert ChangePasswordView.serializer_class.__name__ == (
            "ChangePasswordSerializer"
        )
        assert ChangePasswordView.permission_classes == [IsAuthenticated]

    def test_change_password(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="OldPassword123!",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.put(
            reverse("api:change-password"),
            {
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        assert user.check_password("NewPassword123!")
        assert not user.check_password("OldPassword123!")

    def test_invalid_old_password_returns_400(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="OldPassword123!",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.put(
            reverse("api:change-password"),
            {
                "old_password": "WrongPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")

    def test_passwords_must_match(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="OldPassword123!",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.put(
            reverse("api:change-password"),
            {
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "DifferentPassword123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")

    def test_missing_required_fields_returns_400(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="OldPassword123!",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.put(
            reverse("api:change-password"),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")

    def test_unauthenticated_request_returns_401(self):
        client = APIClient()

        response = client.put(
            reverse("api:change-password"),
            {
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_weak_password_returns_400(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="OldPassword123!",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.put(
            reverse("api:change-password"),
            {
                "old_password": "OldPassword123!",
                "password1": "123",
                "password2": "123",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        user.refresh_from_db()
        assert user.check_password("OldPassword123!")
