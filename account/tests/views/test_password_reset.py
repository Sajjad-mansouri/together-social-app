import shutil
import tempfile
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.tokens import default_token_generator
from django.template.response import TemplateResponse
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from account.views import (
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def media_root():
    temp_dir = tempfile.mkdtemp()

    with override_settings(MEDIA_ROOT=temp_dir):
        yield

    shutil.rmtree(temp_dir)


@pytest.fixture
def test_user(django_user_model):
    return django_user_model.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
        is_active=True,
    )


@pytest.fixture
def test_user_2(django_user_model):
    return django_user_model.objects.create_user(
        username="test_user_2",
        email="test_user_2@example.com",
        password="test_password",
        is_active=True,
    )


class TestPasswordResetView:
    def test_view_configuration(self):
        view = PasswordResetView()

        assert view.template_name == ("registration/pass_reset_form.html")
        assert view.email_template_name == ("email/reset/pass_reset_email.txt")
        assert view.html_email_template_name == ("email/reset/pass_reset_email.html")
        assert view.subject_template_name == ("email/reset/pass_reset_subject.txt")
        assert view.success_url == reverse(
            "account:password_reset_done",
        )

    def test_get_renders_password_reset_page(self, client):
        response = client.get(
            reverse("account:password_reset"),
        )

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/pass_reset_form.html",
        ]
        assert "form" in response.context

    def test_get_uses_password_reset_form(self, client):
        response = client.get(
            reverse("account:password_reset"),
        )

        assert isinstance(
            response.context["form"],
            auth_views.PasswordResetView.form_class,
        )

    def test_form_valid_stores_email_in_session(
        self,
        client,
        test_user,
    ):
        response = client.post(
            reverse("account:password_reset"),
            {
                "email": test_user.email,
            },
        )

        assert response.status_code == 302
        assert response.url == reverse(
            "account:password_reset_done",
        )
        assert client.session["email"] == test_user.email

    def test_form_valid_passes_expected_context_to_parent(
        self,
        client,
        test_user,
        settings,
    ):
        settings.DEVELOPER_NAME = "Test Developer"

        request = RequestFactory().post(
            reverse("account:password_reset"),
        )
        request.session = client.session

        view = PasswordResetView()
        view.setup(request)

        form = type(
            "TestForm",
            (),
            {
                "cleaned_data": {
                    "email": test_user.email,
                },
            },
        )()

        with patch.object(
            auth_views.PasswordResetView,
            "form_valid",
            return_value="parent-response",
        ) as parent_form_valid:
            response = view.form_valid(form)

        assert response == "parent-response"

        assert request.session["email"] == test_user.email

        parent_form_valid.assert_called_once_with(form)

        assert view.extra_email_context == {
            "developer_name": "Test Developer",
            "logo_url": request.build_absolute_uri(
                "/static/images/logo_transparent.png",
            ),
        }

    def test_form_valid_uses_submitted_email(
        self,
        client,
        settings,
    ):
        settings.DEVELOPER_NAME = "Test Developer"

        submitted_email = "submitted@example.com"

        request = RequestFactory().post(
            reverse("account:password_reset"),
        )
        request.session = client.session

        view = PasswordResetView()
        view.setup(request)

        form = type(
            "TestForm",
            (),
            {
                "cleaned_data": {
                    "email": submitted_email,
                },
            },
        )()

        with patch.object(
            auth_views.PasswordResetView,
            "form_valid",
            return_value="parent-response",
        ):
            response = view.form_valid(form)

        assert response == "parent-response"
        assert request.session["email"] == submitted_email

    def test_valid_password_reset_request_sends_email(
        self,
        client,
        test_user,
        mailoutbox,
    ):
        response = client.post(
            reverse("account:password_reset"),
            {
                "email": test_user.email,
            },
        )

        assert response.status_code == 302
        assert response.url == reverse(
            "account:password_reset_done",
        )

        assert len(mailoutbox) == 1
        assert test_user.email in mailoutbox[0].to

    def test_unknown_email_does_not_reveal_user_existence(
        self,
        client,
        mailoutbox,
    ):
        response = client.post(
            reverse("account:password_reset"),
            {
                "email": "unknown@example.com",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse(
            "account:password_reset_done",
        )
        assert len(mailoutbox) == 0

    def test_invalid_email_does_not_submit_form(
        self,
        client,
        mailoutbox,
    ):
        response = client.post(
            reverse("account:password_reset"),
            {
                "email": "invalid-email",
            },
        )

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/pass_reset_form.html",
        ]
        assert response.context["form"].errors
        assert len(mailoutbox) == 0


class TestPasswordResetDoneView:
    def test_view_configuration(self):
        view = PasswordResetDoneView()

        assert view.template_name == ("registration/pass_reset_done.html")

    def test_get_renders_password_reset_done_page(self, client):
        response = client.get(
            reverse("account:password_reset_done"),
        )

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/pass_reset_done.html",
        ]

    def test_context_contains_email_from_session(self, client):
        session = client.session
        session["email"] = "test_user@example.com"
        session.save()

        response = client.get(
            reverse("account:password_reset_done"),
        )

        assert response.context["email"] == "test_user@example.com"

    def test_context_contains_none_without_session_email(
        self,
        client,
    ):
        response = client.get(
            reverse("account:password_reset_done"),
        )

        assert response.context["email"] is None

    def test_session_email_is_not_modified(self, client):
        session = client.session
        session["email"] = "test_user@example.com"
        session.save()

        response = client.get(
            reverse("account:password_reset_done"),
        )

        assert response.status_code == 200
        assert client.session["email"] == "test_user@example.com"


class TestPasswordResetConfirmView:
    def test_view_configuration(self):
        view = PasswordResetConfirmView()

        assert view.template_name == ("registration/pass_reset_confirm.html")
        assert view.success_url == reverse(
            "account:password_reset_complete",
        )

    def test_invalid_token_renders_invalid_link_page(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": "invalid-token",
                },
            ),
        )

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/pass_reset_confirm.html",
        ]
        assert response.context["validlink"] is False

    def test_valid_token_redirects_to_set_password_url(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(
            test_user,
        )

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            ),
        )

        assert response.status_code == 302
        assert response.url.endswith("/set-password/")

    def test_valid_token_stores_token_in_session(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(
            test_user,
        )

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            ),
        )

        assert response.status_code == 302
        assert (
            client.session.get(
                "_password_reset_token",
            )
            == token
        )

    def test_set_password_page_renders_after_valid_token(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(
            test_user,
        )

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            ),
        )

        assert response.status_code == 302

        response = client.get(response.url)

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/pass_reset_confirm.html",
        ]
        assert response.context["validlink"] is True
        assert "form" in response.context

    def test_valid_token_allows_password_change(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(
            test_user,
        )

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            ),
        )

        assert response.status_code == 302

        response = client.post(
            response.url,
            {
                "new_password1": "new_test_password",
                "new_password2": "new_test_password",
            },
        )

        assert response.status_code == 302
        assert response.url == reverse(
            "account:password_reset_complete",
        )

        test_user.refresh_from_db()

        assert test_user.check_password(
            "new_test_password",
        )

    def test_password_mismatch_does_not_change_password(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(
            test_user,
        )

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            ),
        )

        assert response.status_code == 302

        response = client.post(
            response.url,
            {
                "new_password1": "new_test_password",
                "new_password2": "different_password",
            },
        )

        assert response.status_code == 200
        assert response.context["form"].errors

        test_user.refresh_from_db()

        assert test_user.check_password(
            "test_password",
        )

    def test_token_becomes_invalid_after_password_change(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(
            test_user,
        )

        test_user.set_password("changed_password")
        test_user.save()

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": token,
                },
            ),
        )

        assert response.status_code == 200
        assert response.context["validlink"] is False

    def test_unknown_user_token_is_invalid(self, client):
        uidb64 = urlsafe_base64_encode(
            force_bytes(999999999),
        )

        response = client.get(
            reverse(
                "account:password_reset_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": "token",
                },
            ),
        )

        assert response.status_code == 200
        assert response.context["validlink"] is False


class TestPasswordResetCompleteView:
    def test_view_configuration(self):
        view = PasswordResetCompleteView()

        assert view.template_name == ("registration/pass_reset_complete.html")

    def test_get_renders_password_reset_complete_page(self, client):
        response = client.get(
            reverse("account:password_reset_complete"),
        )

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/pass_reset_complete.html",
        ]
