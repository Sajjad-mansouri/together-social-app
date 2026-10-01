from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.test import APIClient

from api.views import MessageApiView


class TestMessageApiView:
    def setup_method(self):
        self.client = APIClient()

    def test_view_configuration(self):
        assert MessageApiView.parser_classes == [
            FormParser,
            MultiPartParser,
            JSONParser,
        ]

    @patch("api.views.mail_admins")
    @patch("api.views.EmailMessage")
    @patch("api.views.render_to_string")
    def test_send_message_successfully(
        self,
        mock_render_to_string,
        mock_email_message,
        mock_mail_admins,
    ):
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "message": "I have a question about the website.",
        }

        mock_render_to_string.side_effect = [
            "Thank you John Doe!",
            "New message from John Doe: I have a question about the website.",
        ]

        mock_message = mock_email_message.return_value

        url = reverse("api:message")

        response = self.client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == "sent"

        assert mock_render_to_string.call_count == 2

        mock_render_to_string.assert_any_call(
            "email/message_user.txt",
            {"user": "John Doe"},
        )
        mock_render_to_string.assert_any_call(
            "email/message_admin.txt",
            {
                "user": "John Doe",
                "message": "I have a question about the website.",
            },
        )

        mock_email_message.assert_called_once_with(
            "Thank you for contacting us!",
            "Thank you John Doe!",
            None,
            ["john@example.com"],
        )

        mock_message.send.assert_called_once_with()

        mock_mail_admins.assert_called_once_with(
            "New message",
            "New message from John Doe: I have a question about the website.",
        )

    @patch("api.views.mail_admins")
    @patch("api.views.EmailMessage")
    @patch("api.views.render_to_string")
    def test_email_is_sent_to_submitted_email_address(
        self,
        mock_render_to_string,
        mock_email_message,
        mock_mail_admins,
    ):
        data = {
            "name": "Jane Smith",
            "email": "jane@example.com",
            "message": "Please contact me.",
        }

        mock_render_to_string.side_effect = [
            "User email body",
            "Admin email body",
        ]

        url = reverse("api:message")

        response = self.client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        mock_email_message.assert_called_once_with(
            "Thank you for contacting us!",
            "User email body",
            None,
            ["jane@example.com"],
        )

        mock_email_message.return_value.send.assert_called_once_with()

        mock_mail_admins.assert_called_once_with(
            "New message",
            "Admin email body",
        )

    @patch("api.views.mail_admins")
    @patch("api.views.EmailMessage")
    @patch("api.views.render_to_string")
    def test_user_email_template_receives_name(
        self,
        mock_render_to_string,
        mock_email_message,
        mock_mail_admins,
    ):
        data = {
            "name": "Alice",
            "email": "alice@example.com",
            "message": "Hello!",
        }

        mock_render_to_string.side_effect = [
            "User body",
            "Admin body",
        ]

        url = reverse("api:message")

        self.client.post(
            url,
            data,
            format="json",
        )

        mock_render_to_string.assert_any_call(
            "email/message_user.txt",
            {"user": "Alice"},
        )

    @patch("api.views.mail_admins")
    @patch("api.views.EmailMessage")
    @patch("api.views.render_to_string")
    def test_admin_email_template_receives_name_and_message(
        self,
        mock_render_to_string,
        mock_email_message,
        mock_mail_admins,
    ):
        data = {
            "name": "Bob",
            "email": "bob@example.com",
            "message": "This is my message.",
        }

        mock_render_to_string.side_effect = [
            "User body",
            "Admin body",
        ]

        url = reverse("api:message")

        self.client.post(
            url,
            data,
            format="json",
        )

        mock_render_to_string.assert_any_call(
            "email/message_admin.txt",
            {
                "user": "Bob",
                "message": "This is my message.",
            },
        )

    @patch("api.views.mail_admins")
    @patch("api.views.EmailMessage")
    @patch("api.views.render_to_string")
    def test_admin_notification_is_sent(
        self,
        mock_render_to_string,
        mock_email_message,
        mock_mail_admins,
    ):
        data = {
            "name": "Admin Test",
            "email": "admin-test@example.com",
            "message": "A message for the site administrators.",
        }

        mock_render_to_string.side_effect = [
            "User body",
            "Admin body",
        ]

        url = reverse("api:message")

        response = self.client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        mock_mail_admins.assert_called_once_with(
            "New message",
            "Admin body",
        )

    @patch("api.views.mail_admins")
    @patch("api.views.EmailMessage")
    @patch("api.views.render_to_string")
    def test_user_email_is_sent_before_admin_notification(
        self,
        mock_render_to_string,
        mock_email_message,
        mock_mail_admins,
    ):
        data = {
            "name": "Order Test",
            "email": "order@example.com",
            "message": "Please help me.",
        }

        mock_render_to_string.side_effect = [
            "User body",
            "Admin body",
        ]

        call_order = []

        mock_email_message.return_value.send.side_effect = lambda: call_order.append(
            "user_email"
        )
        mock_mail_admins.side_effect = lambda *args: call_order.append("admin_email")

        url = reverse("api:message")

        response = self.client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert call_order == ["user_email", "admin_email"]

    @patch("api.views.mail_admins")
    @patch("api.views.EmailMessage")
    @patch("api.views.render_to_string")
    def test_empty_message_is_accepted_by_current_view(
        self,
        mock_render_to_string,
        mock_email_message,
        mock_mail_admins,
    ):
        data = {
            "name": "Empty Message",
            "email": "empty@example.com",
            "message": "",
        }

        mock_render_to_string.side_effect = [
            "User body",
            "Admin body",
        ]

        url = reverse("api:message")

        response = self.client.post(
            url,
            data,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == "sent"

        mock_mail_admins.assert_called_once_with(
            "New message",
            "Admin body",
        )

    def test_missing_name_raises_key_error(self):
        data = {
            "email": "missing-name@example.com",
            "message": "Hello",
        }

        url = reverse("api:message")

        with patch("api.views.EmailMessage"), patch("api.views.render_to_string"):
            try:
                self.client.post(
                    url,
                    data,
                    format="json",
                )
            except KeyError as exc:
                assert exc.args == ("name",)
            else:
                raise AssertionError("Expected KeyError was not raised.")

    def test_missing_email_raises_key_error(self):
        data = {
            "name": "Missing Email",
            "message": "Hello",
        }

        url = reverse("api:message")

        with patch("api.views.EmailMessage"), patch("api.views.render_to_string"):
            try:
                self.client.post(
                    url,
                    data,
                    format="json",
                )
            except KeyError as exc:
                assert exc.args == ("email",)
            else:
                raise AssertionError("Expected KeyError was not raised.")

    def test_missing_message_raises_key_error(self):
        data = {
            "name": "Missing Message",
            "email": "missing-message@example.com",
        }

        url = reverse("api:message")

        with patch("api.views.EmailMessage"), patch("api.views.render_to_string"):
            try:
                self.client.post(
                    url,
                    data,
                    format="json",
                )
            except KeyError as exc:
                assert exc.args == ("message",)
            else:
                raise AssertionError("Expected KeyError was not raised.")
