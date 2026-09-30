from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


UserModel = get_user_model()


def send_email(
    subject_template_name,
    email_template_name,
    context,
    from_email,
    to_email,
    html_email_template_name=None,
):
    """
    Render and send an email using the supplied templates.
    """
    if isinstance(subject_template_name, str):
        subject = subject_template_name
    else:
        subject = loader.render_to_string(subject_template_name, context)

    subject = "".join(subject.splitlines())

    body = loader.render_to_string(email_template_name, context)

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
        email_message.attach_alternative(html_email, "text/html")

    email_message.send()


class EmailConfirmation:
    subject_template_name = (
        "email/registration/confirmation_email_subject.txt"
    )
    email_template_name = "email/registration/confirmation_email.html"
    html_email_template_name = (
        "email/registration/confirmation_html_email.html"
    )

    token_generator = default_token_generator
    domain_override = None
    from_email = None
    extra_email_context = None

    def __init__(self, email, request):
        self.email = email
        self.request = request

    def get_users(self, email):
        """
        Return users matching the supplied email address who have
        a usable password.
        """
        email_field_name = UserModel.get_email_field_name()

        users = UserModel._default_manager.filter(
            **{f"{email_field_name}__iexact": email}
        )

        return (
            user
            for user in users
            if user.has_usable_password()
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
        send_email(
            subject_template_name=subject_template_name,
            email_template_name=email_template_name,
            context=context,
            from_email=from_email,
            to_email=to_email,
            html_email_template_name=html_email_template_name,
        )

    def save(self):
        """
        Generate and send an email confirmation link for each
        matching user.
        """
        if self.domain_override:
            site_name = self.domain_override
            domain = self.domain_override
        else:
            current_site = get_current_site(self.request)
            site_name = current_site.name
            domain = current_site.domain

        email_field_name = UserModel.get_email_field_name()

        for user in self.get_users(self.email):
            user_email = getattr(user, email_field_name)

            context = {
                "email": user_email,
                "domain": domain,
                "site_name": site_name,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "username": user.get_username(),
                "token": self.token_generator.make_token(user),
                "protocol": (
                    "https"
                    if self.request.is_secure()
                    else "http"
                ),
                **(self.extra_email_context or {}),
            }

            self.send_mail(
                subject_template_name=self.subject_template_name,
                email_template_name=self.email_template_name,
                context=context,
                from_email=self.from_email,
                to_email=user_email,
                html_email_template_name=self.html_email_template_name,
            )