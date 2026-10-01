import pytest
from django.http import Http404
from django.test import RequestFactory

from account.models import Block
from api.serializers import RestrictionSerializer


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
def serializer_context(test_user):
    request = RequestFactory().get("/")
    request.user = test_user

    return {"request": request}


@pytest.mark.django_db
class TestRestrictionSerializer:
    def test_meta_model(self):
        assert RestrictionSerializer.Meta.model is Block

    def test_meta_fields(self):
        assert RestrictionSerializer.Meta.fields == [
            "id",
            "from_user",
            "to_user",
        ]

    def test_serialization(
        self,
        test_user,
        test_user_2,
    ):
        block = Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        serializer = RestrictionSerializer(block)

        assert serializer.data == {
            "id": block.id,
            "from_user": test_user.id,
            "to_user": test_user_2.id,
        }

    def test_to_internal_value_sets_request_user(
        self,
        serializer_context,
        test_user,
        test_user_2,
    ):
        serializer = RestrictionSerializer(
            data={"to_user": test_user_2.username},
            context=serializer_context,
        )

        assert serializer.is_valid()

        assert serializer.validated_data["from_user"] == test_user

    def test_to_internal_value_converts_username_to_user(
        self,
        serializer_context,
        test_user_2,
    ):
        serializer = RestrictionSerializer(
            data={"to_user": test_user_2.username},
            context=serializer_context,
        )

        assert serializer.is_valid()

        assert serializer.validated_data["to_user"] == test_user_2

    def test_submitted_from_user_is_replaced(
        self,
        serializer_context,
        test_user,
        test_user_2,
    ):
        serializer = RestrictionSerializer(
            data={
                "from_user": test_user_2.id,
                "to_user": test_user_2.username,
            },
            context=serializer_context,
        )

        assert serializer.is_valid()

        assert serializer.validated_data["from_user"] == test_user

    def test_valid_data_can_create_block(
        self,
        serializer_context,
        test_user,
        test_user_2,
    ):
        serializer = RestrictionSerializer(
            data={"to_user": test_user_2.username},
            context=serializer_context,
        )

        assert serializer.is_valid()

        block = serializer.save()

        assert block.from_user == test_user
        assert block.to_user == test_user_2

    def test_created_block_is_persisted(
        self,
        serializer_context,
        test_user,
        test_user_2,
    ):
        serializer = RestrictionSerializer(
            data={"to_user": test_user_2.username},
            context=serializer_context,
        )

        assert serializer.is_valid()

        block = serializer.save()

        assert Block.objects.filter(pk=block.pk).exists()

    def test_to_user_is_required(
        self,
        serializer_context,
    ):
        serializer = RestrictionSerializer(
            data={},
            context=serializer_context,
        )

        assert serializer.is_valid() is False
        assert "to_user" in serializer.errors

    def test_unknown_username_raises_404(
        self,
        serializer_context,
    ):
        serializer = RestrictionSerializer(
            data={"to_user": "does-not-exist"},
            context=serializer_context,
        )

        with pytest.raises(Http404):
            serializer.is_valid()
