import pytest
from django.test import RequestFactory
from rest_framework.exceptions import ValidationError

from api.serializers import ChangePasswordSerializer


@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="OldPassword123!",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def serializer_context(test_user):
    request = RequestFactory().post("/")
    request.user = test_user

    return {"request": request}


class TestChangePasswordSerializer:
    def test_fields(self):
        serializer = ChangePasswordSerializer()

        assert set(serializer.fields) == {
            "old_password",
            "password1",
            "password2",
        }

    def test_all_password_fields_are_required(self):
        serializer = ChangePasswordSerializer()

        assert serializer.fields["old_password"].required is True
        assert serializer.fields["password1"].required is True
        assert serializer.fields["password2"].required is True

    def test_all_password_fields_are_write_only(self):
        serializer = ChangePasswordSerializer()

        assert serializer.fields["old_password"].write_only is True
        assert serializer.fields["password1"].write_only is True
        assert serializer.fields["password2"].write_only is True

    def test_all_password_fields_have_max_length_200(self):
        serializer = ChangePasswordSerializer()

        assert serializer.fields["old_password"].max_length == 200
        assert serializer.fields["password1"].max_length == 200
        assert serializer.fields["password2"].max_length == 200

    def test_to_internal_value_returns_validated_data(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            context=serializer_context,
        )

        data = {
            "old_password": "OldPassword123!",
            "password1": "NewPassword123!",
            "password2": "NewPassword123!",
        }

        result = serializer.to_internal_value(data)

        assert result["old_password"] == "OldPassword123!"
        assert result["password1"] == "NewPassword123!"
        assert result["password2"] == "NewPassword123!"

    def test_valid_password_change(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        assert serializer.is_valid()

        assert serializer.validated_data["old_password"] == "OldPassword123!"
        assert serializer.validated_data["password1"] == "NewPassword123!"
        assert serializer.validated_data["password2"] == "NewPassword123!"

    def test_old_password_is_required(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid()

        assert "old_password" in exc_info.value.detail

    def test_password1_is_required(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid()

        assert "password1" in exc_info.value.detail

    def test_password2_is_required(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid()

        assert "password2" in exc_info.value.detail

    def test_incorrect_old_password(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "WrongPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid()

        assert exc_info.value.detail["old_password"] == ["old password is not correct"]

    def test_correct_old_password_passes_validation(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        assert serializer.is_valid() is True
        assert "old_password" not in serializer.errors

    def test_passwords_must_match(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "DifferentPassword123!",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid()

        assert exc_info.value.detail["non_field_errors"] == ["doesnot match passwords"]

    def test_password_validator_rejects_common_password(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "password",
                "password2": "password",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid()

        assert "non_field_errors" in exc_info.value.detail

    def test_password_validator_rejects_similar_password(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "testuser123",
                "password2": "testuser123",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid()

        assert "non_field_errors" in exc_info.value.detail

    def test_password_validator_rejects_numeric_password(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "12345678",
                "password2": "12345678",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError) as exc_info:
            serializer.is_valid()

        assert "non_field_errors" in exc_info.value.detail

    def test_save_changes_password(
        self,
        test_user,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        assert serializer.is_valid()

        user = serializer.save()

        test_user.refresh_from_db()

        assert user == test_user
        assert test_user.check_password("NewPassword123!")
        assert not test_user.check_password("OldPassword123!")

    def test_save_returns_user(
        self,
        test_user,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        assert serializer.is_valid()

        result = serializer.save()

        assert result == test_user

    def test_save_persists_password_to_database(
        self,
        test_user,
        serializer_context,
        django_user_model,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        assert serializer.is_valid()

        serializer.save()

        user = django_user_model.objects.get(pk=test_user.pk)

        assert user.check_password("NewPassword123!")

    def test_is_valid_always_raises_on_invalid_data(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "WrongPassword123!",
                "password1": "NewPassword123!",
                "password2": "NewPassword123!",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=False)

    def test_is_valid_raises_when_passwords_do_not_match(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
                "password2": "DifferentPassword123!",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=False)

    def test_is_valid_raises_when_required_field_is_missing(
        self,
        serializer_context,
    ):
        serializer = ChangePasswordSerializer(
            data={
                "old_password": "OldPassword123!",
                "password1": "NewPassword123!",
            },
            context=serializer_context,
        )

        with pytest.raises(ValidationError):
            serializer.is_valid(raise_exception=False)
