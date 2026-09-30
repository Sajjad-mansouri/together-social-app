import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ImproperlyConfigured
from django.template.response import TemplateResponse
from django.test import RequestFactory, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.generic import TemplateView

from account.forms import CustomCreationForm
from account.models import Profile
from account.views import (
    INTERNAL_REGISTRATION_SESSION_TOKEN,
    PasswordContextMixin,
    RegistrationConfirmView,
    RegistrationDoneView,
    RegistrationView,
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
        is_active=False,
    )


@pytest.fixture
def test_user_2(django_user_model):
    return django_user_model.objects.create_user(
        username="test_user_2",
        email="test_user_2@example.com",
        password="test_password",
        is_active=False,
    )


@pytest.fixture
def test_admin(django_user_model):
    return django_user_model.objects.create_superuser(
        username="test_admin",
        email="test_admin@example.com",
        password="test_password",
    )


class PasswordContextTestView(PasswordContextMixin, TemplateView):
    """Minimal concrete view for testing PasswordContextMixin independently."""

    title = "Test title"
    template_name = "registration/test.html"


class TestPasswordContextMixin:
    def test_get_context_data_adds_title_and_none_subtitle(self):
        request = RequestFactory().get("/")
        view = PasswordContextTestView()
        view.setup(request)

        context = view.get_context_data()

        assert context["title"] == "Test title"
        assert context["subtitle"] is None

    def test_get_context_data_preserves_existing_context(self):
        request = RequestFactory().get("/")
        view = PasswordContextTestView()
        view.setup(request)

        context = view.get_context_data(
            existing_value="test_value",
        )

        assert context["existing_value"] == "test_value"

    def test_extra_context_is_added(self):
        request = RequestFactory().get("/")
        view = PasswordContextTestView()
        view.extra_context = {
            "custom_title": "Custom title",
            "custom_value": "Custom value",
        }
        view.setup(request)

        context = view.get_context_data()

        assert context["custom_title"] == "Custom title"
        assert context["custom_value"] == "Custom value"

    def test_extra_context_can_override_default_context_values(self):
        request = RequestFactory().get("/")
        view = PasswordContextTestView()
        view.extra_context = {
            "title": "Overridden title",
            "subtitle": "Overridden subtitle",
        }
        view.setup(request)

        context = view.get_context_data()

        assert context["title"] == "Overridden title"
        assert context["subtitle"] == "Overridden subtitle"

    def test_none_extra_context_does_not_change_context(self):
        request = RequestFactory().get("/")
        view = PasswordContextTestView()
        view.extra_context = None
        view.setup(request)

        context = view.get_context_data()

        assert context["title"] == "Test title"
        assert context["subtitle"] is None


class TestRegistrationView:
    def test_view_configuration(self):
        view = RegistrationView()

        assert view.model is UserModel
        assert view.form_class is CustomCreationForm
        assert view.template_name == "registration/register.html"
        assert view.success_url == reverse(
            "account:registration_done",
        )
        assert view.title == "Register"

        assert view.email_template_name == "email/registration/registration_email.txt"
        assert (
            view.html_email_template_name
            == "email/registration/registration_email.html"
        )
        assert (
            view.subject_template_name == "email/registration/registration_subject.txt"
        )

        assert view.from_email is None
        assert view.extra_email_context is None
        assert view.token_generator is default_token_generator

    def test_get_renders_registration_page(self, client):
        url = reverse("account:register")

        response = client.get(url)

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/register.html",
        ]
        assert "form" in response.context

    def test_get_uses_registration_form(self, client):
        url = reverse("account:register")

        response = client.get(url)

        assert isinstance(
            response.context["form"],
            CustomCreationForm,
        )

    def test_form_valid_saves_user_and_redirects(
        self,
        client,
        test_user,
    ):
        url = reverse("account:register")

        with patch(
            "account.views.CustomCreationForm.save",
            return_value=test_user,
        ) as save_mock:
            response = client.post(
                url,
                {
                    "username": "submitted_user",
                    "email": "submitted@example.com",
                    "password1": "test_password",
                    "password2": "test_password",
                },
            )

        assert response.status_code == 302
        assert response.url == reverse(
            "account:registration_done",
        )

        save_mock.assert_called_once()

        options = save_mock.call_args.kwargs

        assert options["use_https"] is False
        assert options["token_generator"] is default_token_generator
        assert options["from_email"] is None
        assert (
            options["email_template_name"]
            == "email/registration/registration_email.txt"
        )
        assert (
            options["subject_template_name"]
            == "email/registration/registration_subject.txt"
        )
        assert options["request"] is not None
        assert (
            options["html_email_template_name"]
            == "email/registration/registration_email.html"
        )
        assert options["extra_email_context"] is None

    def test_form_valid_uses_https_for_secure_request(
        self,
        client,
        test_user,
    ):
        url = reverse("account:register")

        with patch(
            "account.views.CustomCreationForm.save",
            return_value=test_user,
        ) as save_mock:
            response = client.post(
                url,
                {
                    "username": "submitted_user",
                    "email": "submitted@example.com",
                    "password1": "test_password",
                    "password2": "test_password",
                },
                secure=True,
            )

        assert response.status_code == 302
        assert response.url == reverse(
            "account:registration_done",
        )
        assert save_mock.call_args.kwargs["use_https"] is True

    def test_form_valid_passes_custom_view_options_to_form_save(
        self,
        client,
        test_user,
    ):
        custom_token_generator = object()
        custom_context = {"source": "registration"}

        request = RequestFactory().post(
            reverse("account:register"),
        )

        session = client.session
        request.session = session

        view = RegistrationView()
        view.setup(request)
        view.token_generator = custom_token_generator
        view.from_email = "noreply@example.com"
        view.extra_email_context = custom_context

        form = MagicMock()
        form.save.return_value = test_user

        with patch(
            "account.views.messages.success",
        ) as success_mock:
            response = view.form_valid(form)

        assert response.status_code == 302
        assert response.url == reverse("account:registration_done")

        form.save.assert_called_once_with(
            use_https=False,
            token_generator=custom_token_generator,
            from_email="noreply@example.com",
            email_template_name=("email/registration/registration_email.txt"),
            subject_template_name=("email/registration/registration_subject.txt"),
            request=request,
            html_email_template_name=("email/registration/registration_email.html"),
            extra_email_context=custom_context,
        )

        assert request.session["email"] == test_user.email
        success_mock.assert_called_once_with(
            request,
            "Signed up successfully! Please confirm your email.",
        )

    def test_form_valid_stores_user_email_in_session(
        self,
        client,
        test_user,
    ):
        url = reverse("account:register")

        with patch(
            "account.views.CustomCreationForm.save",
            return_value=test_user,
        ):
            response = client.post(
                url,
                {
                    "username": "submitted_user",
                    "email": "submitted@example.com",
                    "password1": "test_password",
                    "password2": "test_password",
                },
            )

        assert response.status_code == 302
        assert client.session["email"] == test_user.email

    def test_form_valid_adds_success_message(
        self,
        client,
        test_user,
    ):
        url = reverse("account:register")

        with patch(
            "account.views.CustomCreationForm.save",
            return_value=test_user,
        ):
            response = client.post(
                url,
                {
                    "username": "submitted_user",
                    "email": "submitted@example.com",
                    "password1": "test_password",
                    "password2": "test_password",
                },
            )

        stored_messages = list(
            messages.get_messages(response.wsgi_request),
        )

        assert len(stored_messages) == 1
        assert stored_messages[0].level == messages.SUCCESS
        assert (
            str(stored_messages[0])
            == "Signed up successfully! Please confirm your email."
        )

    def test_invalid_form_does_not_save_or_redirect(self, client):
        url = reverse("account:register")

        with patch(
            "account.views.CustomCreationForm.save",
        ) as save_mock:
            response = client.post(
                url,
                {
                    "username": "",
                    "email": "invalid-email",
                    "password1": "test_password",
                    "password2": "different_password",
                },
            )

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/register.html",
        ]
        assert response.context["form"].errors

        save_mock.assert_not_called()

    def test_form_valid_returns_http_redirect_response(
        self,
        client,
        test_user,
    ):
        url = reverse("account:register")

        with patch(
            "account.views.CustomCreationForm.save",
            return_value=test_user,
        ):
            response = client.post(
                url,
                {
                    "username": "submitted_user",
                    "email": "submitted@example.com",
                    "password1": "test_password",
                    "password2": "test_password",
                },
            )

        assert response.status_code == 302
        assert response.url == reverse(
            "account:registration_done",
        )


class TestRegistrationDoneView:
    def test_view_configuration(self):
        view = RegistrationDoneView()

        assert view.template_name == ("registration/registration_done.html")
        assert view.title == "Activition Email sent"

    def test_get_renders_registration_done_page(self, client):
        url = reverse("account:registration_done")

        response = client.get(url)

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/registration_done.html",
        ]

    def test_context_contains_email_from_session(self, client):
        session = client.session
        session["email"] = "test_user@example.com"
        session.save()

        response = client.get(
            reverse("account:registration_done"),
        )

        assert response.context["email"] == "test_user@example.com"

    def test_context_contains_none_when_session_email_is_missing(
        self,
        client,
    ):
        response = client.get(
            reverse("account:registration_done"),
        )

        assert response.context["email"] is None

    def test_context_contains_password_context_values(self, client):
        response = client.get(
            reverse("account:registration_done"),
        )

        assert response.context["title"] == "Activition Email sent"
        assert response.context["subtitle"] is None

    def test_session_email_is_not_modified(self, client):
        session = client.session
        session["email"] = "test_user@example.com"
        session.save()

        response = client.get(
            reverse("account:registration_done"),
        )

        assert response.status_code == 200
        assert client.session["email"] == "test_user@example.com"


class TestRegistrationConfirmView:
    def test_view_configuration(self):
        view = RegistrationConfirmView()

        assert view.template_name == ("registration/registration_complete.html")
        assert view.confirm_registration_url_token == ("confirmation-done")
        assert view.token_generator is default_token_generator

    def test_get_user_returns_matching_user(self, test_user):
        view = RegistrationConfirmView()

        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )

        result = view.get_user(uidb64)

        assert result == test_user

    def test_get_user_returns_none_for_unknown_user(self):
        view = RegistrationConfirmView()

        uidb64 = urlsafe_base64_encode(
            force_bytes(999999999),
        )

        result = view.get_user(uidb64)

        assert result is None

    @pytest.mark.parametrize(
        "uidb64",
        [
            "",
            "invalid",
            "!!!",
            "not-a-valid-uid",
        ],
    )
    def test_get_user_returns_none_for_invalid_uid(self, uidb64):
        view = RegistrationConfirmView()

        result = view.get_user(uidb64)

        assert result is None

    def test_dispatch_requires_uidb64_parameter(self):
        request = RequestFactory().get("/")

        view = RegistrationConfirmView()

        with pytest.raises(
            ImproperlyConfigured,
            match=r"URL path must contain 'uidb64' and 'token' parameters",
        ):
            view.dispatch(
                request,
                token="token",
            )

    def test_dispatch_requires_token_parameter(
        self,
        test_user,
    ):
        request = RequestFactory().get("/")

        view = RegistrationConfirmView()

        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )

        with pytest.raises(
            ImproperlyConfigured,
            match=r"URL path must contain 'uidb64' and 'token' parameters",
        ):
            view.dispatch(
                request,
                uidb64=uidb64,
            )

    def test_invalid_token_renders_unsuccessful_page(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "invalid-token",
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert isinstance(response, TemplateResponse)
        assert response.template_name == [
            "registration/registration_complete.html",
        ]

        assert response.context["validlink"] is False
        assert response.context["form"] is None
        assert response.context["title"] == "Password reset unsuccessful"

        test_user.refresh_from_db()

        assert test_user.is_active is False

    def test_invalid_token_does_not_create_profile(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "invalid-token",
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert not Profile.objects.filter(
            user=test_user,
        ).exists()

    def test_valid_token_redirects_to_confirmation_done(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(url)

        assert response.status_code == 302

        expected_url = url.replace(
            token,
            "confirmation-done",
        )

        assert response.url == expected_url

    def test_valid_token_is_stored_in_session(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(url)

        assert response.status_code == 302
        assert client.session[INTERNAL_REGISTRATION_SESSION_TOKEN] == token

    def test_valid_token_does_not_activate_user_on_first_request(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(url)

        assert response.status_code == 302

        test_user.refresh_from_db()

        assert test_user.is_active is False

    def test_confirmation_done_with_valid_session_token_activates_user(
        self,
        client,
        test_user,
        test_admin,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        first_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        first_response = client.get(first_url)

        assert first_response.status_code == 302

        confirmation_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        second_response = client.get(confirmation_url)

        assert second_response.status_code == 200

        test_user.refresh_from_db()

        assert test_user.is_active is True

    def test_confirmation_done_creates_profile(
        self,
        client,
        test_user,
        test_admin,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        first_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(first_url)

        assert response.status_code == 302

        confirmation_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        response = client.get(confirmation_url)

        assert response.status_code == 200
        assert Profile.objects.filter(
            user=test_user,
        ).exists()

    def test_confirmation_done_does_not_create_duplicate_profile(
        self,
        client,
        test_user,
        test_admin,
    ):
        existing_profile = Profile.objects.create(
            user=test_user,
        )

        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        first_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(first_url)

        assert response.status_code == 302

        confirmation_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        response = client.get(confirmation_url)

        assert response.status_code == 200
        assert (
            Profile.objects.filter(
                user=test_user,
            ).count()
            == 1
        )

        existing_profile.refresh_from_db()

        assert existing_profile.user == test_user

    def test_confirmation_done_with_missing_session_token_is_invalid(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["validlink"] is False
        assert response.context["form"] is None

        test_user.refresh_from_db()

        assert test_user.is_active is False
        assert not Profile.objects.filter(
            user=test_user,
        ).exists()

    def test_confirmation_done_with_invalid_session_token_is_invalid(
        self,
        client,
        test_user,
    ):
        session = client.session
        session[INTERNAL_REGISTRATION_SESSION_TOKEN] = "invalid-token"
        session.save()

        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["validlink"] is False

        test_user.refresh_from_db()

        assert test_user.is_active is False
        assert not Profile.objects.filter(
            user=test_user,
        ).exists()

    def test_valid_confirmation_context_contains_validlink(
        self,
        client,
        test_user,
        test_admin,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        first_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(first_url)

        assert response.status_code == 302

        confirmation_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        response = client.get(confirmation_url)

        assert response.status_code == 200
        assert response.context["validlink"] is True
        assert response.context["admin"] == test_admin

    def test_valid_confirmation_without_admin_does_not_raise_error(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        first_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(first_url)

        assert response.status_code == 302

        confirmation_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        response = client.get(confirmation_url)

        assert response.status_code == 200
        assert response.context["validlink"] is True
        assert response.context["admin"] is None

        test_user.refresh_from_db()

        assert test_user.is_active is True

    def test_invalid_confirmation_context_contains_expected_values(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "invalid-token",
            },
        )

        response = client.get(url)

        assert response.context["form"] is None
        assert response.context["title"] == "Password reset unsuccessful"
        assert response.context["validlink"] is False

    def test_valid_confirmation_context_does_not_contain_reset_form(
        self,
        client,
        test_user,
        test_admin,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        first_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(first_url)

        assert response.status_code == 302

        confirmation_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        response = client.get(confirmation_url)

        assert response.status_code == 200
        assert response.context["validlink"] is True
        assert "form" not in response.context

    def test_confirmation_uses_custom_token_generator(
        self,
        client,
        test_user,
    ):
        with patch(
            "account.views.RegistrationConfirmView.token_generator",
        ) as token_generator:
            token_generator.check_token.return_value = True

            uidb64 = urlsafe_base64_encode(
                force_bytes(test_user.pk),
            )

            url = reverse(
                "account:register_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": "custom-token",
                },
            )

            response = client.get(url)

        assert response.status_code == 302

        token_generator.check_token.assert_called_once_with(
            test_user,
            "custom-token",
        )

    def test_confirmation_done_uses_custom_token_generator(
        self,
        client,
        test_user,
        test_admin,
    ):
        session = client.session
        session[INTERNAL_REGISTRATION_SESSION_TOKEN] = "stored-token"
        session.save()

        with patch(
            "account.views.RegistrationConfirmView.token_generator",
        ) as token_generator:
            token_generator.check_token.return_value = True

            uidb64 = urlsafe_base64_encode(
                force_bytes(test_user.pk),
            )

            url = reverse(
                "account:register_confirm",
                kwargs={
                    "uidb64": uidb64,
                    "token": "confirmation-done",
                },
            )

            response = client.get(url)

        assert response.status_code == 200

        token_generator.check_token.assert_called_once_with(
            test_user,
            "stored-token",
        )

        test_user.refresh_from_db()

        assert test_user.is_active is True

    def test_invalid_uid_does_not_activate_existing_users(
        self,
        client,
        test_user,
    ):
        invalid_uid = urlsafe_base64_encode(
            force_bytes(999999999),
        )

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": invalid_uid,
                "token": "confirmation-done",
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["validlink"] is False

        test_user.refresh_from_db()

        assert test_user.is_active is False

    def test_confirmation_for_already_active_user(
        self,
        client,
        test_user,
        test_admin,
    ):
        test_user.is_active = True
        test_user.save(update_fields=["is_active"])

        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        first_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(first_url)

        assert response.status_code == 302

        confirmation_url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": "confirmation-done",
            },
        )

        response = client.get(confirmation_url)

        assert response.status_code == 200
        assert response.context["validlink"] is True
        assert response.context["admin"] == test_admin
        assert Profile.objects.filter(
            user=test_user,
        ).exists()

    def test_confirmation_token_becomes_invalid_after_password_change(
        self,
        client,
        test_user,
    ):
        uidb64 = urlsafe_base64_encode(
            force_bytes(test_user.pk),
        )
        token = default_token_generator.make_token(test_user)

        test_user.set_password("changed_password")
        test_user.save()

        url = reverse(
            "account:register_confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        response = client.get(url)

        assert response.status_code == 200
        assert response.context["validlink"] is False

        test_user.refresh_from_db()

        assert test_user.is_active is False
