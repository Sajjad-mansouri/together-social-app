from django.urls import path,include

from . import views
from . import emailconf

urlpatterns=[
	path('profile',views.Profile.as_view(),name='profile'),
	path('register/',views.Register.as_view(),name='register'),
	path('',include('django.contrib.auth.urls')),
]

urlpatterns+=[
	path(
        "confirm/<uidb64>/<token>/",
        emailconf.EmailConfirmView.as_view(),
        name="email_confirm",)
]