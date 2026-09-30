from django.urls import include, path

from . import  views
app_name = "account"
urlpatterns = [
    path("edit-profile/", views.UpdateProfile.as_view(), name="update_profile"),
    path("register/", views.RegistrationView.as_view(), name="register"),
    path(
        "register/registration_done/",
        views.RegistrationDoneView.as_view(),
        name="registration_done",
    ),
    path("deactivate/<int:pk>", views.Deactivate.as_view(), name="deactivate"),
    path("", include("django.contrib.auth.urls")),
]

urlpatterns += [
    path(
        "confirm/<uidb64>/<token>/",
        views.RegistrationConfirmView.as_view(),
        name="register_confirm",
    )
]
