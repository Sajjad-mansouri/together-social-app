from django.db.models import Q
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from account.models import Block, Contact
from api.views import RestrictionApiView


class TestRestrictionApiView:
    def setup_method(self):
        self.client = APIClient()

    def create_user(
        self,
        django_user_model,
        username,
        email,
        password="TestPassword123!",
    ):
        return django_user_model.objects.create_user(
            username=username,
            email=email,
            password=password,
        )

    def test_view_configuration(self):
        assert RestrictionApiView.serializer_class.__name__ == ("RestrictionSerializer")
        assert RestrictionApiView.queryset.model is Block

    def test_post_requires_authentication(self, django_user_model):
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.post(
            url,
            {"to_user": target_user.username},
            format="json",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert not Block.objects.exists()

    def test_create_block(self, django_user_model):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.post(
            url,
            {"to_user": target_user.username},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        block = Block.objects.get(
            from_user=user,
            to_user=target_user,
        )

        assert block.from_user == user
        assert block.to_user == target_user

    def test_create_block_removes_contact_in_authenticated_users_direction(
        self,
        django_user_model,
    ):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        Contact.objects.create(
            from_user=user,
            to_user=target_user,
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.post(
            url,
            {"to_user": target_user.username},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert not Contact.objects.filter(
            from_user=user,
            to_user=target_user,
        ).exists()

    def test_create_block_removes_contact_in_target_users_direction(
        self,
        django_user_model,
    ):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        Contact.objects.create(
            from_user=target_user,
            to_user=user,
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.post(
            url,
            {"to_user": target_user.username},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert not Contact.objects.filter(
            from_user=target_user,
            to_user=user,
        ).exists()

    def test_create_block_removes_contacts_in_both_directions(
        self,
        django_user_model,
    ):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        Contact.objects.create(
            from_user=user,
            to_user=target_user,
        )
        Contact.objects.create(
            from_user=target_user,
            to_user=user,
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.post(
            url,
            {"to_user": target_user.username},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

        assert not Contact.objects.filter(
            Q(from_user=user, to_user=target_user)
            | Q(from_user=target_user, to_user=user)
        ).exists()

    def test_create_block_does_not_remove_unrelated_contacts(
        self,
        django_user_model,
    ):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )
        unrelated_user = self.create_user(
            django_user_model,
            "unrelated",
            "unrelated@example.com",
        )

        unrelated_contact = Contact.objects.create(
            from_user=user,
            to_user=unrelated_user,
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.post(
            url,
            {"to_user": target_user.username},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Contact.objects.filter(
            pk=unrelated_contact.pk,
        ).exists()

    def test_invalid_data_returns_400(self, django_user_model):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": user.username},
        )

        response = self.client.post(
            url,
            {},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not Block.objects.exists()

    def test_create_block_with_nonexistent_target_returns_404(
        self,
        django_user_model,
    ):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": "does-not-exist"},
        )

        response = self.client.post(
            url,
            {"to_user": "does-not-exist"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not Block.objects.exists()

    def test_delete_block(self, django_user_model):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        block = Block.objects.create(
            from_user=user,
            to_user=target_user,
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Block.objects.filter(pk=block.pk).exists()

    def test_delete_requires_authentication(self, django_user_model):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        block = Block.objects.create(
            from_user=user,
            to_user=target_user,
        )

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert Block.objects.filter(pk=block.pk).exists()

    def test_delete_does_not_delete_another_users_block(
        self,
        django_user_model,
    ):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        other_user = self.create_user(
            django_user_model,
            "otheruser",
            "otheruser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        block = Block.objects.create(
            from_user=other_user,
            to_user=target_user,
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Block.objects.filter(pk=block.pk).exists()

    def test_delete_nonexistent_block_returns_404(
        self,
        django_user_model,
    ):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )
        target_user = self.create_user(
            django_user_model,
            "targetuser",
            "targetuser@example.com",
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": target_user.username},
        )

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_nonexistent_target_user_returns_404(
        self,
        django_user_model,
    ):
        user = self.create_user(
            django_user_model,
            "testuser",
            "testuser@example.com",
        )

        self.client.force_authenticate(user=user)

        url = reverse(
            "api:restriction",
            kwargs={"to_user": "does-not-exist"},
        )

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
