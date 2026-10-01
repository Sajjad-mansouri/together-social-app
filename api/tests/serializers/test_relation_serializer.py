from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from account.models import Contact, Profile
from api.serializers import RelationSerializer


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
def related_user(db, django_user_model):
    return django_user_model.objects.create_user(
        username="relateduser",
        email="related@example.com",
        password="testpass123",
        first_name="Related",
        last_name="User",
    )


@pytest.fixture
def profile_image():
    image = Image.new("RGB", (10, 10), color="white")
    image_data = BytesIO()
    image.save(image_data, format="JPEG")
    image_data.seek(0)

    return SimpleUploadedFile(
        "profile.jpg",
        image_data.read(),
        content_type="image/jpeg",
    )


@pytest.fixture
def test_profile(test_user, profile_image):
    return Profile.objects.create(
        user=test_user,
        profile_image=profile_image,
    )


class TestRelationSerializerMeta:
    def test_model(self):
        from django.contrib.auth import get_user_model

        assert RelationSerializer.Meta.model is get_user_model()

    def test_fields(self):
        assert RelationSerializer.Meta.fields == [
            "first_name",
            "last_name",
            "username",
            "profile_image",
            "relation",
        ]


class TestRelationSerializerGetRelation:
    def test_following_returns_contact_id(
        self,
        test_user,
        related_user,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=related_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "following",
            },
        )

        assert serializer.get_relation(related_user) == contact.id

    def test_follower_returns_contact_id(
        self,
        test_user,
        related_user,
    ):
        contact = Contact.objects.create(
            from_user=related_user,
            to_user=test_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "follower",
            },
        )

        assert serializer.get_relation(related_user) == contact.id

    def test_following_uses_owner_username(
        self,
        test_user,
        related_user,
        django_user_model,
    ):
        another_user = django_user_model.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpass123",
        )

        Contact.objects.create(
            from_user=test_user,
            to_user=related_user,
            access=True,
        )
        another_contact = Contact.objects.create(
            from_user=another_user,
            to_user=related_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": another_user.username,
                "relation": "following",
            },
        )

        assert serializer.get_relation(related_user) == another_contact.id

    def test_follower_uses_owner_username(
        self,
        test_user,
        related_user,
        django_user_model,
    ):
        another_user = django_user_model.objects.create_user(
            username="anotheruser",
            email="another@example.com",
            password="testpass123",
        )

        Contact.objects.create(
            from_user=related_user,
            to_user=test_user,
            access=True,
        )
        another_contact = Contact.objects.create(
            from_user=related_user,
            to_user=another_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": another_user.username,
                "relation": "follower",
            },
        )

        assert serializer.get_relation(related_user) == another_contact.id


class TestRelationSerializerSerialization:
    def test_serializes_user_fields(
        self,
        test_user,
        test_profile,
        related_user,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=related_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "following",
            },
        )

        assert serializer.data["first_name"] == related_user.first_name
        assert serializer.data["last_name"] == related_user.last_name
        assert serializer.data["username"] == related_user.username

    def test_serializes_profile_image(
        self,
        test_user,
        related_user,
        profile_image,
    ):
        Profile.objects.create(
            user=related_user,
            profile_image=profile_image,
        )
        Contact.objects.create(
            from_user=test_user,
            to_user=related_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "following",
            },
        )

        profile_image_url = serializer.data["profile_image"]

        assert profile_image_url
        assert profile_image_url.startswith("/media/")

    def test_serializes_following_relation(
        self,
        test_user,
        related_user,
        test_profile,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=related_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "following",
            },
        )

        assert serializer.data["relation"] == contact.id

    def test_serializes_follower_relation(
        self,
        test_user,
        related_user,
        test_profile,
    ):
        contact = Contact.objects.create(
            from_user=related_user,
            to_user=test_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "follower",
            },
        )

        assert serializer.data["relation"] == contact.id

    def test_serializes_expected_fields(
        self,
        test_user,
        related_user,
        test_profile,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=related_user,
            access=True,
        )

        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "following",
            },
        )

        assert set(serializer.data) == {
            "first_name",
            "last_name",
            "username",
            "profile_image",
            "relation",
        }


class TestRelationSerializerEdgeCases:
    def test_following_raises_does_not_exist_when_relation_is_missing(
        self,
        test_user,
        related_user,
    ):
        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "following",
            },
        )

        with pytest.raises(Contact.DoesNotExist):
            serializer.get_relation(related_user)

    def test_follower_raises_does_not_exist_when_relation_is_missing(
        self,
        test_user,
        related_user,
    ):
        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "follower",
            },
        )

        with pytest.raises(Contact.DoesNotExist):
            serializer.get_relation(related_user)

    def test_unknown_relation_returns_none(
        self,
        test_user,
        related_user,
    ):
        serializer = RelationSerializer(
            instance=related_user,
            context={
                "owner": test_user.username,
                "relation": "unknown",
            },
        )

        assert serializer.get_relation(related_user) is None
