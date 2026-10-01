from datetime import date

import pytest

from account.models import Profile
from api.serializers import ProfileSerializer


@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def test_user_2(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass123",
        first_name="Second",
        last_name="User",
    )


@pytest.fixture
def test_profile(test_user):
    return Profile.objects.create(
        user=test_user,
    )


class TestProfileSerializerMeta:
    def test_model(self):
        assert ProfileSerializer.Meta.model is Profile

    def test_fields(self):
        assert ProfileSerializer.Meta.fields == [
            "id",
            "user",
            "profile_image",
            "birth_day",
            "bio",
            "private",
        ]


class TestProfileSerializerSerialization:
    def test_serializes_profile(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        assert serializer.data["id"] == test_profile.id
        assert serializer.data["user"]["username"] == test_user.username
        assert serializer.data["user"]["email"] == test_user.email
        assert serializer.data["user"]["first_name"] == test_user.first_name
        assert serializer.data["user"]["last_name"] == test_user.last_name
        assert serializer.data["birth_day"] == test_profile.birth_day
        assert serializer.data["bio"] == test_profile.bio
        assert serializer.data["private"] == test_profile.private

    def test_contains_expected_fields(self, test_profile):
        serializer = ProfileSerializer(instance=test_profile)

        assert set(serializer.data) == {
            "id",
            "user",
            "profile_image",
            "birth_day",
            "bio",
            "private",
        }

    def test_nested_user_contains_expected_fields(
        self,
        test_profile,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        assert set(serializer.data["user"]) == {
            "first_name",
            "last_name",
            "email",
            "username",
            "profile_image",
        }


class TestProfileSerializerUpdate:
    def test_updates_profile_fields(
        self,
        test_profile,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        validated_data = {
            "private": True,
            "birth_day": date(1995, 5, 10),
            "bio": "Updated biography",
        }

        updated_profile = serializer.update(
            test_profile,
            validated_data,
        )

        assert updated_profile.private is True
        assert updated_profile.birth_day == date(1995, 5, 10)
        assert updated_profile.bio == "Updated biography"

    def test_updates_user_fields(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        validated_data = {
            "user": {
                "first_name": "Updated",
                "last_name": "Name",
                "email": "updated@example.com",
                "username": "updateduser",
            },
        }

        updated_profile = serializer.update(
            test_profile,
            validated_data,
        )

        test_user.refresh_from_db()

        assert updated_profile.user == test_user
        assert test_user.first_name == "Updated"
        assert test_user.last_name == "Name"
        assert test_user.email == "updated@example.com"
        assert test_user.username == "updateduser"

    def test_updates_profile_and_user_fields(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        validated_data = {
            "private": True,
            "birth_day": date(1998, 8, 20),
            "bio": "New biography",
            "user": {
                "first_name": "New",
                "last_name": "User",
                "email": "new@example.com",
                "username": "newusername",
            },
        }

        updated_profile = serializer.update(
            test_profile,
            validated_data,
        )

        test_user.refresh_from_db()
        updated_profile.refresh_from_db()

        assert updated_profile.private is True
        assert updated_profile.birth_day == date(1998, 8, 20)
        assert updated_profile.bio == "New biography"

        assert test_user.first_name == "New"
        assert test_user.last_name == "User"
        assert test_user.email == "new@example.com"
        assert test_user.username == "newusername"

    def test_missing_profile_fields_preserve_existing_values(
        self,
        test_profile,
        test_user,
    ):
        test_profile.private = True
        test_profile.birth_day = date(1990, 1, 1)
        test_profile.bio = "Existing biography"
        test_profile.save()

        original_image = test_profile.profile_image

        serializer = ProfileSerializer(instance=test_profile)

        validated_data = {
            "user": {},
        }

        updated_profile = serializer.update(
            test_profile,
            validated_data,
        )

        test_user.refresh_from_db()
        updated_profile.refresh_from_db()

        assert updated_profile.private is True
        assert updated_profile.birth_day == date(1990, 1, 1)
        assert updated_profile.bio == "Existing biography"
        assert updated_profile.profile_image == original_image

    def test_missing_user_fields_preserve_existing_values(
        self,
        test_profile,
        test_user,
    ):
        original_values = {
            "first_name": test_user.first_name,
            "last_name": test_user.last_name,
            "email": test_user.email,
            "username": test_user.username,
        }

        serializer = ProfileSerializer(instance=test_profile)

        validated_data = {
            "user": {},
        }

        serializer.update(test_profile, validated_data)

        test_user.refresh_from_db()

        assert test_user.first_name == original_values["first_name"]
        assert test_user.last_name == original_values["last_name"]
        assert test_user.email == original_values["email"]
        assert test_user.username == original_values["username"]

    def test_without_user_data_only_updates_profile(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        validated_data = {
            "private": True,
            "bio": "Profile only update",
        }

        serializer.update(test_profile, validated_data)

        test_user.refresh_from_db()
        test_profile.refresh_from_db()

        assert test_profile.private is True
        assert test_profile.bio == "Profile only update"
        assert test_user.first_name == "Test"
        assert test_user.last_name == "User"
        assert test_user.email == "test@example.com"
        assert test_user.username == "testuser"

    def test_update_persists_profile_to_database(
        self,
        test_profile,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        serializer.update(
            test_profile,
            {
                "private": True,
                "bio": "Persisted biography",
            },
        )

        profile = Profile.objects.get(pk=test_profile.pk)

        assert profile.private is True
        assert profile.bio == "Persisted biography"

    def test_update_persists_user_to_database(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        serializer.update(
            test_profile,
            {
                "user": {
                    "first_name": "Persisted",
                    "email": "persisted@example.com",
                },
            },
        )

        user = type(test_user).objects.get(pk=test_user.pk)

        assert user.first_name == "Persisted"
        assert user.email == "persisted@example.com"

    def test_user_object_is_not_replaced(
        self,
        test_profile,
        test_user,
        test_user_2,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        serializer.update(
            test_profile,
            {
                "user": {
                    "first_name": "Changed",
                },
            },
        )

        test_profile.refresh_from_db()

        assert test_profile.user_id == test_user.id
        assert test_profile.user_id != test_user_2.id


class TestProfileSerializerUpdateUserFieldsIndividually:
    def test_updates_only_first_name(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        serializer.update(
            test_profile,
            {
                "user": {
                    "first_name": "UpdatedFirstName",
                },
            },
        )

        test_user.refresh_from_db()

        assert test_user.first_name == "UpdatedFirstName"
        assert test_user.last_name == "User"
        assert test_user.email == "test@example.com"
        assert test_user.username == "testuser"

    def test_updates_only_last_name(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        serializer.update(
            test_profile,
            {
                "user": {
                    "last_name": "UpdatedLastName",
                },
            },
        )

        test_user.refresh_from_db()

        assert test_user.first_name == "Test"
        assert test_user.last_name == "UpdatedLastName"
        assert test_user.email == "test@example.com"
        assert test_user.username == "testuser"

    def test_updates_only_email(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        serializer.update(
            test_profile,
            {
                "user": {
                    "email": "new@example.com",
                },
            },
        )

        test_user.refresh_from_db()

        assert test_user.first_name == "Test"
        assert test_user.last_name == "User"
        assert test_user.email == "new@example.com"
        assert test_user.username == "testuser"

    def test_updates_only_username(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        serializer.update(
            test_profile,
            {
                "user": {
                    "username": "newusername",
                },
            },
        )

        test_user.refresh_from_db()

        assert test_user.first_name == "Test"
        assert test_user.last_name == "User"
        assert test_user.email == "test@example.com"
        assert test_user.username == "newusername"


class TestProfileSerializerEdgeCases:
    def test_empty_user_data_does_not_change_user(
        self,
        test_profile,
        test_user,
    ):
        serializer = ProfileSerializer(instance=test_profile)

        serializer.update(
            test_profile,
            {"user": {}},
        )

        test_user.refresh_from_db()

        assert test_user.first_name == "Test"
        assert test_user.last_name == "User"
        assert test_user.email == "test@example.com"
        assert test_user.username == "testuser"

    def test_empty_validated_data_preserves_profile(
        self,
        test_profile,
    ):
        original_private = test_profile.private
        original_birth_day = test_profile.birth_day
        original_bio = test_profile.bio
        original_image = test_profile.profile_image

        serializer = ProfileSerializer(instance=test_profile)

        updated_profile = serializer.update(
            test_profile,
            {},
        )

        assert updated_profile.private == original_private
        assert updated_profile.birth_day == original_birth_day
        assert updated_profile.bio == original_bio
        assert updated_profile.profile_image == original_image
