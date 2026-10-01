from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.staticfiles.storage import staticfiles_storage
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import urlsafe_base64_decode
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import (
    CreateView,
    DeleteView,
    TemplateView,
    UpdateView,
)

from .forms import CustomCreationForm, ProfileForm, UserForm
from .models import Profile, SiteManager

User_Model = get_user_model()
INTERNAL_REGISTRATION_SESSION_TOKEN = "_registration_token"


class PasswordContextMixin:
    extra_context = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {"title": self.title, "subtitle": None, **(self.extra_context or {})}
        )
        return context


class UpdateProfile(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User_Model
    template_name = "social/update-profile.html"
    form_class = UserForm
    success_message = "Profile successfully Updated"

    def get_success_url(self):
        return reverse("social:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_form"] = ProfileForm(
            instance=self.get_object().profile,
        )
        return context

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        user_form = self.get_form()
        profile_form = ProfileForm(
            instance=self.object.profile,
            data=request.POST,
            files=request.FILES,
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()

            profile = profile_form.save(commit=False)
            profile.user = self.object
            profile.save()

            return self.form_valid(user_form)

        context = self.get_context_data(form=user_form)
        context["user_form"] = profile_form

        return self.render_to_response(context)


class RegistrationView(CreateView):
    model = get_user_model()
    form_class = CustomCreationForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("account:registration_done")
    title = _("Register")

    email_template_name = "email/registration/registration_email.txt"
    html_email_template_name = "email/registration/registration_email.html"
    subject_template_name = "email/registration/registration_subject.txt"
    from_email = None
    extra_email_context = None
    token_generator = default_token_generator

    def form_valid(self, form):
        options = {
            "use_https": self.request.is_secure(),
            "token_generator": self.token_generator,
            "from_email": self.from_email,
            "email_template_name": self.email_template_name,
            "subject_template_name": self.subject_template_name,
            "request": self.request,
            "html_email_template_name": self.html_email_template_name,
            "extra_email_context": self.extra_email_context,
        }

        self.object = form.save(**options)
        self.request.session["email"] = self.object.email
        messages.success(
            self.request,
            _("Signed up successfully! Please confirm your email."),
        )

        return HttpResponseRedirect(self.get_success_url())


class RegistrationDoneView(PasswordContextMixin, TemplateView):
    template_name = "registration/registration_done.html"
    title = _("Activition Email sent")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get("email")
        return context


class RegistrationConfirmView(TemplateView):
    template_name = "registration/registration_complete.html"
    confirm_registration_url_token = "confirmation-done"
    token_generator = default_token_generator

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        if "uidb64" not in kwargs or "token" not in kwargs:
            raise ImproperlyConfigured(
                "The URL path must contain 'uidb64' and 'token' parameters."
            )

        self.validlink = False
        self.user = self.get_user(kwargs["uidb64"])

        if self.user is not None:
            token = kwargs["token"]

            if token == self.confirm_registration_url_token:
                session_token = self.request.session.get(
                    INTERNAL_REGISTRATION_SESSION_TOKEN
                )
                if self.token_generator.check_token(self.user, session_token):
                    # If the token is valid, display the password reset form.
                    self.validlink = True
                    self.user.is_active = True
                    self.user.save()
                    Profile.objects.get_or_create(user=self.user)
                    return super().dispatch(*args, **kwargs)
            else:
                if self.token_generator.check_token(self.user, token):
                    # Store the token in the session and redirect to the
                    # password reset form at a URL without the token. That
                    # avoids the possibility of leaking the token in the
                    # HTTP Referer header.

                    self.request.session[INTERNAL_REGISTRATION_SESSION_TOKEN] = token
                    redirect_url = self.request.path.replace(
                        token, self.confirm_registration_url_token
                    )
                    return HttpResponseRedirect(redirect_url)

        # Display the "confirmation email unsuccessful" page.
        return self.render_to_response(self.get_context_data())

    def get_user(self, uidb64):
        try:
            # urlsafe_base64_decode() decodes to bytestring
            uid = urlsafe_base64_decode(uidb64).decode()
            pk = User_Model._meta.pk.to_python(uid)
            user = User_Model._default_manager.get(pk=pk)
        except (
            TypeError,
            ValueError,
            OverflowError,
            User_Model.DoesNotExist,
            ValidationError,
        ):
            user = None
        return user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.validlink:
            context["validlink"] = True
            admin = User_Model.objects.filter(is_superuser=True).first()

            context["admin"] = admin
        else:
            context.update(
                {
                    "form": None,
                    "title": "Password reset unsuccessful",
                    "validlink": False,
                }
            )
        return context


class PasswordResetView(auth_views.PasswordResetView):
    template_name = "registration/pass_reset_form.html"
    email_template_name = "email/reset/pass_reset_email.txt"
    html_email_template_name = "email/reset/pass_reset_email.html"
    subject_template_name = "email/reset/pass_reset_subject.txt"
    success_url = reverse_lazy("account:password_reset_done")

    def form_valid(self, form):
        self.extra_email_context = {
            "developer_name": settings.DEVELOPER_NAME,
            "logo_url": self.request.build_absolute_uri(
                staticfiles_storage.url("images/logo_transparent.png")
            ),
        }
        email = form.cleaned_data["email"]
        self.request.session["email"] = email
        return super().form_valid(form)


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "registration/pass_reset_done.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["email"] = self.request.session.get("email")
        return context


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "registration/pass_reset_confirm.html"
    success_url = reverse_lazy("account:password_reset_complete")


class PasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "registration/pass_reset_complete.html"


class Deactivate(LoginRequiredMixin, DeleteView):
    template_name = "registration/delete_account.html"
    model = User_Model
    success_url = reverse_lazy("social:home")


class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "together/search.html"


class NotificationView(LoginRequiredMixin, TemplateView):
    template_name = "together/notification.html"


class ContactMe(TemplateView):
    template_name = "together/contact-me.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["manager"] = SiteManager.objects.first()
        return context


class CustomLoginView(LoginView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admin = User_Model.objects.filter(is_superuser=True).first()
        context["admin"] = admin
        return context
