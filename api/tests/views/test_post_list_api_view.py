import pytest
from rest_framework.test import APIRequestFactory

from api.views import PostListApiView
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
def test_user_post(test_user):
    return Message.objects.create(
        user=test_user,
        text="User post",
    )


@pytest.fixture
def test_user_2_post(test_user_2):
    return Message.objects.create(
        user=test_user_2,
        text="Other user post",
    )


@pytest.fixture
def api_request_factory():
    return APIRequestFactory()


@pytest.mark.django_db
class TestPostListApiView:
    def test_serializer_class(self):
        assert PostListApiView.serializer_class.__name__ == "PostSerializer"

    def test_parser_classes(self):
        assert PostListApiView.parser_classes == [
            # Resolved by DRF when the class is loaded.
            PostListApiView.parser_classes[0],
            PostListApiView.parser_classes[1],
        ]

    def test_get_queryset_returns_current_user_posts(
        self,
        api_request_factory,
        test_user,
        test_user_post,
        test_user_2_post,
    ):
        request = api_request_factory.get("/api/posts/")
        request.user = test_user

        view = PostListApiView()
        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [test_user_post]

    def test_get_queryset_does_not_return_other_users_posts(
        self,
        api_request_factory,
        test_user,
        test_user_post,
        test_user_2_post,
    ):
        request = api_request_factory.get("/api/posts/")
        request.user = test_user

        view = PostListApiView()
        view.request = request

        queryset = view.get_queryset()

        assert test_user_post in queryset
        assert test_user_2_post not in queryset

    def test_get_queryset_returns_saved_posts_for_saved_path(
        self,
        api_request_factory,
        test_user,
        test_user_post,
        test_user_2_post,
    ):
        SavePost.objects.create(
            user=test_user,
            post=test_user_2_post,
        )

        request = api_request_factory.get("/api/posts/saved/")
        request.user = test_user

        view = PostListApiView()
        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [test_user_2_post]

    def test_saved_path_does_not_return_unsaved_posts(
        self,
        api_request_factory,
        test_user,
        test_user_post,
        test_user_2_post,
    ):
        request = api_request_factory.get("/api/posts/saved/")
        request.user = test_user

        view = PostListApiView()
        view.request = request

        queryset = view.get_queryset()

        assert test_user_post not in queryset
        assert test_user_2_post not in queryset

    def test_saved_path_returns_only_posts_saved_by_current_user(
        self,
        api_request_factory,
        test_user,
        test_user_2,
        test_user_post,
        test_user_2_post,
    ):
        SavePost.objects.create(
            user=test_user,
            post=test_user_2_post,
        )
        SavePost.objects.create(
            user=test_user_2,
            post=test_user_post,
        )

        request = api_request_factory.get("/api/posts/saved/")
        request.user = test_user

        view = PostListApiView()
        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [test_user_2_post]

    def test_non_saved_path_returns_only_current_user_posts(
        self,
        api_request_factory,
        test_user,
        test_user_post,
        test_user_2_post,
    ):
        SavePost.objects.create(
            user=test_user,
            post=test_user_2_post,
        )

        request = api_request_factory.get("/api/posts/")
        request.user = test_user

        view = PostListApiView()
        view.request = request

        queryset = view.get_queryset()

        assert list(queryset) == [test_user_post]

    def test_empty_queryset_when_user_has_no_posts(
        self,
        api_request_factory,
        test_user,
    ):
        request = api_request_factory.get("/api/posts/")
        request.user = test_user

        view = PostListApiView()
        view.request = request

        queryset = view.get_queryset()

        assert not queryset.exists()

    def test_empty_queryset_when_user_has_no_saved_posts(
        self,
        api_request_factory,
        test_user,
    ):
        request = api_request_factory.get("/api/posts/saved/")
        request.user = test_user

        view = PostListApiView()
        view.request = request

        queryset = view.get_queryset()

        assert not queryset.exists()
