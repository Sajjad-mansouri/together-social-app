import pytest
from django.contrib.contenttypes.models import ContentType
from django.test import RequestFactory

from account.models import Contact
from api.permissions import AuthorDeletePermission, RelationDeletePermission
from social.models import Comment, Message


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
def test_user_3(db, django_user_model):
    return django_user_model.objects.create_user(
        username="testuser3",
        email="test3@example.com",
        password="testpass123",
    )


@pytest.fixture
def test_message(test_user):
    return Message.objects.create(
        user=test_user,
        text="Test message",
    )


@pytest.fixture
def test_comment(test_user, test_message):
    content_type = ContentType.objects.get_for_model(Message)

    return Comment.objects.create(
        author=test_user,
        comment="Test comment",
        content_type=content_type,
        object_id=test_message.pk,
    )


@pytest.fixture
def request_factory():
    return RequestFactory()


def make_request(request_factory, method, user):
    request = request_factory.generic(
        method,
        "/api/test/",
    )
    request.user = user
    return request


@pytest.mark.django_db
class TestAuthorDeletePermission:
    @pytest.fixture
    def permission(self):
        return AuthorDeletePermission()

    @pytest.mark.parametrize(
        "method",
        ["GET", "HEAD", "OPTIONS"],
    )
    def test_safe_methods_are_allowed_for_any_user(
        self,
        permission,
        request_factory,
        test_user_2,
        test_message,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user_2,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                test_message,
            )
            is True
        )

    @pytest.mark.parametrize(
        "method",
        ["GET", "HEAD", "OPTIONS"],
    )
    def test_safe_methods_are_allowed_for_any_user_on_comment(
        self,
        permission,
        request_factory,
        test_user_2,
        test_comment,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user_2,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                test_comment,
            )
            is True
        )

    @pytest.mark.parametrize(
        "method",
        ["POST", "PUT", "PATCH", "DELETE"],
    )
    def test_message_owner_is_allowed_for_unsafe_methods(
        self,
        permission,
        request_factory,
        test_user,
        test_message,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                test_message,
            )
            is True
        )

    @pytest.mark.parametrize(
        "method",
        ["POST", "PUT", "PATCH", "DELETE"],
    )
    def test_message_non_owner_is_denied_for_unsafe_methods(
        self,
        permission,
        request_factory,
        test_user_2,
        test_message,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user_2,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                test_message,
            )
            is False
        )

    @pytest.mark.parametrize(
        "method",
        ["POST", "PUT", "PATCH", "DELETE"],
    )
    def test_comment_author_is_allowed_for_unsafe_methods(
        self,
        permission,
        request_factory,
        test_user,
        test_comment,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                test_comment,
            )
            is True
        )

    @pytest.mark.parametrize(
        "method",
        ["POST", "PUT", "PATCH", "DELETE"],
    )
    def test_comment_non_author_is_denied_for_unsafe_methods(
        self,
        permission,
        request_factory,
        test_user_2,
        test_comment,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user_2,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                test_comment,
            )
            is False
        )

    def test_comment_permission_uses_author(
        self,
        permission,
        request_factory,
        test_user,
        test_user_2,
        test_comment,
    ):
        assert test_comment.author == test_user

        request = make_request(
            request_factory,
            "DELETE",
            test_user,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                test_comment,
            )
            is True
        )

        request = make_request(
            request_factory,
            "DELETE",
            test_user_2,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                test_comment,
            )
            is False
        )

    def test_permission_uses_message_user_for_non_comment_objects(
        self,
        permission,
        request_factory,
        test_user,
        test_user_2,
        test_message,
    ):
        assert test_message.user == test_user

        owner_request = make_request(
            request_factory,
            "DELETE",
            test_user,
        )

        non_owner_request = make_request(
            request_factory,
            "DELETE",
            test_user_2,
        )

        assert (
            permission.has_object_permission(
                owner_request,
                None,
                test_message,
            )
            is True
        )

        assert (
            permission.has_object_permission(
                non_owner_request,
                None,
                test_message,
            )
            is False
        )


@pytest.mark.django_db
class TestRelationDeletePermission:
    @pytest.fixture
    def permission(self):
        return RelationDeletePermission()

    @pytest.fixture
    def contact(self, test_user, test_user_2):
        return Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

    def test_from_user_is_allowed(
        self,
        permission,
        request_factory,
        test_user,
        contact,
    ):
        request = make_request(
            request_factory,
            "DELETE",
            test_user,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                contact,
            )
            is True
        )

    def test_to_user_is_allowed(
        self,
        permission,
        request_factory,
        test_user_2,
        contact,
    ):
        request = make_request(
            request_factory,
            "DELETE",
            test_user_2,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                contact,
            )
            is True
        )

    def test_unrelated_user_is_denied(
        self,
        permission,
        request_factory,
        test_user_3,
        contact,
    ):
        request = make_request(
            request_factory,
            "DELETE",
            test_user_3,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                contact,
            )
            is False
        )

    @pytest.mark.parametrize(
        "method",
        ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    )
    def test_from_user_is_allowed_regardless_of_method(
        self,
        permission,
        request_factory,
        test_user,
        contact,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                contact,
            )
            is True
        )

    @pytest.mark.parametrize(
        "method",
        ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    )
    def test_to_user_is_allowed_regardless_of_method(
        self,
        permission,
        request_factory,
        test_user_2,
        contact,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user_2,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                contact,
            )
            is True
        )

    @pytest.mark.parametrize(
        "method",
        ["GET", "HEAD", "OPTIONS", "POST", "PUT", "PATCH", "DELETE"],
    )
    def test_unrelated_user_is_denied_regardless_of_method(
        self,
        permission,
        request_factory,
        test_user_3,
        contact,
        method,
    ):
        request = make_request(
            request_factory,
            method,
            test_user_3,
        )

        assert (
            permission.has_object_permission(
                request,
                None,
                contact,
            )
            is False
        )
