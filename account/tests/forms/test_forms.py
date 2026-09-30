from datetime import date
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.utils.http import urlsafe_base64_decode
from PIL import Image

from account.forms import CustomCreationForm, ProfileForm, UserForm
from account.models import Profile

pytestmark = pytest.mark.django_db


def create_test_image(
    name="test_image.jpg",
    image_format="JPEG",
    content_type="image/jpeg",
):
    image = Image.new("RGB", (1, 1))
    image_data = BytesIO()
    image.save(image_data, format=image_format)
    image_data.seek(0)

    return SimpleUploadedFile(
        name=name,
        content=image_data.getvalue(),
        content_type=content_type,
    )


@pytest.fixture
def test_user(django_user_model):
    return django_user_model.objects.create_user(
        username="test_user",
        email="test_user@example.com",
        password="test_password",
    )


@pytest.fixture
def test_user_2(django_user_model):
    return django_user_model.objects.create_user(
        username="test_user_2",
        email="test_user_2@example.com",
        password="test_password",
    )


@pytest.fixture
def test_profile(test_user):
    return Profile.objects.create(user=test_user)


@pytest.fixture
def test_request():
    return RequestFactory().get("/")


class TestProfileForm:
    def test_form_contains_expected_fields(self):
        form = ProfileForm()

        assert list(form.fields) == [
            "profile_image",
            "birth_day",
        ]

    def test_form_accepts_valid_data(self):
        form = ProfileForm(
            data={
                "birth_day": "2000-01-01",
            },
        )

        assert form.is_valid()
        assert form.cleaned_data["birth_day"] == date(2000, 1, 1)

    def test_profile_image_uses_model_default(self):
        form = ProfileForm(
            data={
                "birth_day": "2000-01-01",
            },
        )

        assert form.is_valid()
        assert (
            form.instance.profile_image.name
            == "profile_image/default/blank-profile.png"
        )

    def test_form_accepts_valid_image(self):
        test_image = create_test_image()

        form = ProfileForm(
            data={
                "birth_day": "2000-01-01",
            },
            files={
                "profile_image": test_image,
            },
        )

        assert form.is_valid()
        assert form.cleaned_data["profile_image"] is not None
        assert form.cleaned_data["profile_image"].name == "test_image.jpg"

    def test_birth_day_is_optional(self):
        form = ProfileForm(data={})

        assert form.is_valid()
        assert form.cleaned_data["birth_day"] is None

    def test_invalid_birth_day_is_rejected(self):
        form = ProfileForm(
            data={
                "birth_day": "not-a-date",
            },
        )

        assert form.is_valid() is False
        assert "birth_day" in form.errors

    def test_invalid_image_is_rejected(self):
        test_image = SimpleUploadedFile(
            name="test_image.jpg",
            content=b"not a real image",
            content_type="image/jpeg",
        )

        form = ProfileForm(
            data={
                "birth_day": "2000-01-01",
            },
            files={
                "profile_image": test_image,
            },
        )

        assert form.is_valid() is False
        assert "profile_image" in form.errors

    def test_save_creates_profile(self, test_user):
        form = ProfileForm(
            data={
                "birth_day": "2000-01-01",
            },
        )

        assert form.is_valid()

        test_profile = form.save(commit=False)
        test_profile.user = test_user
        test_profile.save()

        assert test_profile.pk is not None
        assert test_profile.user == test_user
        assert test_profile.birth_day == date(2000, 1, 1)

    def test_save_with_image_updates_profile(self, test_profile):
        test_image = create_test_image()

        form = ProfileForm(
            instance=test_profile,
            data={
                "birth_day": "1995-05-15",
            },
            files={
                "profile_image": test_image,
            },
        )

        assert form.is_valid()

        updated_profile = form.save()

        assert updated_profile.pk == test_profile.pk
        assert updated_profile.birth_day == date(1995, 5, 15)
        assert updated_profile.profile_image.name.startswith("profile_image/")

    def test_form_updates_existing_profile(self, test_profile):
        form = ProfileForm(
            instance=test_profile,
            data={
                "birth_day": "1995-05-15",
            },
        )

        assert form.is_valid()

        updated_profile = form.save()

        assert updated_profile.pk == test_profile.pk
        assert updated_profile.birth_day == date(1995, 5, 15)


class TestUserForm:
    def test_form_contains_expected_fields(self):
        form = UserForm()

        assert list(form.fields) == [
            "first_name",
            "last_name",
            "username",
            "email",
        ]

    def test_form_accepts_valid_data(self):
        form = UserForm(
            data={
                "first_name": "test_first_name",
                "last_name": "test_last_name",
                "username": "test_user",
                "email": "test_user@example.com",
            },
        )

        assert form.is_valid()

    def test_form_creates_user(self):
        form = UserForm(
            data={
                "first_name": "test_first_name",
                "last_name": "test_last_name",
                "username": "test_user",
                "email": "test_user@example.com",
            },
        )

        assert form.is_valid()

        test_user = form.save()

        assert test_user.pk is not None
        assert test_user.first_name == "test_first_name"
        assert test_user.last_name == "test_last_name"
        assert test_user.username == "test_user"
        assert test_user.email == "test_user@example.com"

    def test_first_name_is_optional(self):
        form = UserForm(
            data={
                "first_name": "",
                "last_name": "test_last_name",
                "username": "test_user",
                "email": "test_user@example.com",
            },
        )

        assert form.is_valid()

    def test_last_name_is_optional(self):
        form = UserForm(
            data={
                "first_name": "test_first_name",
                "last_name": "",
                "username": "test_user",
                "email": "test_user@example.com",
            },
        )

        assert form.is_valid()

    def test_username_is_required(self):
        form = UserForm(
            data={
                "first_name": "test_first_name",
                "last_name": "test_last_name",
                "username": "",
                "email": "test_user@example.com",
            },
        )

        assert form.is_valid() is False
        assert "username" in form.errors

    def test_email_is_required(self):
        form = UserForm(
            data={
                "first_name": "test_first_name",
                "last_name": "test_last_name",
                "username": "test_user",
                "email": "",
            },
        )

        assert form.is_valid() is False
        assert "email" in form.errors

    def test_invalid_email_is_rejected(self):
        form = UserForm(
            data={
                "first_name": "test_first_name",
                "last_name": "test_last_name",
                "username": "test_user",
                "email": "invalid-email",
            },
        )

        assert form.is_valid() is False
        assert "email" in form.errors

    def test_duplicate_username_is_rejected(self, test_user):
        form = UserForm(
            data={
                "first_name": "test_first_name",
                "last_name": "test_last_name",
                "username": test_user.username,
                "email": "test_user_2@example.com",
            },
        )

        assert form.is_valid() is False
        assert "username" in form.errors

    def test_duplicate_email_is_rejected(self, test_user):
        form = UserForm(
            data={
                "first_name": "test_first_name",
                "last_name": "test_last_name",
                "username": "test_user_2",
                "email": test_user.email,
            },
        )

        assert form.is_valid() is False
        assert "email" in form.errors

    def test_form_updates_existing_user(self, test_user):
        form = UserForm(
            instance=test_user,
            data={
                "first_name": "test_updated_first_name",
                "last_name": "test_updated_last_name",
                "username": test_user.username,
                "email": test_user.email,
            },
        )

        assert form.is_valid()

        updated_user = form.save()

        assert updated_user.pk == test_user.pk
        assert updated_user.first_name == "test_updated_first_name"
        assert updated_user.last_name == "test_updated_last_name"
        assert updated_user.username == test_user.username
        assert updated_user.email == test_user.email


class TestCustomCreationForm:
    def test_form_contains_expected_fields(self):
        form = CustomCreationForm()

        assert list(form.fields) == [
            "username",
            "email",
            "password1",
            "password2",
        ]

    def test_valid_registration_data(self):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "test_user@example.com",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid()

    def test_username_is_required(self):
        form = CustomCreationForm(
            data={
                "username": "",
                "email": "test_user@example.com",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid() is False
        assert "username" in form.errors

    def test_email_is_required(self):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid() is False
        assert "email" in form.errors

    def test_invalid_email_is_rejected(self):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "invalid-email",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid() is False
        assert "email" in form.errors

    def test_email_value_is_preserved_by_form_cleaning(self):
        test_email = "Test_User@Example.COM"

        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": test_email,
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid()
        assert form.cleaned_data["email"] == test_email

    def test_password_mismatch_is_rejected(self):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "test_user@example.com",
                "password1": "TestPassword123!",
                "password2": "DifferentPassword123!",
            },
        )

        assert form.is_valid() is False
        assert "__all__" in form.errors or "password2" in form.errors

    def test_weak_password_is_rejected(self):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "test_user@example.com",
                "password1": "123",
                "password2": "123",
            },
        )

        assert form.is_valid() is False
        assert "password2" in form.errors or "__all__" in form.errors

    def test_duplicate_username_is_rejected(self, test_user):
        form = CustomCreationForm(
            data={
                "username": test_user.username,
                "email": "test_user_2@example.com",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid() is False
        assert "username" in form.errors

    def test_duplicate_email_is_rejected(self, test_user):
        form = CustomCreationForm(
            data={
                "username": "test_user_2",
                "email": test_user.email,
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid() is False
        assert "email" in form.errors

    def test_save_commit_false_does_not_create_user(self):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "test_user@example.com",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid()

        with patch.object(
            form,
            "_send_confirmation_email",
        ) as send_confirmation_email:
            test_user = form.save(commit=False)

        assert test_user.pk is None
        assert test_user.username == "test_user"
        assert test_user.email == "test_user@example.com"
        assert test_user.is_active is False

        send_confirmation_email.assert_not_called()

    def test_save_creates_inactive_user(self, test_request):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "test_user@example.com",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid()

        with patch.object(
            form,
            "_send_confirmation_email",
        ) as send_confirmation_email:
            test_user = form.save(
                request=test_request,
                domain_override="example.com",
            )

        test_user.refresh_from_db()

        assert test_user.pk is not None
        assert test_user.is_active is False

        send_confirmation_email.assert_called_once_with(
            request=test_request,
            domain_override="example.com",
        )

    def test_save_sets_password(self, test_request):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "test_user@example.com",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid()

        with patch.object(
            form,
            "_send_confirmation_email",
        ):
            test_user = form.save(
                request=test_request,
                domain_override="example.com",
            )

        assert test_user.check_password("TestPassword123!")
        assert not test_user.check_password("WrongPassword123!")

    def test_save_sends_confirmation_email(self, test_request):
        form = CustomCreationForm(
            data={
                "username": "test_user",
                "email": "test_user@example.com",
                "password1": "TestPassword123!",
                "password2": "TestPassword123!",
            },
        )

        assert form.is_valid()

        with patch.object(
            form,
            "send_mail",
        ) as send_mail:
            test_user = form.save(
                request=test_request,
                domain_override="example.com",
            )

        assert test_user.pk is not None
        send_mail.assert_called_once()

        call_kwargs = send_mail.call_args.kwargs

        assert call_kwargs["to_email"] == test_user.email
        assert call_kwargs["context"]["user"] == test_user
        assert call_kwargs["context"]["email"] == test_user.email
        assert call_kwargs["context"]["domain"] == "example.com"

    def test_send_mail_sends_plain_text_email(self, mailoutbox):
        form = CustomCreationForm()

        with patch(
            "account.forms.loader.render_to_string",
            side_effect=[
                "test subject\n",
                "test email body",
            ],
        ):
            form.send_mail(
                subject_template_name="test_subject.txt",
                email_template_name="test_email.txt",
                context={"test_key": "test_value"},
                from_email="test@example.com",
                to_email="test_user@example.com",
            )

        assert len(mailoutbox) == 1

        test_email = mailoutbox[0]

        assert test_email.subject == "test subject"
        assert test_email.body == "test email body"
        assert test_email.from_email == "test@example.com"
        assert test_email.to == ["test_user@example.com"]

    def test_send_mail_removes_newlines_from_subject(
        self,
        mailoutbox,
    ):
        form = CustomCreationForm()

        with patch(
            "account.forms.loader.render_to_string",
            side_effect=[
                "test subject\nsecond line\r\n",
                "test email body",
            ],
        ):
            form.send_mail(
                subject_template_name="test_subject.txt",
                email_template_name="test_email.txt",
                context={},
                from_email="test@example.com",
                to_email="test_user@example.com",
            )

        assert mailoutbox[0].subject == "test subjectsecond line"

    def test_send_mail_attaches_html_email(self, mailoutbox):
        form = CustomCreationForm()

        with patch(
            "account.forms.loader.render_to_string",
            side_effect=[
                "test subject",
                "test email body",
                "<p>test html email</p>",
            ],
        ):
            form.send_mail(
                subject_template_name="test_subject.txt",
                email_template_name="test_email.txt",
                context={},
                from_email="test@example.com",
                to_email="test_user@example.com",
                html_email_template_name="test_email.html",
            )

        assert len(mailoutbox) == 1

        test_email = mailoutbox[0]

        assert test_email.alternatives == [
            (
                "<p>test html email</p>",
                "text/html",
            ),
        ]

    def test_send_mail_does_not_attach_html_without_html_template(
        self,
        mailoutbox,
    ):
        form = CustomCreationForm()

        with patch(
            "account.forms.loader.render_to_string",
            side_effect=[
                "test subject",
                "test email body",
            ],
        ):
            form.send_mail(
                subject_template_name="test_subject.txt",
                email_template_name="test_email.txt",
                context={},
                from_email="test@example.com",
                to_email="test_user@example.com",
                html_email_template_name=None,
            )

        assert len(mailoutbox) == 1
        assert mailoutbox[0].alternatives == []

    def test_send_confirmation_email_for_existing_user(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        send_mail.assert_called_once()

        context = send_mail.call_args.kwargs["context"]

        assert context["email"] == test_user.email
        assert context["domain"] == "example.com"
        assert context["site_name"] == "example.com"
        assert context["user"] == test_user
        assert context["username"] == test_user.username
        assert context["protocol"] == "http"
        assert context["uid"]
        assert context["token"]

    def test_send_confirmation_email_uses_https(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                use_https=True,
                request=test_request,
            )

        context = send_mail.call_args.kwargs["context"]

        assert context["protocol"] == "https"

    def test_send_confirmation_email_supports_extra_context(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
                extra_email_context={
                    "test_key": "test_value",
                },
            )

        context = send_mail.call_args.kwargs["context"]

        assert context["test_key"] == "test_value"

    def test_confirmation_email_uses_case_insensitive_email_lookup(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email.upper(),
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        send_mail.assert_called_once()

        context = send_mail.call_args.kwargs["context"]

        assert context["user"] == test_user
        assert context["email"] == test_user.email

    def test_confirmation_email_uses_stored_user_email(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email.upper(),
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        assert send_mail.call_args.kwargs["to_email"] == test_user.email

    def test_confirmation_email_contains_valid_uid(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        context = send_mail.call_args.kwargs["context"]

        decoded_user_id = urlsafe_base64_decode(
            context["uid"],
        ).decode()

        assert decoded_user_id == str(test_user.pk)

    def test_confirmation_email_contains_valid_token(
        self,
        test_user,
        test_request,
    ):
        from django.contrib.auth.tokens import default_token_generator

        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        context = send_mail.call_args.kwargs["context"]

        assert default_token_generator.check_token(
            test_user,
            context["token"],
        )

    def test_confirmation_email_is_not_sent_when_email_does_not_exist(
        self,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": "nonexistent@example.com",
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        send_mail.assert_not_called()

    def test_confirmation_email_uses_user_email_from_database(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        call_kwargs = send_mail.call_args.kwargs

        assert call_kwargs["to_email"] == test_user.email
        assert call_kwargs["context"]["email"] == test_user.email

    def test_confirmation_email_passes_html_template(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        assert (
            send_mail.call_args.kwargs["html_email_template_name"]
            == "registration/registration_email.html"
        )

    def test_confirmation_email_passes_default_templates(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        call_kwargs = send_mail.call_args.kwargs

        assert (
            call_kwargs["subject_template_name"]
            == "registration/registration_subject.txt"
        )
        assert (
            call_kwargs["email_template_name"] == "registration/registration_email.txt"
        )

    def test_confirmation_email_uses_custom_templates(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
                subject_template_name="test_subject.txt",
                email_template_name="test_email.txt",
                html_email_template_name="test_email.html",
            )

        call_kwargs = send_mail.call_args.kwargs

        assert call_kwargs["subject_template_name"] == "test_subject.txt"
        assert call_kwargs["email_template_name"] == "test_email.txt"
        assert call_kwargs["html_email_template_name"] == "test_email.html"

    def test_confirmation_email_uses_custom_token_generator(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        test_token = "test-token"

        class TestTokenGenerator:
            def make_token(self, user):
                assert user == test_user
                return test_token

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
                token_generator=TestTokenGenerator(),
            )

        context = send_mail.call_args.kwargs["context"]

        assert context["token"] == test_token

    def test_confirmation_email_uses_custom_from_email(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
                from_email="test_sender@example.com",
            )

        assert send_mail.call_args.kwargs["from_email"] == "test_sender@example.com"

    def test_confirmation_email_processes_matching_user(
        self,
        test_user,
        test_user_2,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        send_mail.assert_called_once()

        assert send_mail.call_args.kwargs["to_email"] == test_user.email
        assert send_mail.call_args.kwargs["context"]["user"] == test_user
        assert send_mail.call_args.kwargs["context"]["user"] != test_user_2

    def test_confirmation_email_uses_request_for_logo_url(
        self,
        test_user,
        test_request,
    ):
        form = CustomCreationForm()
        form.cleaned_data = {
            "email": test_user.email,
        }

        with patch.object(form, "send_mail") as send_mail:
            form._send_confirmation_email(
                domain_override="example.com",
                request=test_request,
            )

        context = send_mail.call_args.kwargs["context"]

        assert context["logo_url"].startswith("http")
        assert "images/logo_transparent.png" in context["logo_url"]
