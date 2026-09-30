import json

import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory
from django.urls import reverse

from account.models import AboutSite, Block, Contact
from social.models import Message, Report
from social.views import Home


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
def test_user_3(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser3",
        email="test3@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_admin(db, django_user_model):
    return django_user_model.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
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
        text="Second test message",
    )


@pytest.fixture
def test_message_3(test_user_3):
    return Message.objects.create(
        user=test_user_3,
        text="Third test message",
    )


@pytest.fixture
def message_content_type():
    return ContentType.objects.get_for_model(Message)


@pytest.fixture
def test_report(
    test_user,
    test_message_2,
    message_content_type,
):
    return Report.objects.create(
        user=test_user,
        content_type=message_content_type,
        object_id=test_message_2.pk,
    )


@pytest.fixture
def home_view_request(test_user):
    request = RequestFactory().get(reverse("social:home"))
    request.user = test_user
    return request


@pytest.fixture
def home_view(home_view_request):
    view = Home()
    view.setup(home_view_request)
    return view


@pytest.mark.django_db
class TestHome:
    def test_template_name(self):
        assert Home.template_name == "together/home.html"

    def test_url_name(self):
        assert reverse("social:home")

    def test_authenticated_user_get_uses_home_view(
        self,
        client,
        test_user,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse("social:home"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 200

    def test_unauthenticated_user_get_redirects_or_renders_login_page(
        self,
        client,
        test_admin,
    ):
        response = client.get(reverse("social:home"))

        assert response.status_code == 200
        assert response.context["admin"] == test_admin

    def test_unauthenticated_user_receives_admin(
        self,
        client,
        test_admin,
    ):
        response = client.get(reverse("social:home"))

        assert response.context["admin"] == test_admin

    def test_unauthenticated_user_receives_descriptions_as_json(
        self,
        client,
        test_admin,
    ):
        AboutSite.objects.create(text="First description")
        AboutSite.objects.create(text="Second description")

        response = client.get(reverse("social:home"))

        assert response.context["descriptions"] == json.dumps(
            [
                "First description",
                "Second description",
            ]
        )

    def test_unauthenticated_user_receives_first_admin(
        self,
        client,
        django_user_model,
        test_admin,
    ):
        second_admin = django_user_model.objects.create_superuser(
            username="admin2",
            email="admin2@example.com",
            password="adminpass123",
        )

        response = client.get(reverse("social:home"))

        assert response.context["admin"] == test_admin
        assert response.context["admin"] != second_admin

    def test_queryset_contains_own_messages(
        self,
        home_view,
        test_message,
    ):
        queryset = home_view.get_queryset()

        assert test_message in queryset

    def test_queryset_contains_messages_from_followed_users(
        self,
        home_view,
        test_user,
        test_user_2,
        test_message_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 in queryset

    def test_queryset_excludes_messages_from_unfollowed_users(
        self,
        home_view,
        test_message_2,
    ):
        queryset = home_view.get_queryset()

        assert test_message_2 not in queryset

    def test_queryset_excludes_messages_from_inactive_follow(
        self,
        home_view,
        test_user,
        test_user_2,
        test_message_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 not in queryset

    def test_queryset_contains_messages_from_multiple_followed_users(
        self,
        home_view,
        test_user,
        test_user_2,
        test_user_3,
        test_message_2,
        test_message_3,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_3,
            access=True,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 in queryset
        assert test_message_3 in queryset

    def test_queryset_excludes_reported_messages(
        self,
        home_view,
        test_user,
        test_user_2,
        test_message_2,
        test_report,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 not in queryset

    def test_queryset_does_not_exclude_unreported_messages(
        self,
        home_view,
        test_user,
        test_user_2,
        test_message_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 in queryset

    def test_queryset_excludes_message_reported_by_another_user(
        self,
        home_view,
        test_user,
        test_user_2,
        test_user_3,
        test_message_2,
        message_content_type,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        Report.objects.create(
            user=test_user_3,
            content_type=message_content_type,
            object_id=test_message_2.pk,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 not in queryset

    def test_queryset_excludes_messages_from_blocked_users(
        self,
        home_view,
        test_user,
        test_user_2,
        test_message_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        Block.objects.create(
            from_user=test_user_2,
            to_user=test_user,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 not in queryset

    def test_queryset_keeps_messages_from_users_who_have_not_blocked_current_user(
        self,
        home_view,
        test_user,
        test_user_2,
        test_message_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 in queryset

    def test_queryset_keeps_own_message_without_following_self(
        self,
        home_view,
        test_message,
    ):
        queryset = home_view.get_queryset()

        assert test_message in queryset

    def test_queryset_returns_own_and_followed_messages(
        self,
        home_view,
        test_user,
        test_user_2,
        test_message,
        test_message_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        queryset = home_view.get_queryset()

        assert test_message in queryset
        assert test_message_2 in queryset

    def test_queryset_excludes_blocked_user_but_keeps_other_followed_user(
        self,
        home_view,
        test_user,
        test_user_2,
        test_user_3,
        test_message,
        test_message_2,
        test_message_3,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_3,
            access=True,
        )

        Block.objects.create(
            from_user=test_user_2,
            to_user=test_user,
        )

        queryset = home_view.get_queryset()

        assert test_message in queryset
        assert test_message_2 not in queryset
        assert test_message_3 in queryset

    def test_queryset_excludes_reported_message_but_keeps_other_message(
        self,
        home_view,
        test_user,
        test_user_2,
        test_user_3,
        test_message_2,
        test_message_3,
        message_content_type,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_3,
            access=True,
        )

        Report.objects.create(
            user=test_user_3,
            content_type=message_content_type,
            object_id=test_message_2.pk,
        )

        queryset = home_view.get_queryset()

        assert test_message_2 not in queryset
        assert test_message_3 in queryset

    def test_queryset_applies_all_home_rules(
        self,
        home_view,
        test_user,
        test_user_2,
        test_user_3,
        test_message,
        test_message_2,
        test_message_3,
        message_content_type,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_3,
            access=True,
        )

        Block.objects.create(
            from_user=test_user_3,
            to_user=test_user,
        )

        Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message_2.pk,
        )

        queryset = home_view.get_queryset()

        assert test_message in queryset
        assert test_message_2 not in queryset
        assert test_message_3 not in queryset
