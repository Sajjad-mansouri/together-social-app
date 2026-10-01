import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient

from account.models import Contact, Profile
from api.permissions import RelationDeletePermission
from api.serializers import ContactSerializer
from api.views import ContactApiView, ContactDetailApiView

UserModel = get_user_model()


@pytest.mark.django_db
class TestContactApiView:
    @pytest.fixture
    def api_client(self):
        return APIClient()

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
    def contact(self, test_user, test_user_2):
        return Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )

    @pytest.fixture
    def contact_url(self):
        return reverse("api:contact")

    def contact_detail_url(self, contact):
        return reverse(
            "api:contact-detail",
            kwargs={"pk": contact.pk},
        )

    def conection_url(self, username):
        return reverse(
            "api:conection",
            kwargs={"to_user": username},
        )

    # ------------------------------------------------------------------
    # View configuration
    # ------------------------------------------------------------------

    def test_serializer_class(self):
        assert ContactApiView.serializer_class is ContactSerializer

    def test_queryset(self):
        assert ContactApiView.queryset.model is Contact

    def test_detail_serializer_class(self):
        assert ContactDetailApiView.serializer_class is ContactSerializer

    def test_detail_queryset(self):
        assert ContactDetailApiView.queryset.model is Contact

    def test_detail_permission_classes(self):
        assert ContactDetailApiView.permission_classes == [
            IsAuthenticated,
            RelationDeletePermission,
        ]

    def test_permission_classes(self):
        assert ContactApiView.permission_classes == [IsAuthenticated]

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def test_get_returns_contacts(
        self,
        api_client,
        contact_url,
        test_user,
        test_user_2,
    ):
        contact = Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user,
            access=True,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(contact_url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["id"] == contact.id

    def test_get_returns_empty_list_when_no_contacts(
        self,
        api_client,
        contact_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(contact_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    def test_get_returns_all_contacts(
        self,
        api_client,
        contact_url,
        test_user,
        test_user_2,
        test_user_3,
    ):
        contact_1 = Contact.objects.create(
            from_user=test_user,
            to_user=test_user_2,
            access=True,
        )
        contact_2 = Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user_3,
            access=False,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.get(contact_url)

        assert response.status_code == status.HTTP_200_OK

        contact_ids = {item["id"] for item in response.data}

        assert contact_1.id in contact_ids
        assert contact_2.id in contact_ids

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def test_create_contact(
        self,
        api_client,
        contact_url,
        test_user,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            contact_url,
            {
                "from_user": test_user_2.id,
                "to_user": test_user_2.id,
                "access": True,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        contact = Contact.objects.get(
            from_user=test_user,
            to_user=test_user_2,
        )

        assert contact.access is True
        assert response.data["id"] == contact.id
        assert response.data["from_user"] == test_user.id
        assert response.data["to_user"] == test_user_2.id

    def test_create_contact_ignores_submitted_from_user(
        self,
        api_client,
        contact_url,
        test_user,
        test_user_2,
        test_user_3,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            contact_url,
            {
                "from_user": test_user_3.id,
                "to_user": test_user_2.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        contact = Contact.objects.get(
            to_user=test_user_2,
        )

        assert contact.from_user == test_user
        assert contact.from_user != test_user_3

    def test_create_contact_sets_access_for_public_profile(
        self,
        api_client,
        contact_url,
        test_user,
        test_user_2,
    ):
        test_user_2.profile.private = False
        test_user_2.profile.save()

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            contact_url,
            {
                "to_user": test_user_2.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        contact = Contact.objects.get(
            from_user=test_user,
            to_user=test_user_2,
        )

        assert contact.access is True

    def test_create_contact_sets_access_for_private_profile(
        self,
        api_client,
        contact_url,
        test_user,
        test_user_2,
    ):
        test_user_2.profile.private = True
        test_user_2.profile.save()

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            contact_url,
            {
                "to_user": test_user_2.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        contact = Contact.objects.get(
            from_user=test_user,
            to_user=test_user_2,
        )

        assert contact.access is False

    def test_create_contact_overrides_submitted_access(
        self,
        api_client,
        contact_url,
        test_user,
        test_user_2,
    ):
        test_user_2.profile.private = True
        test_user_2.profile.save()

        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            contact_url,
            {
                "to_user": test_user_2.id,
                "access": True,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        contact = Contact.objects.get(
            from_user=test_user,
            to_user=test_user_2,
        )

        assert contact.access is False

    def test_create_contact_requires_to_user(
        self,
        api_client,
        contact_url,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.post(
            contact_url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "to_user" in response.data

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def test_retrieve_contact(
        self,
        api_client,
        contact,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            self.contact_detail_url(contact),
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == contact.id
        assert response.data["from_user"] == contact.from_user.id
        assert response.data["to_user"] == contact.to_user.id

    def test_retrieve_nonexistent_contact_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.get(
            reverse(
                "api:contact-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def test_update_contact(
        self,
        api_client,
        contact,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.patch(
            self.contact_detail_url(contact),
            {
                "access": False,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        contact.refresh_from_db()

        assert contact.access is False
        assert response.data["access"] is False

    def test_update_contact_preserves_unspecified_fields(
        self,
        api_client,
        contact,
        test_user,
    ):
        original_from_user = contact.from_user
        original_to_user = contact.to_user

        api_client.force_authenticate(user=test_user)

        response = api_client.patch(
            self.contact_detail_url(contact),
            {
                "access": False,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK

        contact.refresh_from_db()

        assert contact.from_user == original_from_user
        assert contact.to_user == original_to_user
        assert contact.access is False

    def test_update_nonexistent_contact_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.patch(
            reverse(
                "api:contact-detail",
                kwargs={"pk": 999999},
            ),
            {
                "access": False,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Delete by primary key
    # ------------------------------------------------------------------

    def test_delete_contact_by_pk(
        self,
        api_client,
        contact,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            self.contact_detail_url(contact),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Contact.objects.filter(pk=contact.pk).exists()

    def test_delete_contact_by_pk_does_not_delete_other_contact(
        self,
        api_client,
        contact,
        test_user_2,
        test_user_3,
    ):
        other_contact = Contact.objects.create(
            from_user=test_user_2,
            to_user=test_user_3,
            access=True,
        )

        api_client.force_authenticate(user=test_user_2)

        response = api_client.delete(
            self.contact_detail_url(other_contact),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Contact.objects.filter(pk=other_contact.pk).exists()
        assert Contact.objects.filter(pk=contact.pk).exists()

    def test_delete_nonexistent_contact_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            reverse(
                "api:contact-detail",
                kwargs={"pk": 999999},
            ),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Delete through /conection/<to_user>/
    # ------------------------------------------------------------------

    def test_delete_connection_by_username(
        self,
        api_client,
        contact,
        test_user,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            self.conection_url(test_user_2.username),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not Contact.objects.filter(
            from_user=test_user,
            to_user=test_user_2,
        ).exists()

    def test_delete_connection_by_username_only_deletes_current_users_relation(
        self,
        api_client,
        contact,
        test_user,
        test_user_2,
        test_user_3,
    ):
        other_contact = Contact.objects.create(
            from_user=test_user_3,
            to_user=test_user_2,
            access=True,
        )

        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            self.conection_url(test_user_2.username),
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        assert not Contact.objects.filter(
            pk=contact.pk,
        ).exists()

        assert Contact.objects.filter(
            pk=other_contact.pk,
        ).exists()

    def test_delete_connection_with_unknown_username_returns_404(
        self,
        api_client,
        test_user,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            self.conection_url("does-not-exist"),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_connection_when_relation_does_not_exist_returns_404(
        self,
        api_client,
        test_user,
        test_user_2,
    ):
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(
            self.conection_url(test_user_2.username),
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def test_list_requires_authentication(
        self,
        api_client,
        contact_url,
    ):
        response = api_client.get(contact_url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_requires_authentication(
        self,
        api_client,
        contact_url,
        test_user_2,
    ):
        response = api_client.post(
            contact_url,
            {
                "to_user": test_user_2.id,
            },
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_connection_requires_authentication(
        self,
        api_client,
        contact,
        test_user_2,
    ):
        response = api_client.delete(
            self.conection_url(test_user_2.username),
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
