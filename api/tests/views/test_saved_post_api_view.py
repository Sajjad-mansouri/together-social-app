import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from account.models import Profile
from api.permissions import AuthorDeletePermission
from api.serializers import SavedPostSerializer
from api.views import AddSavedApiView, SavedPostDetailApiView
from social.models import Message, SavePost

UserModel = get_user_model()


@pytest.mark.django_db
class TestAddSavedApiView:
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
    def saved_post(self, test_user, message):
        return SavePost.objects.create(
            user=test_user,
            post=message,
        )

    @pytest.fixture
    def saved_url(self):
        return reverse("api:saved")

    def saved_detail_url(self, saved_post):
        return reverse(
            "api:saved-detail",
            kwargs={"pk": saved_post.pk},
        )

    # ------------------------------------------------------------------
    # View configuration
    # ------------------------------------------------------------------

    def test_serializer_class(self):
        assert AddSavedApiView.serializer_class is SavedPostSerializer

    def test_get_queryset_returns_current_users_saved_posts(
        self,
        test_user,
        test_user_2,
        message,
        message_2,
    ):
        user_saved_post = SavePost.objects.create(
            user=test_user,
            post=message,
        )
        other_saved_post = SavePost.objects.create(
            user=test_user_2,
            post=message_2,
        )

        view = AddSavedApiView()

        class Request:
            user = test_user

        view.request = Request()

        queryset = view.get_queryset()

        assert list(queryset) == [user_saved_post]
        assert other_saved_post not in queryset

    def test_get_queryset_is_empty_when_user_has_no_saved_posts(
        self,
        test_user,
    ):
        view = AddSavedApiView()

        class Request:
            user = test_user

        view.request = Request()

        assert list(view.get_queryset()) == []

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_create_saved_post(
        self,
        api_client,
        saved_url,
        test_user,
        message,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            saved_url,
            {
                "user": test_user.id,
                "post": message.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        saved_post = SavePost.objects.get(
            user=test_user,
            post=message,
        )

        assert saved_post.user == test_user
        assert saved_post.post == message
        assert response.data["id"] == saved_post.id
        assert response.data["user"] == test_user.id
        assert response.data["post"] == message.id

    def test_create_saved_post_ignores_submitted_user(
        self,
        api_client,
        saved_url,
        test_user,
        test_user_2,
        message,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            saved_url,
            {
                "user": test_user_2.id,
                "post": message.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        saved_post = SavePost.objects.get(post=message)

        assert saved_post.user == test_user
        assert saved_post.user != test_user_2

    def test_create_saved_post_requires_post(
        self,
        api_client,
        saved_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            saved_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "post" in response.data

    def test_create_saved_post_for_different_post(
        self,
        api_client,
        saved_url,
        test_user,
        message,
        message_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            saved_url,
            {"post": message_2.id},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        saved_post = SavePost.objects.get(
            user=test_user,
            post=message_2,
        )

        assert saved_post.user == test_user
        assert saved_post.post == message_2

    # ------------------------------------------------------------------
    # Detail configuration
    # ------------------------------------------------------------------

    def test_detail_serializer_class(self):
        assert SavedPostDetailApiView.serializer_class is SavedPostSerializer

    def test_detail_queryset(self):
        assert SavedPostDetailApiView.queryset.model is SavePost

    def test_detail_permission_classes(self):
        assert SavedPostDetailApiView.permission_classes == [
            AuthorDeletePermission,
        ]

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def test_retrieve_saved_post(
        self,
        api_client,
        saved_post,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            self.saved_detail_url(saved_post),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == saved_post.id
        assert response.data["user"] == test_user.id
        assert response.data["post"] == saved_post.post.id

    def test_retrieve_nonexistent_saved_post_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            reverse(
                "api:saved-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def test_delete_saved_post(
        self,
        api_client,
        saved_post,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            self.saved_detail_url(saved_post),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not SavePost.objects.filter(pk=saved_post.pk).exists()

    def test_delete_nonexistent_saved_post_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            reverse(
                "api:saved-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_saved_post_by_another_user_is_rejected(
        self,
        api_client,
        saved_post,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user_2)

        response = api_client.delete(
            self.saved_detail_url(saved_post),
        )

        assert response.status_code in {
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        }

        assert SavePost.objects.filter(pk=saved_post.pk).exists()

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_create_does_not_explicitly_require_authentication(
        self,
        api_client,
        saved_url,
        message,
    ):
        response = api_client.post(
            saved_url,
            {"post": message.id},
            format="json",
        )

        # AddSavedApiView does not define permission_classes.
        # SavedPostSerializer accesses request.user.id, so the exact
        # behavior is determined by the serializer and authentication
        # configuration.
        assert response.status_code in {
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        }

    def test_retrieve_does_not_explicitly_require_authentication(
        self,
        api_client,
        saved_post,
    ):
        response = api_client.get(
            self.saved_detail_url(saved_post),
        )

        assert response.status_code == status.HTTP_200_OK

    def test_delete_requires_authenticated_user_for_permission_check(
        self,
        api_client,
        saved_post,
    ):
        response = api_client.delete(
            self.saved_detail_url(saved_post),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert SavePost.objects.filter(pk=saved_post.pk).exists()
