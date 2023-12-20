from django.urls import path,include

from . import views
from . import emailconf

urlpatterns=[
	path('profile',views.UpdateProfile.as_view(),name='update-profile'),
	path('register/',views.Register.as_view(),name='register'),
	path('',include('django.contrib.auth.urls')),
]

urlpatterns+=[
	path(
        "confirm/<uidb64>/<token>/",
        emailconf.EmailConfirmView.as_view(),
        name="email_confirm",)
]