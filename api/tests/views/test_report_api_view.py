from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from api.views import (
    ReportApiView,
    ReportProblemApiView,
    ReportsView,
)
from social.models import GeneralProblem, Report, ReportProblem


@pytest.mark.django_db
class TestReportsView:
    def test_view_configuration(self):
        assert ReportsView.permission_classes
        assert ReportsView.serializer_class.__name__ == "GeneralReportSerializer"
        assert ReportsView.queryset.model is GeneralProblem

    def test_requires_authentication(self):
        client = APIClient()

        response = client.get(reverse("api:reports"))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_returns_general_problems(self, django_user_model):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        problems = GeneralProblem.objects.create(
            # Add your required GeneralProblem fields here.
        )

        response = client.get(reverse("api:reports"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data[0]["id"] == problems.id

    def test_returns_empty_list_when_no_problems_exist(
        self,
        django_user_model,
    ):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(reverse("api:reports"))

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


@pytest.mark.django_db
class TestReportApiView:
    def test_view_configuration(self):
        assert ReportApiView.permission_classes
        assert ReportApiView.serializer_class.__name__ == "ReportSerializer"
        assert ReportApiView.queryset.model is Report

    def test_requires_authentication(self):
        client = APIClient()

        response = client.post(
            reverse("api:report"),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_report_data_returns_400(
        self,
        django_user_model,
    ):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            reverse("api:report"),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Report.objects.count() == 0


@pytest.mark.django_db
class TestReportProblemApiView:
    def test_view_configuration(self):
        assert ReportProblemApiView.permission_classes
        assert (
            ReportProblemApiView.serializer_class.__name__ == "ReportProblemSerializer"
        )
        assert ReportProblemApiView.queryset.model is ReportProblem

    def test_requires_authentication(self):
        client = APIClient()

        response = client.post(
            reverse("api:report-problem"),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch("api.views.mail_admins")
    @patch("api.views.EmailMessage.send")
    def test_invalid_data_does_not_send_email(
        self,
        mock_send,
        mock_mail_admins,
        django_user_model,
    ):
        user = django_user_model.objects.create_user(
            username="testuser",
            password="testpass123",
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            reverse("api:report-problem"),
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert ReportProblem.objects.count() == 0

        mock_send.assert_not_called()
        mock_mail_admins.assert_not_called()
