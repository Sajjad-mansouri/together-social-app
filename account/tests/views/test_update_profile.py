from datetime import date
from unittest.mock import patch

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse

from account.forms import ProfileForm, UserForm
from account.models import Profile
from account.views import UpdateProfile


@pytest.fixture
def test_user(db, django_user_model):
    user = django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Old",
        last_name="Name",
    )
    Profile.objects.create(
        user=user,
        birth_day=date(2000, 1, 1),
        bio="Old bio",
    )
    return user


@pytest.fixture
def test_user_2(db, django_user_model):
    user = django_user_model.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass123",
        first_name="Second",
        last_name="User",
    )
    Profile.objects.create(
        user=user,
        birth_day=date(1995, 5, 10),
        bio="Second bio",
    )
    return user


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def update_profile_view():
    return UpdateProfile()


class TestUpdateProfile:
    def test_model_is_user_model(self, update_profile_view, django_user_model):
        assert update_profile_view.model is django_user_model

    def test_form_class_is_user_form(self, update_profile_view):
        assert update_profile_view.form_class is UserForm

    def test_template_name_is_correct(self, update_profile_view):
        assert update_profile_view.template_name == ("social/update-profile.html")

    def test_success_message_is_correct(self, update_profile_view):
        assert update_profile_view.success_message == "Profile successfully Updated"

    def test_get_object_returns_authenticated_user(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.get("/edit-profile/")
        request.user = test_user

        update_profile_view.setup(request)

        assert update_profile_view.get_object() == test_user

    def test_get_object_ignores_url_pk(
        self,
        update_profile_view,
        request_factory,
        test_user,
        test_user_2,
    ):
        request = request_factory.get(
            f"/edit-profile/{test_user_2.pk}/",
        )
        request.user = test_user

        update_profile_view.setup(
            request,
            pk=test_user_2.pk,
        )

        assert update_profile_view.get_object() == test_user
        assert update_profile_view.get_object() != test_user_2

    def test_get_success_url_uses_social_profile_url(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.get("/edit-profile/")
        request.user = test_user

        update_profile_view.setup(request)

        expected_url = reverse("social:profile")

        assert update_profile_view.get_success_url() == expected_url

    def test_get_context_data_contains_profile_form(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.get("/edit-profile/")
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        context = update_profile_view.get_context_data()

        assert "form" in context
        assert "user_form" in context
        assert isinstance(context["form"], UserForm)
        assert isinstance(context["user_form"], ProfileForm)

    def test_get_context_data_profile_form_uses_user_profile(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.get("/edit-profile/")
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        context = update_profile_view.get_context_data()

        assert context["user_form"].instance == test_user.profile

    @patch("account.views.ProfileForm")
    def test_get_context_data_creates_profile_form(
        self,
        mock_profile_form,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.get("/edit-profile/")
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        update_profile_view.get_context_data()

        mock_profile_form.assert_called_once_with(
            instance=test_user.profile,
        )

    @patch("account.views.messages.success")
    def test_post_updates_user_and_profile(
        self,
        mock_success,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": "Updated",
                "last_name": "User",
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "2004-04-04",
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        response = update_profile_view.post(request)

        test_user.refresh_from_db()
        test_user.profile.refresh_from_db()

        assert response.status_code == 302
        assert response.url == reverse("social:profile")

        assert test_user.first_name == "Updated"
        assert test_user.last_name == "User"
        assert test_user.email == "test@example.com"

        assert test_user.profile.birth_day == date(2004, 4, 4)

        mock_success.assert_called_once_with(
            request,
            "Profile successfully Updated",
        )

    @patch("account.views.messages.success")
    def test_post_updates_only_authenticated_users_profile(
        self,
        mock_success,
        update_profile_view,
        request_factory,
        test_user,
        test_user_2,
    ):
        original_user_2_first_name = test_user_2.first_name
        original_user_2_birth_day = test_user_2.profile.birth_day

        request = request_factory.post(
            f"/edit-profile/{test_user_2.pk}/",
            data={
                "first_name": "Changed",
                "last_name": "User",
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "2002-06-15",
            },
        )
        request.user = test_user

        update_profile_view.setup(
            request,
            pk=test_user_2.pk,
        )
        update_profile_view.object = test_user

        response = update_profile_view.post(request)

        test_user.refresh_from_db()
        test_user_2.refresh_from_db()
        test_user.profile.refresh_from_db()
        test_user_2.profile.refresh_from_db()

        assert response.status_code == 302
        assert response.url == reverse("social:profile")

        assert test_user.first_name == "Changed"
        assert test_user.profile.birth_day == date(2002, 6, 15)

        assert test_user_2.first_name == original_user_2_first_name
        assert test_user_2.profile.birth_day == original_user_2_birth_day

        mock_success.assert_called_once_with(
            request,
            "Profile successfully Updated",
        )

    @patch("account.views.ProfileForm")
    def test_post_passes_profile_instance_to_profile_form(
        self,
        mock_profile_form,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": test_user.first_name,
                "last_name": test_user.last_name,
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "2000-01-01",
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        profile_form = mock_profile_form.return_value
        profile_form.is_valid.return_value = False

        update_profile_view.post(request)

        first_call = mock_profile_form.call_args_list[0]

        assert first_call.kwargs["instance"] == test_user.profile

    @patch("account.views.ProfileForm")
    def test_post_passes_request_data_to_profile_form(
        self,
        mock_profile_form,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request_data = {
            "first_name": test_user.first_name,
            "last_name": test_user.last_name,
            "username": test_user.username,
            "email": test_user.email,
            "birth_day": "2000-01-01",
        }

        request = request_factory.post(
            "/edit-profile/",
            data=request_data,
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        profile_form = mock_profile_form.return_value
        profile_form.is_valid.return_value = False

        update_profile_view.post(request)

        first_call = mock_profile_form.call_args_list[0]

        assert first_call.kwargs["data"] is request.POST

    def test_post_passes_request_files_to_profile_form(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        image = SimpleUploadedFile(
            "profile.jpg",
            b"fake-image-content",
            content_type="image/jpeg",
        )

        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": test_user.first_name,
                "last_name": test_user.last_name,
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "2000-01-01",
                "profile_image": image,
            },
        )
        request.user = test_user

        assert "profile_image" in request.FILES

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        with patch("account.views.ProfileForm") as profile_form_class:
            profile_form = profile_form_class.return_value
            profile_form.is_valid.return_value = False

            update_profile_view.post(request)

            first_call = profile_form_class.call_args_list[0]

            assert first_call.kwargs["files"] is request.FILES
            assert "profile_image" in first_call.kwargs["files"]

    def test_post_invalid_profile_form_does_not_update_profile(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        original_birth_day = date(2000, 1, 1)

        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": test_user.first_name,
                "last_name": test_user.last_name,
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "not-a-valid-date",
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        response = update_profile_view.post(request)

        test_user.refresh_from_db()
        test_user.profile.refresh_from_db()

        assert response.status_code == 200
        assert test_user.profile.birth_day == original_birth_day

    def test_post_invalid_profile_form_does_not_update_user(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        original_first_name = test_user.first_name
        original_last_name = test_user.last_name

        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": "Changed",
                "last_name": "User",
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "not-a-valid-date",
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        response = update_profile_view.post(request)

        test_user.refresh_from_db()

        assert response.status_code == 200
        assert test_user.first_name == original_first_name
        assert test_user.last_name == original_last_name

    def test_post_invalid_profile_form_returns_profile_form_errors(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": test_user.first_name,
                "last_name": test_user.last_name,
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "not-a-valid-date",
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        response = update_profile_view.post(request)

        assert response.status_code == 200

        context = response.context_data

        assert "user_form" in context
        assert context["user_form"].errors
        assert "birth_day" in context["user_form"].errors

    @patch("account.views.messages.success")
    def test_post_sets_profile_user_to_authenticated_user(
        self,
        mock_success,
        update_profile_view,
        request_factory,
        test_user,
    ):
        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": test_user.first_name,
                "last_name": test_user.last_name,
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "2001-01-01",
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        response = update_profile_view.post(request)

        test_user.profile.refresh_from_db()

        assert response.status_code == 302
        assert test_user.profile.user == test_user

        mock_success.assert_called_once_with(
            request,
            "Profile successfully Updated",
        )

    def test_post_updates_profile_image(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        from io import BytesIO

        from PIL import Image

        image_file = BytesIO()
        image = Image.new("RGB", (10, 10), "white")
        image.save(image_file, format="PNG")
        image_file.seek(0)

        image = SimpleUploadedFile(
            "new-profile.png",
            image_file.getvalue(),
            content_type="image/png",
        )

        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": test_user.first_name,
                "last_name": test_user.last_name,
                "username": test_user.username,
                "email": test_user.email,
                "birth_day": "2003-03-03",
                "profile_image": image,
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        with patch("account.views.messages.success"):
            response = update_profile_view.post(request)

        test_user.profile.refresh_from_db()

        assert response.status_code == 302
        assert response.url == reverse("social:profile")
        assert test_user.profile.profile_image
        assert test_user.profile.profile_image.name != (
            "profile_image/default/blank-profile.png"
        )

    def test_post_invalid_user_form_does_not_update_profile(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        original_first_name = test_user.first_name
        original_birth_day = test_user.profile.birth_day

        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": "Changed",
                "last_name": "User",
                "username": "",
                "email": test_user.email,
                "birth_day": "2005-05-05",
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        response = update_profile_view.post(request)

        test_user.refresh_from_db()
        test_user.profile.refresh_from_db()

        assert response.status_code == 200

        assert test_user.first_name == original_first_name
        assert test_user.profile.birth_day == original_birth_day

    def test_post_invalid_user_form_does_not_update_user(
        self,
        update_profile_view,
        request_factory,
        test_user,
    ):
        original_first_name = test_user.first_name
        original_last_name = test_user.last_name

        request = request_factory.post(
            "/edit-profile/",
            data={
                "first_name": "Changed",
                "last_name": "Changed",
                "username": "",
                "email": test_user.email,
                "birth_day": "2005-05-05",
            },
        )
        request.user = test_user

        update_profile_view.setup(request)
        update_profile_view.object = test_user

        response = update_profile_view.post(request)

        test_user.refresh_from_db()

        assert response.status_code == 200
        assert test_user.first_name == original_first_name
        assert test_user.last_name == original_last_name
