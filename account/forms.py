from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.staticfiles.storage import staticfiles_storage

UserModel = get_user_model()

from .models import Profile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_image", "birth_day"]


class CustomCreationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta(UserCreationForm.Meta):
        model = UserModel
        fields = (
            "username",
            "email",
        )

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        """
        Render and send the registration confirmation email.
        """
        subject = loader.render_to_string(
            subject_template_name,
            context,
        )
        subject = "".join(subject.splitlines())

        body = loader.render_to_string(
            email_template_name,
            context,
        )

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=body,
            from_email=from_email,
            to=[to_email],
        )

        if html_email_template_name:
            html_email = loader.render_to_string(
                html_email_template_name,
                context,
            )
            email_message.attach_alternative(
                html_email,
                "text/html",
            )

        email_message.send(fail_silently=False)

    def _send_confirmation_email(
        self,
        *,
        domain_override=None,
        subject_template_name="registration/registration_subject.txt",
        email_template_name="registration/registration_email.txt",
        use_https=False,
        token_generator=default_token_generator,
        from_email=None,
        request=None,
        html_email_template_name="registration/registration_email.html",
        extra_email_context=None,
    ):
        """
        Generate and send a one-use email confirmation link.
        """
        email = self.cleaned_data["email"]

        if domain_override:
            site_name = domain_override
            domain = domain_override
        else:
            current_site = get_current_site(request)
            site_name = current_site.name
            domain = current_site.domain

        email_field_name = UserModel.get_email_field_name()

        users = UserModel._default_manager.filter(
            **{f"{email_field_name}__iexact": email}
        )

        for user in users:
            user_email = getattr(user, email_field_name)

            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(
                    force_bytes(user.pk),
                ),
                "user": user,
                "username": user.get_username(),
                "token": token_generator.make_token(user),
                "protocol": "https" if use_https else "http",
                'logo_url': request.build_absolute_uri(staticfiles_storage.url('images/logo_transparent.png')),
                **(extra_email_context or {}),
            }

            self.send_mail(
                subject_template_name=subject_template_name,
                email_template_name=email_template_name,
                context=context,
                from_email=from_email,
                to_email=user_email,
                html_email_template_name=html_email_template_name,
            )

    def save(self, commit=True, **options):
        """
        Create an inactive user and optionally send the confirmation email.
        """
        user = super().save(commit=False)
        user.is_active = False

        if commit:
            user.save()

            self._send_confirmation_email(
                **options,
            )

        return user



class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "username", "email"]
