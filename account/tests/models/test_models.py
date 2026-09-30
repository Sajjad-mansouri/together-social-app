from datetime import date

import pytest
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from account.models import Block, Contact, MyUser, Notification, Profile

pytestmark = pytest.mark.django_db


class TestMyUser:
    def test_create_user(self, django_user_model):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

        assert test_user.pk is not None
        assert test_user.username == "test_user"
        assert test_user.email == "test_user@example.com"
        assert test_user.check_password("test_password")
        assert test_user.is_active is True
        assert test_user.is_staff is False
        assert test_user.is_superuser is False

    def test_password_is_hashed(self, django_user_model):
        test_password = "test_password"

        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password=test_password,
        )

        assert test_user.password != test_password
        assert test_user.check_password(test_password)

    def test_email_is_required(self, django_user_model):
        test_user = django_user_model(
            username="test_user",
        )

        with pytest.raises(ValidationError):
            test_user.full_clean()

    def test_email_must_be_unique(self, django_user_model):
        django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

        duplicate_user = django_user_model(
            username="test_user_2",
            email="test_user@example.com",
        )

        with pytest.raises(ValidationError):
            duplicate_user.full_clean()

    def test_duplicate_email_cannot_be_saved(self, django_user_model):
        django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

        duplicate_user = django_user_model(
            username="test_user_2",
            email="test_user@example.com",
        )

        with pytest.raises(IntegrityError):
            duplicate_user.save()

    def test_email_normalization(self, django_user_model):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="Test_User@Example.COM",
            password="test_password",
        )

        test_user.refresh_from_db()

        assert test_user.email == "Test_User@example.com"

    def test_inherits_standard_user_fields(self, django_user_model):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
            first_name="test_first_name",
            last_name="test_last_name",
        )

        assert test_user.first_name == "test_first_name"
        assert test_user.last_name == "test_last_name"
        assert test_user.get_full_name() == "test_first_name test_last_name"

    def test_user_can_be_authenticated_with_created_password(
        self,
        django_user_model,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

        assert test_user.check_password("test_password") is True
        assert test_user.check_password("wrong_password") is False


class TestProfile:
    @pytest.fixture
    def test_user(self, django_user_model):
        return django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

    @pytest.fixture
    def test_profile(self, test_user):
        return Profile.objects.create(user=test_user)

    def test_create_profile(self, test_user):
        test_profile = Profile.objects.create(user=test_user)

        assert test_profile.pk is not None
        assert test_profile.user == test_user

    def test_default_values(self, test_profile):
        assert test_profile.bio == ""
        assert test_profile.link == ""
        assert test_profile.private is False
        assert test_profile.birth_day is None

    def test_profile_user_relationship(self, test_profile, test_user):
        assert test_profile.user_id == test_user.pk
        assert test_user.profile == test_profile

    def test_user_can_have_only_one_profile(self, test_user):
        Profile.objects.create(user=test_user)

        duplicate_profile = Profile(user=test_user)

        with pytest.raises(ValidationError):
            duplicate_profile.full_clean()

    def test_profile_requires_user(self):
        test_profile = Profile()

        with pytest.raises(ValidationError):
            test_profile.full_clean()

    def test_str_returns_username(self, test_profile, test_user):
        assert str(test_profile) == f"profile:{test_user.username}"

    def test_bio_can_contain_text(self, test_user):
        test_bio = "test bio"

        test_profile = Profile.objects.create(
            user=test_user,
            bio=test_bio,
        )

        assert test_profile.bio == test_bio

    def test_bio_can_be_empty(self, test_user):
        test_profile = Profile.objects.create(
            user=test_user,
            bio="",
        )

        test_profile.full_clean()

        assert test_profile.bio == ""

    def test_link_can_be_empty(self, test_user):
        test_profile = Profile.objects.create(
            user=test_user,
            link="",
        )

        test_profile.full_clean()

        assert test_profile.link == ""

    def test_valid_link(self, test_user):
        test_profile = Profile.objects.create(
            user=test_user,
            link="https://example.com",
        )

        test_profile.full_clean()

        assert test_profile.link == "https://example.com"

    def test_invalid_link(self, test_user):
        test_profile = Profile(
            user=test_user,
            link="invalid-url",
        )

        with pytest.raises(ValidationError):
            test_profile.full_clean()

    def test_private_defaults_to_false(self, test_profile):
        assert test_profile.private is False

    def test_private_can_be_enabled(self, test_user):
        test_profile = Profile.objects.create(
            user=test_user,
            private=True,
        )

        assert test_profile.private is True

    def test_birth_day_can_be_empty(self, test_profile):
        assert test_profile.birth_day is None

    def test_birth_day_accepts_valid_date(self, test_user):
        test_birth_day = date(2000, 1, 1)

        test_profile = Profile.objects.create(
            user=test_user,
            birth_day=test_birth_day,
        )

        assert test_profile.birth_day == test_birth_day

    def test_profile_image_can_be_empty(self, test_user):
        test_profile = Profile.objects.create(
            user=test_user,
            profile_image=None,
        )

        test_profile.refresh_from_db()

        assert not test_profile.profile_image

    def test_profile_image_accepts_file_value(self, test_user):
        from django.core.files.uploadedfile import SimpleUploadedFile

        test_image = SimpleUploadedFile(
            name="test_image.jpg",
            content=b"test image content",
            content_type="image/jpeg",
        )

        test_profile = Profile.objects.create(
            user=test_user,
            profile_image=test_image,
        )

        assert test_profile.profile_image
        assert test_profile.profile_image.name.startswith("profile_image/")

    def test_profile_is_deleted_with_user(
        self,
        django_user_model,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_profile = Profile.objects.create(user=test_user)
        test_profile_id = test_profile.pk

        test_user.delete()

        assert not Profile.objects.filter(pk=test_profile_id).exists()


class TestContact:
    @pytest.fixture
    def test_users(self, django_user_model):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_user_2 = django_user_model.objects.create_user(
            username="test_user_2",
            email="test_user_2@example.com",
            password="test_password",
        )

        return test_user, test_user_2

    @pytest.fixture
    def test_contact(self, test_users):
        test_user, test_user_2 = test_users

        return Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

    def test_create_contact(self, test_users):
        test_user, test_user_2 = test_users

        test_contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        assert test_contact.pk is not None
        assert test_contact.from_user == test_user
        assert test_contact.to_user == test_user_2

    def test_access_defaults_to_true(self, test_contact):
        assert test_contact.access is True

    def test_access_can_be_disabled(self, test_users):
        test_user, test_user_2 = test_users

        test_contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=False,
        )

        assert test_contact.access is False

    def test_created_is_set_automatically(self, test_users):
        test_user, test_user_2 = test_users
        before = timezone.now()

        test_contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        after = timezone.now()

        assert before <= test_contact.created <= after

    def test_same_user_pair_cannot_have_duplicate_contact(
        self,
        test_users,
    ):
        test_user, test_user_2 = test_users

        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        with pytest.raises(IntegrityError):
            Contact.objects.create(
                from_user=test_user,
                to_user=test_user_2,
            )

    def test_reverse_contact_is_allowed(self, test_users):
        test_user, test_user_2 = test_users

        Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        test_reverse_contact = Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
        )

        assert test_reverse_contact.pk is not None
        assert Contact.objects.count() == 2

    def test_self_contact_is_allowed_by_current_model(
        self,
        django_user_model,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

        test_contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user,
        )

        assert test_contact.from_user == test_user
        assert test_contact.to_user == test_user

    def test_from_user_reverse_relation(self, test_contact, test_users):
        test_user, _ = test_users

        assert test_contact in test_user.rel_from.all()

    def test_to_user_reverse_relation(self, test_contact, test_users):
        _, test_user_2 = test_users

        assert test_contact in test_user_2.rel_to.all()

    def test_contact_is_deleted_with_from_user(
        self,
        test_users,
    ):
        test_user, test_user_2 = test_users

        test_contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )
        test_contact_id = test_contact.pk

        test_user.delete()

        assert not Contact.objects.filter(pk=test_contact_id).exists()

    def test_contact_is_deleted_with_to_user(
        self,
        test_users,
    ):
        test_user, test_user_2 = test_users

        test_contact = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )
        test_contact_id = test_contact.pk

        test_user_2.delete()

        assert not Contact.objects.filter(pk=test_contact_id).exists()


class TestBlock:
    @pytest.fixture
    def test_users(self, django_user_model):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_user_2 = django_user_model.objects.create_user(
            username="test_user_2",
            email="test_user_2@example.com",
            password="test_password",
        )

        return test_user, test_user_2

    @pytest.fixture
    def test_block(self, test_users):
        test_user, test_user_2 = test_users

        return Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

    def test_create_block(self, test_users):
        test_user, test_user_2 = test_users

        test_block = Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        assert test_block.pk is not None
        assert test_block.from_user == test_user
        assert test_block.to_user == test_user_2

    def test_created_is_set_automatically(self, test_users):
        test_user, test_user_2 = test_users
        before = timezone.now()

        test_block = Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        after = timezone.now()

        assert before <= test_block.created <= after

    def test_same_user_pair_cannot_have_duplicate_block(
        self,
        test_users,
    ):
        test_user, test_user_2 = test_users

        Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        with pytest.raises(IntegrityError):
            Block.objects.create(
                from_user=test_user,
                to_user=test_user_2,
            )

    def test_reverse_block_is_allowed(self, test_users):
        test_user, test_user_2 = test_users

        Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )

        test_reverse_block = Block.objects.create(
            from_user=test_user_2,
            to_user=test_user,
        )

        assert test_reverse_block.pk is not None
        assert Block.objects.count() == 2

    def test_self_block_is_allowed_by_current_model(
        self,
        django_user_model,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

        test_block = Block.objects.create(
            from_user=test_user,
            to_user=test_user,
        )

        assert test_block.from_user == test_user
        assert test_block.to_user == test_user

    def test_from_user_reverse_relation(self, test_block, test_users):
        test_user, _ = test_users

        assert test_block in test_user.block_from.all()

    def test_to_user_reverse_relation(self, test_block, test_users):
        _, test_user_2 = test_users

        assert test_block in test_user_2.block_to.all()

    def test_block_is_deleted_with_from_user(self, test_users):
        test_user, test_user_2 = test_users

        test_block = Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )
        test_block_id = test_block.pk

        test_user.delete()

        assert not Block.objects.filter(pk=test_block_id).exists()

    def test_block_is_deleted_with_to_user(self, test_users):
        test_user, test_user_2 = test_users

        test_block = Block.objects.create(
            from_user=test_user,
            to_user=test_user_2,
        )
        test_block_id = test_block.pk

        test_user_2.delete()

        assert not Block.objects.filter(pk=test_block_id).exists()


class TestNotification:
    @pytest.fixture
    def test_user(self, django_user_model):
        return django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )

    @pytest.fixture
    def test_profile(self, test_user):
        return Profile.objects.create(user=test_user)

    @pytest.fixture
    def test_notification(self, test_user, test_profile):
        return Notification.objects.create(
            user=test_user,
            content_object=test_profile,
            verb="test_verb",
        )

    def test_create_notification(
        self,
        test_user,
        test_profile,
    ):
        test_notification = Notification.objects.create(
            user=test_user,
            content_object=test_profile,
            verb="test_verb",
        )

        assert test_notification.pk is not None
        assert test_notification.user == test_user
        assert test_notification.content_object == test_profile
        assert test_notification.verb == "test_verb"

    def test_seen_defaults_to_false(self, test_notification):
        assert test_notification.seen is False

    def test_seen_can_be_enabled(self, test_user, test_profile):
        test_notification = Notification.objects.create(
            user=test_user,
            content_object=test_profile,
            verb="test_verb",
            seen=True,
        )

        assert test_notification.seen is True

    def test_created_is_set_automatically(
        self,
        test_user,
        test_profile,
    ):
        before = timezone.now()

        test_notification = Notification.objects.create(
            user=test_user,
            content_object=test_profile,
            verb="test_verb",
        )

        after = timezone.now()

        assert before <= test_notification.created <= after

    def test_generic_relation_stores_content_type(
        self,
        test_notification,
    ):
        expected_content_type = ContentType.objects.get_for_model(Profile)

        assert test_notification.content_type == expected_content_type

    def test_generic_relation_stores_object_id(
        self,
        test_notification,
        test_profile,
    ):
        assert test_notification.object_id == test_profile.pk

    def test_generic_relation_resolves_target_object(
        self,
        test_notification,
        test_profile,
    ):
        test_notification.refresh_from_db()

        assert test_notification.content_object == test_profile

    def test_generic_relation_supports_different_model_types(
        self,
        test_user,
    ):
        test_user_2 = MyUser.objects.create_user(
            username="test_user_2",
            email="test_user_2@example.com",
            password="test_password",
        )

        test_notification = Notification.objects.create(
            user=test_user,
            content_object=test_user_2,
            verb="test_verb",
        )

        assert test_notification.content_object == test_user_2
        assert test_notification.content_type == ContentType.objects.get_for_model(
            MyUser
        )
        assert test_notification.object_id == test_user_2.pk

    def test_verb_accepts_300_characters(
        self,
        test_user,
        test_profile,
    ):
        test_verb = "a" * 300

        test_notification = Notification.objects.create(
            user=test_user,
            content_object=test_profile,
            verb=test_verb,
        )

        assert test_notification.verb == test_verb

    def test_verb_rejects_more_than_300_characters(
        self,
        test_user,
        test_profile,
    ):
        test_notification = Notification(
            user=test_user,
            content_object=test_profile,
            verb="a" * 301,
        )

        with pytest.raises(ValidationError):
            test_notification.full_clean()

    def test_user_is_required(self, test_profile):
        test_notification = Notification(
            content_object=test_profile,
            verb="test_verb",
        )

        with pytest.raises(ValidationError):
            test_notification.full_clean()

    def test_verb_is_required(self, test_user, test_profile):
        test_notification = Notification(
            user=test_user,
            content_object=test_profile,
        )

        with pytest.raises(ValidationError):
            test_notification.full_clean()

    def test_notification_is_deleted_with_user(
        self,
        django_user_model,
    ):
        test_user = django_user_model.objects.create_user(
            username="test_user",
            email="test_user@example.com",
            password="test_password",
        )
        test_profile = Profile.objects.create(user=test_user)

        test_notification = Notification.objects.create(
            user=test_user,
            content_object=test_profile,
            verb="test_verb",
        )
        test_notification_id = test_notification.pk

        test_user.delete()

        assert not Notification.objects.filter(
            pk=test_notification_id,
        ).exists()

    def test_notification_target_can_be_deleted(
        self,
        test_notification,
        test_profile,
    ):
        test_profile.delete()

        test_notification.refresh_from_db()

        assert test_notification.content_object is None
