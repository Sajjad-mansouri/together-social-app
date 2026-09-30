import pytest
from django.test import RequestFactory
from django.urls import reverse

from social.views import Setting


@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def setting_request(test_user):
    request = RequestFactory().get("/settings/")
    request.user = test_user
    return request


@pytest.fixture
def setting_view(setting_request):
    view = Setting()
    view.setup(setting_request)
    return view


@pytest.mark.django_db
class TestSetting:
    def test_template_name(self):
        assert Setting.template_name == "together/settings.html"

    def test_get_context_data_sets_owner_to_authenticated_user(
        self,
        setting_view,
        test_user,
    ):
        context = setting_view.get_context_data()

        assert context["owner"] == test_user

    def test_get_context_data_preserves_extra_context(
        self,
        setting_view,
        test_user,
    ):
        context = setting_view.get_context_data(example="value")

        assert context["example"] == "value"
        assert context["owner"] == test_user

    def test_authenticated_user_can_access_settings(
        self,
        client,
        test_user,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse("social:setting"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 200

    def test_authenticated_user_uses_settings_template(
        self,
        client,
        test_user,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse("social:setting"),
            HTTP_USER_AGENT="pytest",
        )

        assert "together/settings.html" in [
            template.name for template in response.templates if template.name
        ]

    def test_authenticated_user_is_available_as_owner_in_template_context(
        self,
        client,
        test_user,
    ):
        client.force_login(test_user)

        response = client.get(
            reverse("social:setting"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.context["owner"] == test_user

    def test_unauthenticated_user_is_redirected(
        self,
        client,
    ):
        response = client.get(
            reverse("social:setting"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 302

    def test_unauthenticated_user_does_not_access_settings_template(
        self,
        client,
    ):
        response = client.get(
            reverse("social:setting"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 302

        assert "together/settings.html" not in response.content.decode()

    def test_login_redirect_contains_requested_settings_path(
        self,
        client,
    ):
        response = client.get(
            reverse("social:setting"),
            HTTP_USER_AGENT="pytest",
        )

        assert response.status_code == 302

        expected_path = reverse("social:setting")
        assert expected_path in response.url
