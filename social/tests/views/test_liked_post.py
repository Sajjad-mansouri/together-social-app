import pytest
from django.test import RequestFactory
from django.urls import reverse

from social.models import Like, Message
from social.views import LikedPost


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
        text="First test message",
    )


@pytest.fixture
def test_message_2(test_user):
    return Message.objects.create(
        user=test_user,
        text="Second test message",
    )


@pytest.fixture
def test_message_3(test_user_2):
    return Message.objects.create(
        user=test_user_2,
        text="Third test message",
    )


@pytest.fixture
def liked_post_request(test_user):
    request = RequestFactory().get("/liked-post/")
    request.user = test_user
    return request


@pytest.fixture
def liked_post_view(liked_post_request):
    view = LikedPost()
    view.setup(liked_post_request)
    return view


@pytest.mark.django_db
class TestLikedPost:
    def test_template_name(self):
        assert LikedPost.template_name == "together/home.html"

    def test_get_queryset_returns_liked_post(
        self,
        liked_post_view,
        test_user,
        test_message,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )

        queryset = liked_post_view.get_queryset()

        assert list(queryset) == [test_message]

    def test_get_queryset_returns_multiple_liked_posts(
        self,
        liked_post_view,
        test_user,
        test_message,
        test_message_2,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )
        Like.objects.create(
            user=test_user,
            post=test_message_2,
        )

        queryset = liked_post_view.get_queryset()

        assert set(queryset) == {
            test_message,
            test_message_2,
        }

    def test_get_queryset_excludes_unliked_posts(
        self,
        liked_post_view,
        test_user,
        test_message,
        test_message_2,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )

        queryset = liked_post_view.get_queryset()

        assert test_message in queryset
        assert test_message_2 not in queryset

    def test_get_queryset_excludes_posts_liked_by_another_user(
        self,
        liked_post_view,
        test_user_2,
        test_message,
    ):
        Like.objects.create(
            user=test_user_2,
            post=test_message,
        )

        queryset = liked_post_view.get_queryset()

        assert test_message not in queryset

    def test_get_queryset_uses_request_user(
        self,
        liked_post_request,
        test_user,
        test_user_2,
        test_message,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )

        liked_post_request.user = test_user_2

        view = LikedPost()
        view.setup(liked_post_request)

        queryset = view.get_queryset()

        assert not queryset.exists()

    def test_get_queryset_includes_posts_from_different_authors(
        self,
        liked_post_view,
        test_user,
        test_message,
        test_message_3,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )
        Like.objects.create(
            user=test_user,
            post=test_message_3,
        )

        queryset = liked_post_view.get_queryset()

        assert set(queryset) == {
            test_message,
            test_message_3,
        }

    def test_get_queryset_returns_empty_queryset_when_user_has_no_likes(
        self,
        liked_post_view,
    ):
        queryset = liked_post_view.get_queryset()

        assert not queryset.exists()

    def test_get_queryset_returns_correct_number_of_posts(
        self,
        liked_post_view,
        test_user,
        test_message,
        test_message_2,
        test_message_3,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )
        Like.objects.create(
            user=test_user,
            post=test_message_2,
        )
        Like.objects.create(
            user=test_user,
            post=test_message_3,
        )

        queryset = liked_post_view.get_queryset()

        assert queryset.count() == 3

    def test_get_queryset_does_not_duplicate_posts(
        self,
        liked_post_view,
        test_user,
        test_user_2,
        test_message,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )
        Like.objects.create(
            user=test_user_2,
            post=test_message,
        )

        queryset = liked_post_view.get_queryset()

        assert queryset.count() == 1

    def test_authenticated_user_can_access_liked_posts(
        self,
        client,
        test_user,
        monkeypatch,
    ):
        client.force_login(test_user)

        def fake_render(request, template_name, context=None, *args, **kwargs):
            from django.http import HttpResponse

            return HttpResponse("OK")

        monkeypatch.setattr(
            "django.views.generic.list.TemplateResponseMixin.render_to_response",
            fake_render,
        )

        response = client.get(
            reverse("social:liked_post"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 200

    def test_authenticated_user_uses_liked_post_template(
        self,
    ):
        assert LikedPost.template_name == "together/home.html"

    def test_authenticated_response_contains_liked_posts(
        self,
        client,
        test_user,
        test_message,
        test_message_2,
        monkeypatch,
    ):
        Like.objects.create(
            user=test_user,
            post=test_message,
        )

        client.force_login(test_user)

        original_get_queryset = LikedPost.get_queryset

        captured_queryset = {}

        def get_queryset(view):
            queryset = original_get_queryset(view)
            captured_queryset["queryset"] = queryset
            return queryset

        monkeypatch.setattr(
            LikedPost,
            "get_queryset",
            get_queryset,
        )

        def fake_render_to_response(self, context, **response_kwargs):
            from django.http import HttpResponse

            return HttpResponse("OK")

        monkeypatch.setattr(
            LikedPost,
            "render_to_response",
            fake_render_to_response,
        )

        response = client.get(
            reverse("social:liked_post"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 200
        assert captured_queryset["queryset"].filter(pk=test_message.pk).exists()
        assert not captured_queryset["queryset"].filter(pk=test_message_2.pk).exists()

    def test_unauthenticated_user_is_redirected(
        self,
        client,
    ):
        response = client.get(
            reverse("social:liked_post"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 302

    def test_unauthenticated_user_redirect_preserves_requested_url(
        self,
        client,
    ):
        response = client.get(
            reverse("social:liked_post"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 302
        assert reverse("social:liked_post") in response.url
