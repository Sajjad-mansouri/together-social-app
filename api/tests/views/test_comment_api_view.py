import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient

from api.permissions import AuthorDeletePermission
from api.serializers import CommentSerializer, LikeCommentSerializer
from api.views import (
    CommentApiView,
    CommentDetailApiView,
    LikeCommentApiView,
    LikeCommentDetailApiView,
)
from social.models import Comment, LikeComment, Message

UserModel = get_user_model()


@pytest.mark.django_db
class TestCommentApiView:
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
    def message(self, test_user):
        return Message.objects.create(
            user=test_user,
            text="Test post",
        )

    @pytest.fixture
    def message_2(self, test_user_2):
        return Message.objects.create(
            user=test_user_2,
            text="Second post",
        )

    @pytest.fixture
    def comment(self, message, test_user):
        return Comment.objects.create(
            content_object=message,
            author=test_user,
            comment="Test comment",
        )

    @pytest.fixture
    def comment_2(self, message, test_user_2):
        return Comment.objects.create(
            content_object=message,
            author=test_user_2,
            comment="Second comment",
        )

    def comments_url(self, message):
        return reverse(
            "api:comments",
            kwargs={"message_id": message.pk},
        )

    def comment_url(self, comment):
        return reverse(
            "api:comment",
            kwargs={"pk": comment.pk},
        )

    # ------------------------------------------------------------------
    # View configuration
    # ------------------------------------------------------------------

    def test_serializer_class(self):
        assert CommentApiView.serializer_class is CommentSerializer

    def test_permission_classes(self):
        assert CommentApiView.permission_classes == [
            IsAuthenticated,
            AuthorDeletePermission,
        ]

    def test_detail_serializer_class(self):
        assert CommentDetailApiView.serializer_class is CommentSerializer

    def test_detail_permission_classes(self):
        assert CommentDetailApiView.permission_classes == [
            IsAuthenticated,
            AuthorDeletePermission,
        ]

    def test_detail_queryset_model(self):
        assert CommentDetailApiView.queryset.model is Comment

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_list_requires_authentication(
        self,
        api_client,
        message,
    ):
        response = api_client.get(self.comments_url(message))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_requires_authentication(
        self,
        api_client,
        message,
    ):
        response = api_client.post(
            self.comments_url(message),
            {"comment": "Anonymous comment"},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ------------------------------------------------------------------
    # Queryset
    # ------------------------------------------------------------------

    def test_get_queryset_returns_comments_for_message(
        self,
        api_client,
        test_user,
        message,
        comment,
        comment_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(self.comments_url(message))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        comment_ids = {item["id"] for item in response.data}

        assert comment.pk in comment_ids
        assert comment_2.pk in comment_ids

    def test_get_queryset_does_not_return_comments_from_other_message(
        self,
        api_client,
        test_user,
        message,
        message_2,
        comment,
    ):
        other_comment = Comment.objects.create(
            content_object=message_2,
            author=test_user,
            comment="Other message comment",
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(self.comments_url(message))

        assert response.status_code == status.HTTP_200_OK

        comment_ids = {item["id"] for item in response.data}

        assert comment.pk in comment_ids
        assert other_comment.pk not in comment_ids

    def test_get_queryset_returns_empty_list(
        self,
        api_client,
        test_user,
        message,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(self.comments_url(message))

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_nonexistent_message_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            reverse(
                "api:comments",
                kwargs={"message_id": 999999},
            )
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_create_comment(
        self,
        api_client,
        test_user,
        message,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.comments_url(message),
            {
                "comment": "New comment",
                "object_id": message.pk,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        comment = Comment.objects.get(
            pk=response.data["id"],
        )

        assert comment.content_object == message
        assert comment.author == test_user
        assert comment.comment == "New comment"

    def test_create_comment_assigns_authenticated_user(
        self,
        api_client,
        test_user,
        test_user_2,
        message,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.comments_url(message),
            {
                "comment": "Authenticated user's comment",
                "object_id": message.pk,
                "author": {
                    "username": test_user_2.username,
                },
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        comment = Comment.objects.get(
            pk=response.data["id"],
        )

        assert comment.author == test_user
        assert comment.author != test_user_2

    def test_create_comment_for_nonexistent_message(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.comments_url(
                type(
                    "MessageReference",
                    (),
                    {"pk": 999999},
                )()
            ),
            {
                "comment": "Invalid object",
                "object_id": 999999,
            },
            format="json",
        )

        assert response.status_code in {
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND,
        }

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def test_retrieve_comment(
        self,
        api_client,
        test_user,
        comment,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            self.comment_url(comment),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == comment.pk
        assert response.data["comment"] == comment.comment

    def test_retrieve_nonexistent_comment_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            reverse(
                "api:comment",
                kwargs={"pk": 999999},
            )
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def test_author_can_delete_comment(
        self,
        api_client,
        test_user,
        comment,
    ):
        api_client.force_authenticate(user=test_user)

        comment_id = comment.pk

        response = api_client.delete(
            self.comment_url(comment),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Comment.objects.filter(pk=comment_id).exists()

    def test_non_author_cannot_delete_comment(
        self,
        api_client,
        test_user_2,
        comment,
    ):
        api_client.force_authenticate(user=test_user_2)

        response = api_client.delete(
            self.comment_url(comment),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Comment.objects.filter(pk=comment.pk).exists()

    def test_unauthenticated_user_cannot_delete_comment(
        self,
        api_client,
        comment,
    ):
        response = api_client.delete(
            self.comment_url(comment),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_nonexistent_comment_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            reverse(
                "api:comment",
                kwargs={"pk": 999999},
            )
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestLikeCommentApiView:
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
    def message(self, test_user):
        return Message.objects.create(
            user=test_user,
            text="Test post",
        )

    @pytest.fixture
    def comment(self, message, test_user):
        return Comment.objects.create(
            content_object=message,
            author=test_user,
            comment="Test comment",
        )

    @pytest.fixture
    def comment_2(self, message, test_user_2):
        return Comment.objects.create(
            content_object=message,
            author=test_user_2,
            comment="Second comment",
        )

    @pytest.fixture
    def like_comment(
        self,
        test_user,
        comment,
    ):
        return LikeComment.objects.create(
            user=test_user,
            comment=comment,
        )

    def likes_url(self):
        return reverse("api:comments-likes")

    def like_detail_url(self, like_comment):
        return reverse(
            "api:comment-likes",
            kwargs={"pk": like_comment.pk},
        )

    # ------------------------------------------------------------------
    # View configuration
    # ------------------------------------------------------------------

    def test_serializer_class(self):
        assert LikeCommentApiView.serializer_class is LikeCommentSerializer

    def test_permission_classes(self):
        assert LikeCommentApiView.permission_classes == [
            IsAuthenticated,
        ]

    def test_queryset_model(self):
        assert LikeCommentApiView.queryset.model is LikeComment

    def test_detail_serializer_class(self):
        assert LikeCommentDetailApiView.serializer_class is LikeCommentSerializer

    def test_detail_permission_classes(self):
        assert LikeCommentDetailApiView.permission_classes == [
            IsAuthenticated,
            AuthorDeletePermission,
        ]

    def test_detail_queryset_model(self):
        assert LikeCommentDetailApiView.queryset.model is LikeComment

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_list_requires_authentication(
        self,
        api_client,
    ):
        response = api_client.get(self.likes_url())

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_requires_authentication(
        self,
        api_client,
        comment,
    ):
        response = api_client.post(
            self.likes_url(),
            {
                "comment": comment.pk,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_requires_authentication(
        self,
        api_client,
        like_comment,
    ):
        response = api_client.get(
            self.like_detail_url(like_comment),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_requires_authentication(
        self,
        api_client,
        like_comment,
    ):
        response = api_client.delete(
            self.like_detail_url(like_comment),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def test_list_returns_all_comment_likes(
        self,
        api_client,
        test_user,
        like_comment,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(self.likes_url())

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == like_comment.pk

    def test_list_returns_empty_list(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(self.likes_url())

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_list_contains_likes_from_multiple_users(
        self,
        api_client,
        test_user,
        test_user_2,
        comment,
        comment_2,
    ):
        first_like = LikeComment.objects.create(
            user=test_user,
            comment=comment,
        )
        second_like = LikeComment.objects.create(
            user=test_user_2,
            comment=comment_2,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(self.likes_url())

        assert response.status_code == status.HTTP_200_OK

        like_ids = {item["id"] for item in response.data}

        assert first_like.pk in like_ids
        assert second_like.pk in like_ids

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_create_comment_like(
        self,
        api_client,
        test_user,
        comment,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.likes_url(),
            {
                "comment": comment.pk,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        like = LikeComment.objects.get(
            pk=response.data["id"],
        )

        assert like.user == test_user
        assert like.comment == comment

    def test_create_comment_like_ignores_submitted_user(
        self,
        api_client,
        test_user,
        test_user_2,
        comment,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.likes_url(),
            {
                "user": test_user_2.pk,
                "comment": comment.pk,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        like = LikeComment.objects.get(
            pk=response.data["id"],
        )

        assert like.user == test_user
        assert like.user != test_user_2

    def test_create_comment_like_for_nonexistent_comment(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            self.likes_url(),
            {
                "comment": 999999,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def test_retrieve_comment_like(
        self,
        api_client,
        test_user,
        like_comment,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            self.like_detail_url(like_comment),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == like_comment.pk
        assert response.data["user"] == test_user.pk
        assert response.data["comment"] == like_comment.comment.pk

    def test_retrieve_nonexistent_comment_like_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            reverse(
                "api:comment-likes",
                kwargs={"pk": 999999},
            )
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def test_like_author_can_delete_comment_like(
        self,
        api_client,
        test_user,
        like_comment,
    ):
        api_client.force_authenticate(user=test_user)

        like_id = like_comment.pk

        response = api_client.delete(
            self.like_detail_url(like_comment),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not LikeComment.objects.filter(pk=like_id).exists()

    def test_non_author_cannot_delete_comment_like(
        self,
        api_client,
        test_user_2,
        like_comment,
    ):
        api_client.force_authenticate(user=test_user_2)

        response = api_client.delete(
            self.like_detail_url(like_comment),
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert LikeComment.objects.filter(
            pk=like_comment.pk,
        ).exists()

    def test_unauthenticated_user_cannot_delete_comment_like(
        self,
        api_client,
        like_comment,
    ):
        response = api_client.delete(
            self.like_detail_url(like_comment),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_nonexistent_comment_like_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            reverse(
                "api:comment-likes",
                kwargs={"pk": 999999},
            )
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
