import pytest
from django.test import RequestFactory

from account.models import Contact, Profile
from api.serializers import ContactSerializer


@pytest.fixture
def test_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_user_2(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser2",
        email="test2@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_user_2_profile(test_user_2):
    return Profile.objects.create(user=test_user_2)


@pytest.fixture
def test_request(test_user):
    request = RequestFactory().post("/api/contacts/")
    request.user = test_user
    return request


class TestContactSerializerMeta:
    def test_model(self):
        assert ContactSerializer.Meta.model is Contact

    def test_fields(self):
        assert ContactSerializer.Meta.fields == [
            "id",
            "from_user",
            "to_user",
            "access",
            "reverse_following",
        ]


class TestContactSerializerReverse:
    def test_returns_false_when_reverse_contact_does_not_exist(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        serializer = ContactSerializer(instance=contact)

        assert serializer.reverse(contact) is False

    def test_returns_true_when_reverse_contact_exists(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
            access=True,
        )

        serializer = ContactSerializer(instance=contact)

        assert serializer.reverse(contact) is True

    def test_reverse_following_is_serialized(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
            access=True,
        )

        serializer = ContactSerializer(instance=contact)

        assert serializer.data["reverse_following"] is True


class TestContactSerializerToInternalValue:
    def test_sets_from_user_to_request_user(
        self,
        test_request,
        test_user,
        test_user_2,
    ):
        serializer = ContactSerializer(
            context={"request": test_request},
        )

        data = {
            "from_user": test_user_2.pk,
            "to_user": test_user_2.pk,
            "access": False,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["from_user"] == test_user

    def test_does_not_trust_submitted_from_user(
        self,
        test_request,
        test_user,
        test_user_2,
    ):
        serializer = ContactSerializer(
            context={"request": test_request},
        )

        data = {
            "from_user": test_user_2.pk,
            "to_user": test_user_2.pk,
            "access": False,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["from_user"] == test_user
        assert internal_data["from_user"] != test_user_2

    def test_partial_update_does_not_replace_from_user(
        self,
        test_request,
        test_user_2,
    ):
        serializer = ContactSerializer(
            context={"request": test_request},
            partial=True,
        )

        data = {
            "from_user": test_user_2.pk,
            "to_user": test_user_2.pk,
            "access": False,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["from_user"] == test_user_2

    def test_partial_update_preserves_submitted_from_user(
        self,
        test_request,
        test_user,
        test_user_2,
    ):
        serializer = ContactSerializer(
            context={"request": test_request},
            partial=True,
        )

        data = {
            "from_user": test_user_2.pk,
            "to_user": test_user_2.pk,
            "access": False,
        }

        internal_data = serializer.to_internal_value(data)

        assert internal_data["from_user"] == test_user_2
        assert internal_data["from_user"] != test_user


class TestContactSerializerCreate:
    def test_create_sets_access_true_for_public_profile(
        self,
        test_request,
        test_user,
        test_user_2,
        test_user_2_profile,
    ):
        test_user_2.profile.private = False
        test_user_2.profile.save()

        serializer = ContactSerializer(
            context={"request": test_request},
        )

        contact = serializer.create(
            {
                "from_user": test_user,
                "to_user": test_user_2,
                "access": False,
            }
        )

        assert contact.from_user == test_user
        assert contact.to_user == test_user_2
        assert contact.access is True

    def test_create_sets_access_false_for_private_profile(
        self,
        test_request,
        test_user,
        test_user_2,
        test_user_2_profile,
    ):
        test_user_2.profile.private = True
        test_user_2.profile.save()

        serializer = ContactSerializer(
            context={"request": test_request},
        )

        contact = serializer.create(
            {
                "from_user": test_user,
                "to_user": test_user_2,
                "access": True,
            }
        )

        assert contact.from_user == test_user
        assert contact.to_user == test_user_2
        assert contact.access is False

    def test_create_overrides_submitted_access_value(
        self,
        test_request,
        test_user,
        test_user_2,
        test_user_2_profile,
    ):
        test_user_2.profile.private = True
        test_user_2.profile.save()

        serializer = ContactSerializer(
            context={"request": test_request},
        )

        contact = serializer.create(
            {
                "from_user": test_user,
                "to_user": test_user_2,
                "access": True,
            }
        )

        assert contact.access is False

    def test_create_persists_contact(
        self,
        test_request,
        test_user,
        test_user_2,
        test_user_2_profile,
    ):
        test_user_2.profile.private = False
        test_user_2.profile.save()

        serializer = ContactSerializer(
            context={"request": test_request},
        )

        contact = serializer.create(
            {
                "from_user": test_user,
                "to_user": test_user_2,
                "access": False,
            }
        )

        assert Contact.objects.filter(
            id=contact.id,
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        ).exists()


class TestContactSerializerRepresentation:
    def test_contains_expected_fields(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        serializer = ContactSerializer(instance=contact)

        assert set(serializer.data) == {
            "id",
            "from_user",
            "to_user",
            "access",
            "reverse_following",
        }

    def test_serializes_contact_values(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        serializer = ContactSerializer(instance=contact)

        assert serializer.data["id"] == contact.id
        assert serializer.data["from_user"] == test_user.id
        assert serializer.data["to_user"] == test_user_2.id
        assert serializer.data["access"] is True
        assert serializer.data["reverse_following"] is False

    def test_serializes_reverse_following_as_true(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
            access=True,
        )

        serializer = ContactSerializer(instance=contact)

        assert serializer.data["reverse_following"] is True


class TestContactSerializerEdgeCases:
    def test_reverse_ignores_access_value(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
            access=False,
        )

        serializer = ContactSerializer(instance=contact)

        assert serializer.reverse(contact) is True
