import pytest
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.test import RequestFactory

from account.models import Block, Contact
from social.models import Message, Report
from social.views import Profile


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
def test_message_2(test_user):
    return Message.objects.create(
        user=test_user,
        text="Second test message",
    )


@pytest.fixture
def test_message_3(test_user_2):
    return Message.objects.create(
        user=test_user_2,
        text="User 2 message",
    )


@pytest.fixture
def message_content_type():
    return ContentType.objects.get_for_model(Message)


@pytest.fixture
def profile_request(test_user):
    request = RequestFactory().get("/profile/")
    request.user = test_user
    return request


@pytest.fixture
def profile_view(profile_request):
    view = Profile()
    view.setup(profile_request)

    # This is normally populated by ListView.get().
    # The tests call get_queryset() directly, so initialize
    # object_list to reproduce the normal ListView lifecycle.
    view.object_list = view.get_queryset()

    return view


@pytest.mark.django_db
class TestProfile:
    def test_template_name(self):
        assert Profile.template_name == "together/profile.html"

    def test_get_queryset_uses_authenticated_user_as_default_owner(
        self,
        profile_view,
        test_user,
        test_message,
    ):
        queryset = profile_view.get_queryset()

        assert profile_view.owner == test_user
        assert list(queryset) == [test_message]

    def test_get_queryset_uses_username_from_url(
        self,
        profile_request,
        test_user,
        test_user_2,
        test_message_3,
    ):
        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )

        queryset = view.get_queryset()

        assert view.owner == test_user_2
        assert list(queryset) == [test_message_3]

    def test_get_queryset_returns_only_owner_messages(
        self,
        profile_view,
        test_message,
        test_message_2,
        test_message_3,
    ):
        queryset = profile_view.get_queryset()

        assert test_message in queryset
        assert test_message_2 in queryset
        assert test_message_3 not in queryset

    def test_get_queryset_excludes_reported_messages(
        self,
        profile_view,
        test_user,
        test_message,
        test_message_2,
        message_content_type,
    ):
        Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
            general_report_id=None,
        )

        queryset = profile_view.get_queryset()

        assert test_message not in queryset
        assert test_message_2 in queryset

    def test_get_queryset_excludes_only_reported_messages(
        self,
        profile_view,
        test_user,
        test_message,
        test_message_2,
        message_content_type,
    ):
        Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
            general_report_id=None,
        )

        queryset = profile_view.get_queryset()

        assert list(queryset) == [test_message_2]

    def test_get_queryset_ignores_report_for_different_message(
        self,
        profile_view,
        test_user,
        test_message,
        test_message_2,
        message_content_type,
    ):
        Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message_2.pk,
            general_report_id=None,
        )

        queryset = profile_view.get_queryset()

        assert test_message in queryset
        assert test_message_2 not in queryset

    def test_get_queryset_report_from_another_user_also_excludes_message(
        self,
        profile_view,
        test_user_2,
        test_message,
        test_message_2,
        message_content_type,
    ):
        Report.objects.create(
            user=test_user_2,
            content_type=message_content_type,
            object_id=test_message.pk,
            general_report_id=None,
        )

        queryset = profile_view.get_queryset()

        assert test_message not in queryset
        assert test_message_2 in queryset

    def test_get_queryset_raises_http404_for_unknown_username(
        self,
        profile_request,
    ):
        view = Profile()
        view.setup(
            profile_request,
            username="does-not-exist",
        )

        with pytest.raises(Http404):
            view.get_queryset()

    def test_get_queryset_sets_owner(
        self,
        profile_view,
        test_user,
    ):
        assert profile_view.owner == test_user

    def test_own_profile_has_access(
        self,
        profile_view,
        test_user,
    ):
        context = profile_view.get_context_data()

        assert context["owner"] == test_user
        assert context["access"] is True

    def test_own_profile_is_not_requested(
        self,
        profile_view,
    ):
        context = profile_view.get_context_data()

        assert context["requested"] is False

    def test_own_profile_is_not_blocked(
        self,
        profile_view,
    ):
        context = profile_view.get_context_data()

        assert context["is_block"] is False

    def test_own_profile_has_empty_relationship_ids(
        self,
        profile_view,
    ):
        context = profile_view.get_context_data()

        assert context["contact_id"] == ""
        assert context["requested_id"] == ""

    def test_authenticated_user_with_active_contact_has_access(
        self,
        profile_request,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["owner"] == test_user_2
        assert context["access"] is True
        assert context["requested"] is False
        assert context["is_block"] is False
        assert context["contact_id"] == contact.id
        assert "requested_id" not in context

    def test_authenticated_user_with_pending_request_is_requested(
        self,
        profile_request,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["owner"] == test_user_2
        assert context["access"] is False
        assert context["requested"] is True
        assert context["is_block"] is False
        assert context["requested_id"] == contact.id
        assert "contact_id" not in context

    def test_authenticated_user_without_relationship_has_no_access(
        self,
        profile_request,
        test_user_2,
    ):
        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["owner"] == test_user_2
        assert context["access"] is False
        assert context["requested"] is False
        assert context["is_block"] is False
        assert context["contact_id"] == ""
        assert context["requested_id"] == ""

    def test_authenticated_user_has_contact_id_when_access_is_true(
        self,
        profile_request,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["contact_id"] == contact.id
        assert "requested_id" not in context

    def test_authenticated_user_has_requested_id_when_request_is_pending(
        self,
        profile_request,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["requested_id"] == contact.id
        assert "contact_id" not in context

    def test_authenticated_user_blocking_profile_owner(
        self,
        profile_request,
        test_user,
        test_user_2,
    ):
        Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["is_block"] is True

    def test_authenticated_user_without_block_has_is_block_false(
        self,
        profile_request,
        test_user_2,
    ):
        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["is_block"] is False

    def test_following_count_counts_active_relationships(
        self,
        profile_request,
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
            from_user=test_user_2,
            to_user=test_user_3,
            access=True,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["following_count"] == 2

    def test_follower_count_counts_active_relationships(
        self,
        profile_request,
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
            from_user=test_user_3,
            to_user=test_user_2,
            access=True,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["follower_count"] == 2

    def test_following_count_excludes_pending_relationships(
        self,
        profile_request,
        test_user,
        test_user_2,
        test_user_3,
    ):
        Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user_3,
            access=False,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["following_count"] == 0

    def test_follower_count_excludes_pending_relationships(
        self,
        profile_request,
        test_user,
        test_user_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["follower_count"] == 0

    def test_total_post_counts_all_owner_messages(
        self,
        profile_request,
        test_user_2,
        test_message_3,
    ):
        Message.objects.create(
            user=test_user_2,
            text="Another message",
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["total_post"] == 2

    def test_total_post_counts_reported_messages_too(
        self,
        profile_request,
        test_user,
        test_user_2,
        test_message_3,
        message_content_type,
    ):
        reported_message = Message.objects.create(
            user=test_user_2,
            text="Reported message",
        )

        Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=reported_message.pk,
            general_report_id=None,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert reported_message not in view.object_list
        assert context["total_post"] == 2

    def test_context_contains_expected_common_keys(
        self,
        profile_view,
    ):
        context = profile_view.get_context_data()

        assert context["owner"] is profile_view.owner
        assert "following_count" in context
        assert "follower_count" in context
        assert "total_post" in context
        assert "access" in context
        assert "requested" in context
        assert "is_block" in context

    def test_active_contact_context_does_not_include_requested_id(
        self,
        profile_request,
        test_user,
        test_user_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["access"] is True
        assert context["requested"] is False
        assert "contact_id" in context
        assert "requested_id" not in context

    def test_pending_request_context_does_not_include_contact_id(
        self,
        profile_request,
        test_user,
        test_user_2,
    ):
        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["access"] is False
        assert context["requested"] is True
        assert "requested_id" in context
        assert "contact_id" not in context

    def test_no_relationship_context_contains_empty_ids(
        self,
        profile_request,
        test_user_2,
    ):
        view = Profile()
        view.setup(
            profile_request,
            username=test_user_2.username,
        )
        view.object_list = view.get_queryset()

        context = view.get_context_data()

        assert context["contact_id"] == ""
        assert context["requested_id"] == ""

    def test_owner_is_available_in_context(
        self,
        profile_view,
        test_user,
    ):
        context = profile_view.get_context_data()

        assert context["owner"] == test_user

    def test_get_queryset_uses_message_content_type_for_reports(
        self,
        profile_view,
        test_user,
        test_message,
        message_content_type,
    ):
        Report.objects.create(
            user=test_user,
            content_type=message_content_type,
            object_id=test_message.pk,
            general_report_id=None,
        )

        queryset = profile_view.get_queryset()

        assert not queryset.filter(pk=test_message.pk).exists()
