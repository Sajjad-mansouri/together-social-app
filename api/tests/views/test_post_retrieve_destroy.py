import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.permissions import AuthorDeletePermission
from api.serializers import PostSerializer
from api.views import PostRetrieveDestroyAPIView
from social.models import Message


@pytest.fixture
def api_client():
    return APIClient()


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
def test_message_2(test_user_2):
    return Message.objects.create(
        user=test_user_2,
        text="Other user's message",
    )


@pytest.fixture
def post_detail_url(test_message):
    return reverse(
        "api:post-detail",
        kwargs={"pk": test_message.pk},
    )


@pytest.mark.django_db
class TestPostRetrieveDestroyAPIView:
    def test_serializer_class(self):
        assert PostRetrieveDestroyAPIView.serializer_class is PostSerializer

    def test_permission_classes(self):
        assert PostRetrieveDestroyAPIView.permission_classes == [
            AuthorDeletePermission,
        ]

    def test_queryset_model(self):
        assert PostRetrieveDestroyAPIView.queryset.model is Message

    def test_get_returns_post(
        self,
        api_client,
        test_user,
        test_message,
        post_detail_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(post_detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == test_message.id
        assert response.data["text"] == test_message.text

    def test_get_returns_post_for_non_owner(
        self,
        api_client,
        test_user_2,
        test_message,
        post_detail_url,
    ):
        api_client.force_authenticate(user=test_user_2)

        response = api_client.get(post_detail_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == test_message.id

    def test_get_nonexistent_post_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        url = reverse(
            "api:post-detail",
            kwargs={"pk": 999999},
        )

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_owner_can_delete_post(
        self,
        api_client,
        test_user,
        test_message,
        post_detail_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(post_detail_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Message.objects.filter(pk=test_message.pk).exists()

    def test_non_owner_cannot_delete_post(
        self,
        api_client,
        test_user_2,
        test_message,
        post_detail_url,
    ):
        api_client.force_authenticate(user=test_user_2)

        response = api_client.delete(post_detail_url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Message.objects.filter(pk=test_message.pk).exists()

    def test_unauthenticated_user_cannot_delete_post(
        self,
        api_client,
        test_message,
        post_detail_url,
    ):
        response = api_client.delete(post_detail_url)

        assert response.status_code in {
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        }
        assert Message.objects.filter(pk=test_message.pk).exists()

    def test_delete_does_not_delete_other_posts(
        self,
        api_client,
        test_user,
        test_message,
        test_message_2,
        post_detail_url,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(post_detail_url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not Message.objects.filter(pk=test_message.pk).exists()
        assert Message.objects.filter(pk=test_message_2.pk).exists()
