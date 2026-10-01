import datetime

import pytest
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from account.models import Contact, Notification


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


@pytest.mark.django_db
class TestContactNotificationSignal:
    def test_creating_contact_with_access_true_creates_notification(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        notification = Notification.objects.get(
            content_type=ContentType.objects.get_for_model(Contact),
            object_id=contact.pk,
        )

        assert notification.user == test_user
        assert notification.content_object == contact
        assert notification.verb == f"{test_user} is following You"

    def test_creating_contact_with_access_false_creates_notification(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        notification = Notification.objects.get(
            content_type=ContentType.objects.get_for_model(Contact),
            object_id=contact.pk,
        )

        assert notification.user == test_user
        assert notification.content_object == contact
        assert notification.verb == f"{test_user} is requesting follow You"

    def test_notification_uses_contact_content_type(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        notification = Notification.objects.get(
            object_id=contact.pk,
        )

        expected_content_type = ContentType.objects.get_for_model(Contact)

        assert notification.content_type == expected_content_type

    def test_notification_points_to_saved_contact(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        notification = Notification.objects.get(
            object_id=contact.pk,
        )

        assert notification.content_object.pk == contact.pk
        assert notification.content_object == contact

    def test_notification_is_created_for_from_user(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        notification = Notification.objects.get(
            content_type=ContentType.objects.get_for_model(Contact),
            object_id=contact.pk,
        )

        assert notification.user_id == test_user.pk
        assert notification.user_id != test_user_2.pk

    def test_notification_is_created_when_contact_is_saved(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        assert not Notification.objects.exists()

        contact.save()

        assert (
            Notification.objects.filter(
                content_type=ContentType.objects.get_for_model(Contact),
                object_id=contact.pk,
            ).count()
            == 1
        )

    def test_saving_same_contact_within_sixty_seconds_does_not_create_duplicate(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        content_type = ContentType.objects.get_for_model(Contact)

        assert (
            Notification.objects.filter(
                user=test_user,
                content_type=content_type,
                object_id=contact.pk,
                verb=f"{test_user} is following You",
            ).count()
            == 1
        )

        contact.save()

        assert (
            Notification.objects.filter(
                user=test_user,
                content_type=content_type,
                object_id=contact.pk,
                verb=f"{test_user} is following You",
            ).count()
            == 1
        )

    def test_saving_contact_with_same_state_within_sixty_seconds_does_not_duplicate(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        contact.save()

        notifications = Notification.objects.filter(
            user=test_user,
            content_type=ContentType.objects.get_for_model(Contact),
            object_id=contact.pk,
            verb=f"{test_user} is requesting follow You",
        )

        assert notifications.count() == 1

    def test_old_similar_notification_does_not_prevent_new_notification(
        self,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        content_type = ContentType.objects.get_for_model(Contact)
        verb = f"{test_user} is following You"

        notification = Notification.objects.get(
            user=test_user,
            content_type=content_type,
            object_id=contact.pk,
            verb=verb,
        )

        notification.created = timezone.now() - datetime.timedelta(seconds=61)
        notification.save(update_fields=["created"])

        contact.save()

        assert (
            Notification.objects.filter(
                user=test_user,
                content_type=content_type,
                object_id=contact.pk,
                verb=verb,
            ).count()
            == 2
        )

    def test_different_contact_can_create_separate_notification(
        self,
        test_user,
        test_user_2,
        django_user_model,
    ):
        test_user_3 = django_user_model.objects.create_user(
            username="testuser3",
            email="test3@example.com",
            password="testpass123",
        )

        contact_1 = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        contact_2 = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_3,
            access=True,
        )

        content_type = ContentType.objects.get_for_model(Contact)
        verb = f"{test_user} is following You"

        notifications = Notification.objects.filter(
            user=test_user,
            content_type=content_type,
            verb=verb,
        )

        assert notifications.count() == 2
        assert {notification.object_id for notification in notifications} == {
            contact_1.pk,
            contact_2.pk,
        }

    def test_access_true_and_false_use_different_verbs(
        self,
        test_user,
        test_user_2,
        django_user_model,
    ):
        test_user_3 = django_user_model.objects.create_user(
            username="testuser3",
            email="test3@example.com",
            password="testpass123",
        )

        following_contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

        request_contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_3,
            access=False,
        )

        content_type = ContentType.objects.get_for_model(Contact)

        following_notification = Notification.objects.get(
            content_type=content_type,
            object_id=following_contact.pk,
        )

        request_notification = Notification.objects.get(
            content_type=content_type,
            object_id=request_contact.pk,
        )

        assert following_notification.verb == f"{test_user} is following You"
        assert request_notification.verb == f"{test_user} is requesting follow You"

        assert following_notification.verb != request_notification.verb
