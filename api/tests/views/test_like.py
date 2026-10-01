import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from account.models import Profile
from api.permissions import AuthorDeletePermission
from api.serializers import LikeSerializer
from api.views import LikeApiView, LikeDetailApiView
from social.models import Like, Message

UserModel = get_user_model()


@pytest.mark.django_db
class TestLikeApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def test_user(self):
        user = UserModel.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="testpass123",
        )
        Profile.objects.create(user=user)
        return user

    @pytest.fixture
    def test_user_2(self):
        user = UserModel.objects.create_user(
            username="test_user_2",
            email="test2@example.com",
            password="testpass123",
        )
        Profile.objects.create(user=user)
        return user

    @pytest.fixture
    def message(self, test_user):
        return Message.objects.create(
            user=test_user,
            text="Test post",
        )

    @pytest.fixture
    def message_2(self, test_user_2):
        return Message.objects.create(
            user=test_user_2,
            text="Second test post",
        )

    @pytest.fixture
    def like(self, test_user, message):
        return Like.objects.create(
            user=test_user,
            post=message,
        )

    @pytest.fixture
    def like_url(self):
        return reverse("api:like")

    def like_detail_url(self, like):
        return reverse(
            "api:like-detail",
            kwargs={"pk": like.pk},
        )

    # ------------------------------------------------------------------
    # View configuration
    # ------------------------------------------------------------------

    def test_serializer_class(self):
        assert LikeApiView.serializer_class is LikeSerializer

    def test_queryset(self):
        assert LikeApiView.queryset.model is Like

    def test_detail_serializer_class(self):
        assert LikeDetailApiView.serializer_class is LikeSerializer

    def test_detail_queryset(self):
        assert LikeDetailApiView.queryset.model is Like

    def test_detail_permission_classes(self):
        assert LikeDetailApiView.permission_classes == [
            AuthorDeletePermission,
        ]

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def test_get_returns_likes(
        self,
        api_client,
        like_url,
        test_user,
        message,
    ):
        like = Like.objects.create(
            user=test_user,
            post=message,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(like_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == like.id
        assert response.data[0]["user"] == test_user.id
        assert response.data[0]["post"] == message.id

    def test_get_returns_empty_list_when_no_likes(
        self,
        api_client,
        like_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(like_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_get_returns_all_likes(
        self,
        api_client,
        like_url,
        test_user,
        test_user_2,
        message,
        message_2,
    ):
        like_1 = Like.objects.create(
            user=test_user,
            post=message,
        )
        like_2 = Like.objects.create(
            user=test_user_2,
            post=message_2,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(like_url)

        assert response.status_code == status.HTTP_200_OK

        like_ids = {item["id"] for item in response.data}

        assert like_1.id in like_ids
        assert like_2.id in like_ids

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_create_like(
        self,
        api_client,
        like_url,
        test_user,
        message,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            like_url,
            {
                "user": test_user.id,
                "post": message.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        like = Like.objects.get(
            user=test_user,
            post=message,
        )

        assert like.user == test_user
        assert like.post == message
        assert response.data["id"] == like.id

    def test_create_like_ignores_submitted_user(
        self,
        api_client,
        like_url,
        test_user,
        test_user_2,
        message,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            like_url,
            {
                "user": test_user_2.id,
                "post": message.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        like = Like.objects.get(
            post=message,
        )

        assert like.user == test_user
        assert like.user != test_user_2

    def test_create_like_requires_post(
        self,
        api_client,
        like_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            like_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "post" in response.data

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def test_retrieve_like(
        self,
        api_client,
        like,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            self.like_detail_url(like),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == like.id
        assert response.data["user"] == like.user.id
        assert response.data["post"] == like.post.id

    def test_retrieve_nonexistent_like_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            reverse(
                "api:like-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def test_delete_like(
        self,
        api_client,
        like,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            self.like_detail_url(like),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Like.objects.filter(pk=like.pk).exists()

    def test_delete_nonexistent_like_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            reverse(
                "api:like-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_like_by_another_user_is_rejected(
        self,
        api_client,
        like,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user_2)

        response = api_client.delete(
            self.like_detail_url(like),
        )

        assert response.status_code in {
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        }

        assert Like.objects.filter(pk=like.pk).exists()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_list_does_not_require_authentication(
        self,
        api_client,
        like_url,
    ):
        response = api_client.get(like_url)

        assert response.status_code == status.HTTP_200_OK

    def test_create_does_not_require_authentication(
        self,
        api_client,
        like_url,
    ):
        response = api_client.post(
            like_url,
            {},
            format="json",
        )

        # The view has no explicit IsAuthenticated permission.
        # The serializer accesses request.user.id, so anonymous
        # requests may fail during validation rather than return 401.
        assert response.status_code in {
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        }

    def test_retrieve_does_not_require_authentication(
        self,
        api_client,
        like,
    ):
        response = api_client.get(
            self.like_detail_url(like),
        )

        assert response.status_code == status.HTTP_200_OK

    def test_delete_requires_authenticated_user_for_permission_check(
        self,
        api_client,
        like,
    ):
        response = api_client.delete(
            self.like_detail_url(like),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Like.objects.filter(pk=like.pk).exists()
