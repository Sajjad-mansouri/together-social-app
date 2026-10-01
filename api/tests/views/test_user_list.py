import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APIRequestFactory

from account.models import Block, Contact, Profile
from api.serializers import RelationSerializer, SearchSerializer
from api.views import UserListAPiView

UserModel = get_user_model()


@pytest.mark.django_db
class TestUserListAPiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

    @pytest.fixture
    def api_request_factory(self):
        return APIRequestFactory()

    @pytest.fixture
    def test_user(self):
        user = UserModel.objects.create_user(
            username="test_user",
            email="test@example.com",
            password="testpass123",
        )
        Profile.objects.create(user=user)
        return user

    @pytest.fixture
    def test_user_2(self):
        user = UserModel.objects.create_user(
            username="test_user_2",
            email="test2@example.com",
            password="testpass123",
        )
        Profile.objects.create(user=user)
        return user

    @pytest.fixture
    def test_user_3(self):
        user = UserModel.objects.create_user(
            username="test_user_3",
            email="test3@example.com",
            password="testpass123",
        )
        Profile.objects.create(user=user)
        return user

    @pytest.fixture
    def user_list_url(self):
        return reverse("api:user-list")

    def get_request(self, api_request_factory, test_user, query_params=None):
        request = api_request_factory.get(
            "/api/users/",
            query_params or {},
        )
        request.user = test_user
        return request

    # ------------------------------------------------------------------
    # Serializer selection
    # ------------------------------------------------------------------

    def test_get_serializer_class_without_relation(
        self,
        api_request_factory,
        test_user,
    ):
        request = api_request_factory.get(
            "/api/users/",
            {"search": "test"},
        )
        request.user = test_user

        view = UserListAPiView()
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        assert view.get_serializer_class() is SearchSerializer

    def test_get_serializer_class_with_relation(
        self,
        api_request_factory,
        test_user,
    ):
        request = api_request_factory.get(
            "/api/users/",
            {
                "relation": "follower",
                "owner": test_user.username,
            },
        )
        request.user = test_user

        view = UserListAPiView()
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        assert view.get_serializer_class() is RelationSerializer

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def test_search_returns_matching_users(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {"search": "test_user_2"},
        )

        assert response.status_code == 200
        usernames = {item["username"] for item in response.data}

        assert test_user_2.username in usernames

    def test_search_is_case_insensitive(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {"search": "TEST_USER_2"},
        )

        assert response.status_code == 200
        usernames = {item["username"] for item in response.data}

        assert test_user_2.username in usernames

    def test_search_uses_username_prefix(
        self,
        api_client,
        user_list_url,
        test_user,
    ):
        matching_user = UserModel.objects.create_user(
            username="testing_student",
            email="student@example.com",
            password="testpass123",
        )
        Profile.objects.create(user=matching_user)

        non_matching_user = UserModel.objects.create_user(
            username="student_testing",
            email="student2@example.com",
            password="testpass123",
        )
        Profile.objects.create(user=non_matching_user)

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {"search": "testing"},
        )

        assert response.status_code == 200

        usernames = {item["username"] for item in response.data}

        assert matching_user.username in usernames
        assert non_matching_user.username not in usernames

    def test_search_excludes_current_user(
        self,
        api_client,
        user_list_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {"search": "test"},
        )

        assert response.status_code == 200

        usernames = {item["username"] for item in response.data}

        assert test_user.username not in usernames

    def test_search_excludes_users_blocked_by_current_user(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        Block.objects.create(
            from_user=test_user_2,
            to_user=test_user,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {"search": "test"},
        )

        assert response.status_code == 200

        usernames = {item["username"] for item in response.data}

        assert test_user_2.username not in usernames

    def test_search_does_not_exclude_unblocked_users(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {"search": "test"},
        )

        assert response.status_code == 200

        usernames = {item["username"] for item in response.data}

        assert test_user_2.username in usernames

    def test_search_returns_empty_list_when_no_user_matches(
        self,
        api_client,
        user_list_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {"search": "does-not-exist"},
        )

        assert response.status_code == 200
        assert response.data == []

    # ------------------------------------------------------------------
    # Followers
    # ------------------------------------------------------------------

    def test_follower_relation_returns_followers_with_access(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
        test_user_3,
    ):
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user_3,
            to_user=test_user,
            access=False,
        )

        api_client.force_authenticate(user=test_user_3)

        response = api_client.get(
            user_list_url,
            {
                "relation": "follower",
                "owner": test_user.username,
            },
        )

        assert response.status_code == 200

        usernames = {item["username"] for item in response.data}

        assert test_user_2.username in usernames
        assert test_user_3.username not in usernames

    def test_follower_relation_uses_owner_not_authenticated_user(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
        test_user_3,
    ):
        Contact.objects.create(
            from_user=test_user_3,
            to_user=test_user_2,
            access=True,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "follower",
                "owner": test_user_2.username,
            },
        )

        assert response.status_code == 200

        usernames = {item["username"] for item in response.data}

        assert test_user_3.username in usernames

    def test_follower_relation_excludes_inaccessible_followers(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
            access=False,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "follower",
                "owner": test_user.username,
            },
        )

        assert response.status_code == 200
        assert response.data == []

    # ------------------------------------------------------------------
    # Following
    # ------------------------------------------------------------------

    def test_following_relation_returns_followed_users_with_access(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
        test_user_3,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_3,
            access=False,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "following",
                "owner": test_user.username,
            },
        )

        assert response.status_code == 200

        usernames = {item["username"] for item in response.data}

        assert test_user_2.username in usernames
        assert test_user_3.username not in usernames

    def test_following_relation_uses_owner_not_authenticated_user(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
        test_user_3,
    ):
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user_3,
            access=True,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "following",
                "owner": test_user_2.username,
            },
        )

        assert response.status_code == 200

        usernames = {item["username"] for item in response.data}

        assert test_user_3.username in usernames

    def test_following_relation_excludes_inaccessible_following_users(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "following",
                "owner": test_user.username,
            },
        )

        assert response.status_code == 200
        assert response.data == []

    # ------------------------------------------------------------------
    # Relation owner
    # ------------------------------------------------------------------

    def test_follower_with_unknown_owner_returns_404(
        self,
        api_client,
        user_list_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "follower",
                "owner": "does-not-exist",
            },
        )

        assert response.status_code == 404

    def test_following_with_unknown_owner_returns_404(
        self,
        api_client,
        user_list_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "following",
                "owner": "does-not-exist",
            },
        )

        assert response.status_code == 404

    # ------------------------------------------------------------------
    # Serializer context
    # ------------------------------------------------------------------

    def test_relation_context_contains_relation_and_owner(
        self,
        api_request_factory,
        test_user,
    ):
        request = api_request_factory.get(
            "/api/users/",
            {
                "relation": "follower",
                "owner": test_user.username,
            },
        )
        request.user = test_user

        view = UserListAPiView()
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        context = view.get_serializer_context()

        assert context["relation"] == "follower"
        assert context["owner"] == test_user.username

    def test_context_contains_following_relation(
        self,
        api_request_factory,
        test_user,
    ):
        request = api_request_factory.get(
            "/api/users/",
            {
                "relation": "following",
                "owner": test_user.username,
            },
        )
        request.user = test_user

        view = UserListAPiView()
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        context = view.get_serializer_context()

        assert context["relation"] == "following"
        assert context["owner"] == test_user.username

    def test_context_does_not_add_relation_without_relation_parameter(
        self,
        api_request_factory,
        test_user,
    ):
        request = api_request_factory.get(
            "/api/users/",
            {"search": "test"},
        )
        request.user = test_user

        view = UserListAPiView()
        view.request = view.initialize_request(request)
        view.format_kwarg = None

        context = view.get_serializer_context()

        assert "relation" not in context
        assert "owner" not in context

    # ------------------------------------------------------------------
    # Search serializer response
    # ------------------------------------------------------------------

    def test_search_response_contains_expected_fields(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {"search": "test_user_2"},
        )

        assert response.status_code == 200
        assert len(response.data) == 1

        item = response.data[0]

        assert set(item) == {
            "first_name",
            "last_name",
            "username",
            "profile_image",
        }
        assert item["username"] == test_user_2.username

    # ------------------------------------------------------------------
    # Relation serializer response
    # ------------------------------------------------------------------

    def test_follower_response_contains_relation_field(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
            access=True,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "follower",
                "owner": test_user.username,
            },
        )

        assert response.status_code == 200
        assert len(response.data) == 1

        item = response.data[0]

        assert set(item) == {
            "first_name",
            "last_name",
            "username",
            "profile_image",
            "relation",
        }
        assert item["username"] == test_user_2.username
        assert item["relation"] == (
            Contact.objects.get(
                from_user=test_user_2,
                to_user=test_user,
            ).id
        )

    def test_following_response_contains_relation_field(
        self,
        api_client,
        user_list_url,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            user_list_url,
            {
                "relation": "following",
                "owner": test_user.username,
            },
        )

        assert response.status_code == 200
        assert len(response.data) == 1

        item = response.data[0]

        assert set(item) == {
            "first_name",
            "last_name",
            "username",
            "profile_image",
            "relation",
        }
        assert item["username"] == test_user_2.username
        assert item["relation"] == contact.id
