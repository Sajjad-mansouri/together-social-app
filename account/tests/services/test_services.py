from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory
from django.utils.http import urlsafe_base64_decode

from account.services import EmailConfirmation, send_email

pytestmark = pytest.mark.django_db


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
def test_request():
    return RequestFactory().get("/")


@pytest.fixture
def secure_test_request():
    return RequestFactory().get("/", secure=True)


class TestSendEmail:
    def test_sends_plain_text_email(
        self,
        mailoutbox,
    ):
        with patch(
            "account.services.loader.render_to_string",
            side_effect=[
                "test email body",
            ],
        ) as render_to_string:
            send_email(
                subject_template_name="Test subject",
                email_template_name="test_email.txt",
                context={"test_key": "test_value"},
                from_email="test_sender@example.com",
                to_email="test_user@example.com",
            )

        assert len(mailoutbox) == 1

        email = mailoutbox[0]

        assert email.subject == "Test subject"
        assert email.body == "test email body"
        assert email.from_email == "test_sender@example.com"
        assert email.to == ["test_user@example.com"]

        render_to_string.assert_called_once_with(
            "test_email.txt",
            {"test_key": "test_value"},
        )

    def test_renders_subject_when_subject_is_not_string(
        self,
        mailoutbox,
    ):
        with patch(
            "account.services.loader.render_to_string",
            side_effect=[
                "Rendered subject",
                "test email body",
            ],
        ) as render_to_string:
            send_email(
                subject_template_name=MagicMock(),
                email_template_name="test_email.txt",
                context={"test_key": "test_value"},
                from_email="test_sender@example.com",
                to_email="test_user@example.com",
            )

        assert len(mailoutbox) == 1
        assert mailoutbox[0].subject == "Rendered subject"

        assert render_to_string.call_count == 2

    def test_removes_line_breaks_from_subject(
        self,
        mailoutbox,
    ):
        with patch(
            "account.services.loader.render_to_string",
            return_value="test email body",
        ):
            send_email(
                subject_template_name=("test subject\nsecond line\r\nthird line"),
                email_template_name="test_email.txt",
                context={},
                from_email="test_sender@example.com",
                to_email="test_user@example.com",
            )

        assert mailoutbox[0].subject == ("test subjectsecond linethird line")

    def test_renders_html_email_when_html_template_is_provided(
        self,
        mailoutbox,
    ):
        with patch(
            "account.services.loader.render_to_string",
            side_effect=[
                "test email body",
                "<p>test html email</p>",
            ],
        ) as render_to_string:
            send_email(
                subject_template_name="Test subject",
                email_template_name="test_email.txt",
                context={"test_key": "test_value"},
                from_email="test_sender@example.com",
                to_email="test_user@example.com",
                html_email_template_name="test_email.html",
            )

        assert len(mailoutbox) == 1

        email = mailoutbox[0]

        assert email.body == "test email body"
        assert email.alternatives == [
            (
                "<p>test html email</p>",
                "text/html",
            ),
        ]

        assert render_to_string.call_count == 2
        render_to_string.assert_any_call(
            "test_email.txt",
            {"test_key": "test_value"},
        )
        render_to_string.assert_any_call(
            "test_email.html",
            {"test_key": "test_value"},
        )

    def test_does_not_render_html_when_html_template_is_not_provided(
        self,
        mailoutbox,
    ):
        with patch(
            "account.services.loader.render_to_string",
            return_value="test email body",
        ) as render_to_string:
            send_email(
                subject_template_name="Test subject",
                email_template_name="test_email.txt",
                context={},
                from_email="test_sender@example.com",
                to_email="test_user@example.com",
                html_email_template_name=None,
            )

        assert len(mailoutbox) == 1
        assert mailoutbox[0].alternatives == []

        render_to_string.assert_called_once_with(
            "test_email.txt",
            {},
        )

    def test_uses_same_context_for_all_templates(
        self,
        mailoutbox,
    ):
        context = {
            "username": "test_user",
            "domain": "example.com",
        }

        with patch(
            "account.services.loader.render_to_string",
            side_effect=[
                "test body",
                "<p>test html</p>",
            ],
        ) as render_to_string:
            send_email(
                subject_template_name="Test subject",
                email_template_name="test_email.txt",
                context=context,
                from_email="test_sender@example.com",
                to_email="test_user@example.com",
                html_email_template_name="test_email.html",
            )

        render_to_string.assert_any_call(
            "test_email.txt",
            context,
        )
        render_to_string.assert_any_call(
            "test_email.html",
            context,
        )

    def test_sends_email_to_single_recipient(
        self,
        mailoutbox,
    ):
        with patch(
            "account.services.loader.render_to_string",
            return_value="test body",
        ):
            send_email(
                subject_template_name="Test subject",
                email_template_name="test_email.txt",
                context={},
                from_email="test_sender@example.com",
                to_email="test_user@example.com",
            )

        assert mailoutbox[0].to == [
            "test_user@example.com",
        ]

    def test_uses_supplied_from_email(
        self,
        mailoutbox,
    ):
        with patch(
            "account.services.loader.render_to_string",
            return_value="test body",
        ):
            send_email(
                subject_template_name="Test subject",
                email_template_name="test_email.txt",
                context={},
                from_email="custom_sender@example.com",
                to_email="test_user@example.com",
            )

        assert mailoutbox[0].from_email == ("custom_sender@example.com")


class TestEmailConfirmation:
    def test_initializes_with_email_and_request(
        self,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email="test_user@example.com",
            request=test_request,
        )

        assert confirmation.email == "test_user@example.com"
        assert confirmation.request is test_request

    def test_class_defaults(self):
        assert (
            EmailConfirmation.subject_template_name
            == "email/registration/confirmation_email_subject.txt"
        )
        assert (
            EmailConfirmation.email_template_name
            == "email/registration/confirmation_email.html"
        )
        assert (
            EmailConfirmation.html_email_template_name
            == "email/registration/confirmation_html_email.html"
        )
        assert EmailConfirmation.domain_override is None
        assert EmailConfirmation.from_email is None
        assert EmailConfirmation.extra_email_context is None

    def test_get_users_returns_matching_user(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        users = list(
            confirmation.get_users(test_user.email),
        )

        assert users == [test_user]

    def test_get_users_performs_case_insensitive_lookup(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email.upper(),
            request=test_request,
        )

        users = list(
            confirmation.get_users(test_user.email.upper()),
        )

        assert users == [test_user]

    def test_get_users_returns_multiple_matching_users(
        self,
        django_user_model,
        test_request,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_user_2 = django_user_model.objects.create_user(
            username="test_user_2",
            email="TEST_USER@example.com",
            password="test_password",
        )

        confirmation = EmailConfirmation(
            email="test_user@example.com",
            request=test_request,
        )

        users = list(
            confirmation.get_users(
                "test_user@example.com",
            ),
        )

        assert users == [test_user, test_user_2]

    def test_get_users_excludes_user_with_unusable_password(
        self,
        django_user_model,
        test_request,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

        test_user_2 = django_user_model.objects.create_user(
            username="test_user_2",
            email="test_user_2@example.com",
            password="test_password",
        )
        test_user_2.set_unusable_password()
        test_user_2.save(update_fields=["password"])

        confirmation = EmailConfirmation(
            email="test_user@example.com",
            request=test_request,
        )

        users = list(
            confirmation.get_users(
                test_user.email,
            ),
        )

        assert users == [test_user]

    def test_get_users_returns_empty_generator_when_no_user_matches(
        self,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email="nonexistent@example.com",
            request=test_request,
        )

        users = list(
            confirmation.get_users(
                "nonexistent@example.com",
            ),
        )

        assert users == []

    def test_get_users_returns_empty_generator_for_unusable_password(
        self,
        django_user_model,
        test_request,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_user.set_unusable_password()
        test_user.save(update_fields=["password"])

        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        users = list(
            confirmation.get_users(test_user.email),
        )

        assert users == []

    def test_send_mail_delegates_to_send_email(
        self,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email="test_user@example.com",
            request=test_request,
        )

        context = {
            "test_key": "test_value",
        }

        with patch(
            "account.services.send_email",
        ) as send_email_mock:
            confirmation.send_mail(
                subject_template_name="test_subject.txt",
                email_template_name="test_email.txt",
                context=context,
                from_email="test_sender@example.com",
                to_email="test_user@example.com",
                html_email_template_name="test_email.html",
            )

        send_email_mock.assert_called_once_with(
            subject_template_name="test_subject.txt",
            email_template_name="test_email.txt",
            context=context,
            from_email="test_sender@example.com",
            to_email="test_user@example.com",
            html_email_template_name="test_email.html",
        )

    def test_send_mail_passes_none_html_template(
        self,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email="test_user@example.com",
            request=test_request,
        )

        with patch(
            "account.services.send_email",
        ) as send_email_mock:
            confirmation.send_mail(
                subject_template_name="test_subject.txt",
                email_template_name="test_email.txt",
                context={},
                from_email=None,
                to_email="test_user@example.com",
            )

        send_email_mock.assert_called_once_with(
            subject_template_name="test_subject.txt",
            email_template_name="test_email.txt",
            context={},
            from_email=None,
            to_email="test_user@example.com",
            html_email_template_name=None,
        )

    def test_save_sends_confirmation_email(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        send_mail_mock.assert_called_once()

        call_kwargs = send_mail_mock.call_args.kwargs

        assert call_kwargs["to_email"] == test_user.email

    def test_save_uses_domain_override(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )
        confirmation.domain_override = "example.com"

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["domain"] == "example.com"
        assert context["site_name"] == "example.com"

    def test_save_uses_current_site_when_domain_is_not_overridden(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        current_site = MagicMock()
        current_site.name = "test_site"
        current_site.domain = "test.example.com"

        with patch(
            "account.services.get_current_site",
            return_value=current_site,
        ) as get_current_site_mock:
            with patch.object(
                confirmation,
                "send_mail",
            ) as send_mail_mock:
                confirmation.save()

        get_current_site_mock.assert_called_once_with(
            test_request,
        )

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["domain"] == "test.example.com"
        assert context["site_name"] == "test_site"

    def test_save_uses_http_for_insecure_request(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["protocol"] == "http"

    def test_save_uses_https_for_secure_request(
        self,
        test_user,
        secure_test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=secure_test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["protocol"] == "https"

    def test_save_generates_uid_for_user(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        context = send_mail_mock.call_args.kwargs["context"]

        decoded_user_id = urlsafe_base64_decode(
            context["uid"],
        ).decode()

        assert decoded_user_id == str(test_user.pk)

    def test_save_generates_token_for_user(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        token = "test-token"

        token_generator = MagicMock()
        token_generator.make_token.return_value = token

        confirmation.token_generator = token_generator

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        token_generator.make_token.assert_called_once_with(
            test_user,
        )

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["token"] == token

    def test_save_includes_username_in_context(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["username"] == test_user.get_username()

    def test_save_includes_user_email_in_context(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["email"] == test_user.email

    def test_save_uses_class_template_configuration(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        call_kwargs = send_mail_mock.call_args.kwargs

        assert (
            call_kwargs["subject_template_name"] == confirmation.subject_template_name
        )
        assert call_kwargs["email_template_name"] == confirmation.email_template_name
        assert (
            call_kwargs["html_email_template_name"]
            == confirmation.html_email_template_name
        )

    def test_save_uses_from_email_configuration(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )
        confirmation.from_email = "test_sender@example.com"

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        assert (
            send_mail_mock.call_args.kwargs["from_email"] == "test_sender@example.com"
        )

    def test_save_supports_extra_email_context(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )
        confirmation.extra_email_context = {
            "test_key": "test_value",
        }

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["test_key"] == "test_value"

    def test_save_sends_no_email_when_user_does_not_exist(
        self,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email="nonexistent@example.com",
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        send_mail_mock.assert_not_called()

    def test_save_skips_users_with_unusable_password(
        self,
        django_user_model,
        test_request,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_user.set_unusable_password()
        test_user.save(update_fields=["password"])

        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        send_mail_mock.assert_not_called()

    def test_save_sends_one_email_for_each_matching_user(
        self,
        django_user_model,
        test_request,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_user_2 = django_user_model.objects.create_user(
            username="test_user_2",
            email="TEST_USER@example.com",
            password="test_password",
        )

        confirmation = EmailConfirmation(
            email="test_user@example.com",
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        assert send_mail_mock.call_count == 2

        recipients = {call.kwargs["to_email"] for call in send_mail_mock.call_args_list}

        assert recipients == {
            test_user.email,
            test_user_2.email,
        }

    def test_save_sends_each_user_specific_context(
        self,
        django_user_model,
        test_request,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_user_2 = django_user_model.objects.create_user(
            username="test_user_2",
            email="TEST_USER@example.com",
            password="test_password",
        )

        confirmation = EmailConfirmation(
            email="test_user@example.com",
            request=test_request,
        )

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        contexts = [call.kwargs["context"] for call in send_mail_mock.call_args_list]

        users = {context["username"] for context in contexts}

        emails = {context["email"] for context in contexts}

        assert users == {
            test_user.username,
            test_user_2.username,
        }

        assert emails == {
            test_user.email,
            test_user_2.email,
        }

    def test_save_passes_extra_context_to_each_email(
        self,
        django_user_model,
        test_request,
    ):
        django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

        confirmation = EmailConfirmation(
            email="test_user@example.com",
            request=test_request,
        )
        confirmation.extra_email_context = {
            "test_key": "test_value",
        }

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        context = send_mail_mock.call_args.kwargs["context"]

        assert context["test_key"] == "test_value"

    def test_save_uses_custom_subject_template(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )
        confirmation.subject_template_name = "test_subject.txt"

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        assert (
            send_mail_mock.call_args.kwargs["subject_template_name"]
            == "test_subject.txt"
        )

    def test_save_uses_custom_email_template(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )
        confirmation.email_template_name = "test_email.txt"

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        assert (
            send_mail_mock.call_args.kwargs["email_template_name"] == "test_email.txt"
        )

    def test_save_uses_custom_html_email_template(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )
        confirmation.html_email_template_name = "test_email.html"

        with patch.object(
            confirmation,
            "send_mail",
        ) as send_mail_mock:
            confirmation.save()

        assert (
            send_mail_mock.call_args.kwargs["html_email_template_name"]
            == "test_email.html"
        )

    def test_save_does_not_use_current_site_when_domain_is_overridden(
        self,
        test_user,
        test_request,
    ):
        confirmation = EmailConfirmation(
            email=test_user.email,
            request=test_request,
        )
        confirmation.domain_override = "example.com"

        with patch(
            "account.services.get_current_site",
        ) as get_current_site_mock:
            with patch.object(
                confirmation,
                "send_mail",
            ):
                confirmation.save()

        get_current_site_mock.assert_not_called()
